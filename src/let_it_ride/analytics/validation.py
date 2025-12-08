"""Statistical validation for simulation results.

This module validates that simulation results match theoretical probabilities:
- Chi-square goodness of fit test for hand frequency distribution
- Expected value convergence testing against theoretical house edge
- Confidence interval calculation for session win rate
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from scipy import stats

if TYPE_CHECKING:
    from let_it_ride.simulation.aggregation import AggregateStatistics


# Theoretical 5-card poker hand probabilities (exact combinatorics)
# Source: Standard 52-card deck, C(52,5) = 2,598,960 possible hands
THEORETICAL_HAND_PROBS: dict[str, float] = {
    "royal_flush": 4 / 2598960,  # 0.00000154
    "straight_flush": 36 / 2598960,  # 0.0000139 (excludes royal)
    "four_of_a_kind": 624 / 2598960,  # 0.000240
    "full_house": 3744 / 2598960,  # 0.00144
    "flush": 5108 / 2598960,  # 0.00197 (excludes straight/royal flush)
    "straight": 10200 / 2598960,  # 0.00392 (excludes straight flush)
    "three_of_a_kind": 54912 / 2598960,  # 0.0211
    "two_pair": 123552 / 2598960,  # 0.0475
    "pair": 1098240 / 2598960,  # 0.423 (all pairs combined)
    "high_card": 1302540 / 2598960,  # 0.501
}

# Theoretical house edge for Let It Ride main game (optimal strategy)
# This is approximately 3.5% based on standard paytables
THEORETICAL_HOUSE_EDGE: float = 0.035

# Warning thresholds for suspicious deviations
WARNING_THRESHOLD_CHI_SQUARE_P: float = 0.001  # Very suspicious if p < 0.001
WARNING_THRESHOLD_EV_DEVIATION: float = 0.20  # 20% deviation from expected
WARNING_THRESHOLD_WIN_RATE_DEVIATION: float = 0.10  # 10% deviation in win rate


@dataclass(frozen=True, slots=True)
class ChiSquareResult:
    """Result of chi-square goodness of fit test.

    Attributes:
        statistic: Chi-square test statistic.
        p_value: P-value from chi-square distribution.
        degrees_of_freedom: Degrees of freedom (categories - 1).
        is_valid: Whether the distribution passes the test (p > significance).
    """

    statistic: float
    p_value: float
    degrees_of_freedom: int
    is_valid: bool


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Complete validation report for simulation results.

    Attributes:
        chi_square_result: Result of chi-square goodness of fit test.
        observed_frequencies: Observed hand frequency percentages.
        expected_frequencies: Expected hand frequency percentages.
        ev_actual: Actual expected value per hand from simulation.
        ev_theoretical: Theoretical expected value (negative of house edge).
        ev_deviation_pct: Percentage deviation of actual from theoretical EV.
        session_win_rate: Observed session win rate.
        session_win_rate_ci: 95% confidence interval for session win rate.
        warnings: List of warning messages for suspicious deviations.
        is_valid: Overall validity (chi-square passes and no severe warnings).
    """

    chi_square_result: ChiSquareResult
    observed_frequencies: dict[str, float]
    expected_frequencies: dict[str, float]
    ev_actual: float
    ev_theoretical: float
    ev_deviation_pct: float
    session_win_rate: float
    session_win_rate_ci: tuple[float, float]
    warnings: list[str]
    is_valid: bool


def _normalize_hand_frequencies(
    hand_frequencies: dict[str, int],
) -> dict[str, int]:
    """Normalize simulator hand types to theoretical categories.

    The simulator distinguishes pair_tens_or_better and pair_below_tens,
    but theoretical probabilities use a single 'pair' category.

    Args:
        hand_frequencies: Raw hand frequency counts from simulation.

    Returns:
        Normalized frequencies with combined pair category.
    """
    normalized = dict(hand_frequencies)

    # Combine pair types into single 'pair' category
    tens_or_better = normalized.pop("pair_tens_or_better", 0)
    below_tens = normalized.pop("pair_below_tens", 0)
    if tens_or_better > 0 or below_tens > 0:
        normalized["pair"] = tens_or_better + below_tens

    return normalized


def calculate_chi_square(
    observed_frequencies: dict[str, int],
    significance_level: float = 0.05,
) -> ChiSquareResult:
    """Perform chi-square goodness of fit test against theoretical distribution.

    Args:
        observed_frequencies: Observed hand frequency counts (normalized).
        significance_level: P-value threshold for validity (default 0.05).

    Returns:
        ChiSquareResult with test statistics and validity.

    Raises:
        ValueError: If no observations provided or all counts are zero.
    """
    if not observed_frequencies:
        raise ValueError("Cannot perform chi-square test with empty frequencies")

    total_observed = sum(observed_frequencies.values())
    if total_observed == 0:
        raise ValueError("Cannot perform chi-square test with zero total observations")

    # Build aligned observed and expected arrays
    # Only include categories that exist in theoretical probabilities
    observed_values: list[float] = []
    expected_values: list[float] = []

    for hand_type, prob in THEORETICAL_HAND_PROBS.items():
        observed_count = observed_frequencies.get(hand_type, 0)
        expected_count = prob * total_observed

        observed_values.append(float(observed_count))
        expected_values.append(expected_count)

    # Perform chi-square test
    # scipy.stats.chisquare returns (statistic, p_value)
    statistic, p_value = stats.chisquare(observed_values, f_exp=expected_values)

    degrees_of_freedom = len(THEORETICAL_HAND_PROBS) - 1
    is_valid = p_value > significance_level

    return ChiSquareResult(
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=degrees_of_freedom,
        is_valid=is_valid,
    )


def calculate_wilson_confidence_interval(
    successes: int,
    total: int,
    confidence_level: float = 0.95,
) -> tuple[float, float]:
    """Calculate Wilson score confidence interval for a proportion.

    The Wilson score interval is preferred over the normal approximation
    for proportions, especially when the proportion is near 0 or 1.

    Args:
        successes: Number of successes (e.g., winning sessions).
        total: Total number of trials (e.g., total sessions).
        confidence_level: Confidence level (default 0.95 for 95% CI).

    Returns:
        Tuple of (lower_bound, upper_bound) for the proportion.

    Raises:
        ValueError: If total is zero or negative, or successes > total.
    """
    if total <= 0:
        raise ValueError("Total must be positive")
    if successes < 0 or successes > total:
        raise ValueError("Successes must be between 0 and total")

    p_hat = successes / total
    z = stats.norm.ppf((1 + confidence_level) / 2)
    z_squared = z * z

    denominator = 1 + z_squared / total
    center = (p_hat + z_squared / (2 * total)) / denominator
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z_squared / (4 * total)) / total)
    margin = margin / denominator

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return (lower, upper)


def validate_simulation(
    stats: AggregateStatistics,
    significance_level: float = 0.05,
    base_bet: float = 1.0,
) -> ValidationReport:
    """Validate simulation results against theoretical expectations.

    Performs comprehensive statistical validation:
    1. Chi-square test for hand frequency distribution
    2. Expected value convergence check
    3. Session win rate confidence interval

    Args:
        stats: Aggregate statistics from simulation.
        significance_level: P-value threshold for chi-square test (default 0.05).
        base_bet: Base bet amount for EV calculation (default 1.0).

    Returns:
        ValidationReport with all test results and warnings.

    Raises:
        ValueError: If stats has insufficient data for validation.
    """
    warnings: list[str] = []

    # Normalize hand frequencies for chi-square test
    normalized_frequencies = _normalize_hand_frequencies(stats.hand_frequencies)

    # Calculate chi-square test
    # Handle case where hand_frequencies might be empty
    if normalized_frequencies and sum(normalized_frequencies.values()) > 0:
        chi_square_result = calculate_chi_square(
            normalized_frequencies, significance_level
        )

        # Add warning for very low p-value
        if chi_square_result.p_value < WARNING_THRESHOLD_CHI_SQUARE_P:
            warnings.append(
                f"Chi-square p-value ({chi_square_result.p_value:.6f}) is very low, "
                f"suggesting non-random distribution"
            )
    else:
        # No hand frequency data available
        chi_square_result = ChiSquareResult(
            statistic=0.0,
            p_value=1.0,
            degrees_of_freedom=0,
            is_valid=True,  # Can't fail what we can't test
        )
        warnings.append("No hand frequency data available for chi-square test")

    # Calculate observed and expected frequency percentages
    total_hands = sum(normalized_frequencies.values()) if normalized_frequencies else 0
    observed_frequencies: dict[str, float] = {}
    expected_frequencies: dict[str, float] = {}

    for hand_type, prob in THEORETICAL_HAND_PROBS.items():
        expected_frequencies[hand_type] = prob
        if total_hands > 0:
            observed_frequencies[hand_type] = (
                normalized_frequencies.get(hand_type, 0) / total_hands
            )
        else:
            observed_frequencies[hand_type] = 0.0

    # EV convergence testing
    # Theoretical EV per unit bet is negative house edge
    ev_theoretical = -THEORETICAL_HOUSE_EDGE * base_bet
    ev_actual = stats.expected_value_per_hand

    # Calculate deviation percentage (avoid division by zero)
    if abs(ev_theoretical) > 1e-10:
        ev_deviation_pct = abs((ev_actual - ev_theoretical) / ev_theoretical)
    else:
        ev_deviation_pct = abs(ev_actual) if abs(ev_actual) > 1e-10 else 0.0

    if ev_deviation_pct > WARNING_THRESHOLD_EV_DEVIATION:
        warnings.append(
            f"EV deviation ({ev_deviation_pct:.1%}) exceeds threshold "
            f"({WARNING_THRESHOLD_EV_DEVIATION:.1%})"
        )

    # Session win rate confidence interval
    session_win_rate = stats.session_win_rate
    session_win_rate_ci = calculate_wilson_confidence_interval(
        successes=stats.winning_sessions,
        total=stats.total_sessions,
    )

    # Check for extreme win rates (very unusual)
    if session_win_rate < 0.1 or session_win_rate > 0.9:
        warnings.append(
            f"Session win rate ({session_win_rate:.1%}) is unusually extreme"
        )

    # Determine overall validity
    # Valid if chi-square passes and no severe warnings
    is_valid = chi_square_result.is_valid and not any(
        "very low" in w or "unusually extreme" in w for w in warnings
    )

    return ValidationReport(
        chi_square_result=chi_square_result,
        observed_frequencies=observed_frequencies,
        expected_frequencies=expected_frequencies,
        ev_actual=ev_actual,
        ev_theoretical=ev_theoretical,
        ev_deviation_pct=ev_deviation_pct,
        session_win_rate=session_win_rate,
        session_win_rate_ci=session_win_rate_ci,
        warnings=warnings,
        is_valid=is_valid,
    )
