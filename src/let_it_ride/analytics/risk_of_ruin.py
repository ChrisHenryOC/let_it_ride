"""Risk of Ruin analysis for Let It Ride sessions.

This module provides risk of ruin calculation capabilities:
- Monte Carlo risk of ruin estimation with confidence intervals
- Analytical gambler's ruin formula for validation
- Probability of losing X% of bankroll at various bankroll levels
- Risk curves for different bankroll multiples of base bet
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from let_it_ride.analytics.statistics import ConfidenceInterval
from let_it_ride.analytics.validation import calculate_wilson_confidence_interval

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

    from let_it_ride.simulation.session import SessionResult

# Module-level constants
DEFAULT_MAX_SESSIONS_PER_SIM: int = 10_000
DEFAULT_SIMULATIONS_PER_LEVEL: int = 10_000
DEFAULT_BANKROLL_UNITS: tuple[int, ...] = (20, 40, 60, 80, 100)
MAX_SIMULATIONS_PER_LEVEL: int = 1_000_000
MAX_BANKROLL_LEVELS: int = 100


@dataclass(frozen=True, slots=True)
class RiskOfRuinResult:
    """Risk of ruin analysis for a specific bankroll level.

    Attributes:
        bankroll_units: Bankroll as multiple of base bet.
        ruin_probability: Probability of losing entire bankroll.
        confidence_interval: Confidence interval for ruin probability.
        half_bankroll_risk: Probability of bankroll dropping to 50% of starting value.
        quarter_bankroll_risk: Probability of bankroll dropping to 75% of starting value
            (i.e., 25% cumulative loss).
        sessions_simulated: Number of Monte Carlo simulations run.
    """

    bankroll_units: int
    ruin_probability: float
    confidence_interval: ConfidenceInterval
    half_bankroll_risk: float
    quarter_bankroll_risk: float
    sessions_simulated: int


@dataclass(frozen=True, slots=True)
class RiskOfRuinReport:
    """Complete risk of ruin report across multiple bankroll levels.

    Attributes:
        base_bet: Base bet amount used for calculations.
        starting_bankroll: Original starting bankroll from sessions.
        results: Risk of ruin results for each bankroll level.
        mean_session_profit: Average profit per session.
        session_profit_std: Standard deviation of session profits.
        analytical_estimates: Optional analytical ruin estimates for comparison.
    """

    base_bet: float
    starting_bankroll: float
    results: tuple[RiskOfRuinResult, ...]
    mean_session_profit: float
    session_profit_std: float
    analytical_estimates: tuple[float, ...] | None


def _validate_bankroll_units(bankroll_units: Sequence[int]) -> None:
    """Validate bankroll units parameter.

    Args:
        bankroll_units: Sequence of bankroll levels to validate.

    Raises:
        ValueError: If bankroll_units is empty, too long, or contains non-positive values.
    """
    if not bankroll_units:
        raise ValueError("bankroll_units must not be empty")
    if len(bankroll_units) > MAX_BANKROLL_LEVELS:
        raise ValueError(
            f"bankroll_units exceeds maximum of {MAX_BANKROLL_LEVELS} levels"
        )
    if any(units <= 0 for units in bankroll_units):
        raise ValueError("All bankroll units must be positive integers")


def _validate_session_results(
    session_results: Sequence[SessionResult],
) -> None:
    """Validate session results for risk of ruin calculation.

    Args:
        session_results: Session results to validate.

    Raises:
        ValueError: If session_results is empty or has insufficient data.
    """
    if not session_results:
        raise ValueError("session_results must not be empty")
    if len(session_results) < 10:
        raise ValueError(
            "At least 10 session results required for reliable risk estimation"
        )


def _validate_confidence_level(confidence_level: float) -> None:
    """Validate confidence level parameter.

    Args:
        confidence_level: Confidence level to validate.

    Raises:
        ValueError: If confidence_level is not between 0 and 1 (exclusive).
    """
    if not 0 < confidence_level < 1:
        raise ValueError(
            f"confidence_level must be between 0 and 1 (exclusive), got {confidence_level}"
        )


def _calculate_analytical_ruin_probability(
    mean_profit: float,
    std_profit: float,
    bankroll: float,
) -> float:
    """Calculate analytical ruin probability using normal approximation.

    Uses the gambler's ruin formula with normal distribution approximation.
    For a random walk with drift:
    P(ruin) ≈ exp(-2 * μ * B / σ²) when μ > 0
    P(ruin) = 1 when μ <= 0

    This approximation is valid when the session outcomes follow a roughly
    normal distribution and the bankroll is large relative to bet size.

    Args:
        mean_profit: Mean profit per session.
        std_profit: Standard deviation of session profits.
        bankroll: Starting bankroll.

    Returns:
        Analytical ruin probability as a float between 0 and 1.
    """
    if std_profit == 0:
        # No variance means deterministic outcome
        return 0.0 if mean_profit > 0 else 1.0

    if mean_profit <= 0:
        # Negative or zero expected value means eventual ruin is certain
        return 1.0

    # Gambler's ruin with normal approximation
    # P(ruin) = exp(-2 * μ * B / σ²)
    exponent = -2 * mean_profit * bankroll / (std_profit**2)

    # Prevent overflow for very negative exponents
    if exponent < -700:
        return 0.0

    return math.exp(exponent)


def _run_monte_carlo_ruin_simulation(
    session_profits: NDArray[np.floating[Any]],
    bankroll: float,
    simulations: int,
    rng: np.random.Generator,
    max_sessions_per_sim: int = DEFAULT_MAX_SESSIONS_PER_SIM,
) -> tuple[int, int, int, int]:
    """Run Monte Carlo simulation to estimate ruin probability.

    Simulates bankroll trajectories by sampling session profits and
    tracks how many hit various loss thresholds. Uses vectorized NumPy
    operations for performance.

    Args:
        session_profits: Array of session profit values to sample from.
        bankroll: Starting bankroll for simulation.
        simulations: Number of Monte Carlo simulations to run.
        rng: NumPy random generator for reproducibility.
        max_sessions_per_sim: Maximum sessions per simulation before stopping.

    Returns:
        Tuple of (ruin_count, half_loss_count, quarter_loss_count, total_sims).
    """
    # Threshold values: 50% remaining (50% loss), 75% remaining (25% loss)
    loss_50pct_threshold = bankroll * 0.5
    loss_25pct_threshold = bankroll * 0.75

    # Vectorized sampling: shape (simulations, max_sessions_per_sim)
    all_samples = rng.choice(
        session_profits, size=(simulations, max_sessions_per_sim), replace=True
    )

    # Compute cumulative bankroll trajectories for all simulations
    trajectories = bankroll + np.cumsum(all_samples, axis=1)

    # Find threshold crossings using vectorized operations
    # For each simulation, check if any point crosses the threshold
    ruin_mask = np.any(trajectories <= 0, axis=1)
    half_loss_mask = np.any(trajectories <= loss_50pct_threshold, axis=1)
    quarter_loss_mask = np.any(trajectories <= loss_25pct_threshold, axis=1)

    ruin_count = int(np.sum(ruin_mask))
    half_loss_count = int(np.sum(half_loss_mask))
    quarter_loss_count = int(np.sum(quarter_loss_mask))

    return ruin_count, half_loss_count, quarter_loss_count, simulations


def _calculate_ruin_for_bankroll_level(
    session_profits: NDArray[np.floating[Any]],
    base_bet: float,
    bankroll_units: int,
    simulations_per_level: int,
    confidence_level: float,
    rng: np.random.Generator,
) -> RiskOfRuinResult:
    """Calculate risk of ruin for a single bankroll level.

    Args:
        session_profits: Array of session profit values.
        base_bet: Base bet amount.
        bankroll_units: Bankroll as multiple of base bet.
        simulations_per_level: Number of Monte Carlo simulations.
        confidence_level: Confidence level for intervals.
        rng: NumPy random generator.

    Returns:
        RiskOfRuinResult for this bankroll level.
    """
    bankroll = base_bet * bankroll_units

    ruin_count, half_count, quarter_count, total_sims = (
        _run_monte_carlo_ruin_simulation(
            session_profits=session_profits,
            bankroll=bankroll,
            simulations=simulations_per_level,
            rng=rng,
        )
    )

    ruin_probability = ruin_count / total_sims
    half_bankroll_risk = half_count / total_sims
    quarter_bankroll_risk = quarter_count / total_sims

    # Calculate confidence interval using Wilson score
    ci_lower, ci_upper = calculate_wilson_confidence_interval(
        successes=ruin_count,
        total=total_sims,
        confidence_level=confidence_level,
    )

    return RiskOfRuinResult(
        bankroll_units=bankroll_units,
        ruin_probability=ruin_probability,
        confidence_interval=ConfidenceInterval(
            lower=ci_lower,
            upper=ci_upper,
            level=confidence_level,
        ),
        half_bankroll_risk=half_bankroll_risk,
        quarter_bankroll_risk=quarter_bankroll_risk,
        sessions_simulated=total_sims,
    )


def _validate_simulations_per_level(simulations_per_level: int) -> None:
    """Validate simulations_per_level parameter.

    Args:
        simulations_per_level: Number of simulations to validate.

    Raises:
        ValueError: If simulations_per_level is not positive or exceeds maximum.
    """
    if simulations_per_level <= 0:
        raise ValueError("simulations_per_level must be a positive integer")
    if simulations_per_level > MAX_SIMULATIONS_PER_LEVEL:
        raise ValueError(
            f"simulations_per_level exceeds maximum of {MAX_SIMULATIONS_PER_LEVEL:,}"
        )


def calculate_risk_of_ruin(
    session_results: Sequence[SessionResult],
    bankroll_units: Sequence[int] | None = None,
    base_bet: float | None = None,
    simulations_per_level: int = DEFAULT_SIMULATIONS_PER_LEVEL,
    confidence_level: float = 0.95,
    random_seed: int | None = None,
    include_analytical: bool = True,
) -> RiskOfRuinReport:
    """Calculate risk of ruin across multiple bankroll levels.

    Performs Monte Carlo simulation to estimate the probability of losing
    the entire bankroll for various bankroll sizes. Also calculates the
    probability of hitting intermediate loss thresholds (25%, 50%).

    Args:
        session_results: List of SessionResult objects from simulation.
        bankroll_units: Bankroll levels as multiples of base bet.
            Defaults to [20, 40, 60, 80, 100] if not specified.
        base_bet: Base bet amount. If not provided, infers from session data
            by calculating total_wagered / (total_hands * 3), since each hand
            involves 3 base bets (bet1, bet2, bet3).
        simulations_per_level: Number of Monte Carlo simulations per level.
            Must be positive and not exceed MAX_SIMULATIONS_PER_LEVEL.
        confidence_level: Confidence level for intervals (default 0.95).
        random_seed: Optional seed for reproducibility.
        include_analytical: Whether to include analytical estimates.

    Returns:
        RiskOfRuinReport with results for each bankroll level.

    Raises:
        ValueError: If inputs are invalid.
    """
    # Validate inputs
    _validate_session_results(session_results)
    _validate_confidence_level(confidence_level)
    _validate_simulations_per_level(simulations_per_level)

    # Set default bankroll units
    if bankroll_units is None:
        bankroll_units = list(DEFAULT_BANKROLL_UNITS)
    _validate_bankroll_units(bankroll_units)

    # Extract session data
    session_profits = np.array([r.session_profit for r in session_results])
    starting_bankroll = session_results[0].starting_bankroll

    # Determine base bet
    if base_bet is None:
        # Estimate base bet from total wagered / hands played
        total_wagered = sum(r.total_wagered for r in session_results)
        total_hands = sum(r.hands_played for r in session_results)
        # Each hand has 3 base bets wagered (bet1, bet2, bet3)
        estimated_base = total_wagered / (total_hands * 3) if total_hands > 0 else 1.0
        base_bet = estimated_base

    if base_bet <= 0:
        raise ValueError("base_bet must be positive")

    # Calculate statistics using NumPy for consistency
    mean_profit = float(np.mean(session_profits))
    std_profit = (
        float(np.std(session_profits, ddof=1)) if len(session_profits) > 1 else 0.0
    )

    # Initialize RNG
    rng = np.random.default_rng(random_seed)

    # Calculate risk for each bankroll level
    results: list[RiskOfRuinResult] = []
    analytical_estimates: list[float] = []

    for units in sorted(bankroll_units):
        result = _calculate_ruin_for_bankroll_level(
            session_profits=session_profits,
            base_bet=base_bet,
            bankroll_units=units,
            simulations_per_level=simulations_per_level,
            confidence_level=confidence_level,
            rng=rng,
        )
        results.append(result)

        # Calculate analytical estimate if requested
        if include_analytical:
            bankroll = base_bet * units
            analytical = _calculate_analytical_ruin_probability(
                mean_profit=mean_profit,
                std_profit=std_profit,
                bankroll=bankroll,
            )
            analytical_estimates.append(analytical)

    return RiskOfRuinReport(
        base_bet=base_bet,
        starting_bankroll=starting_bankroll,
        results=tuple(results),
        mean_session_profit=mean_profit,
        session_profit_std=std_profit,
        analytical_estimates=tuple(analytical_estimates)
        if include_analytical
        else None,
    )


def format_risk_of_ruin_report(report: RiskOfRuinReport) -> str:
    """Format a risk of ruin report as human-readable text.

    Args:
        report: RiskOfRuinReport to format.

    Returns:
        Formatted string representation of the report.
    """
    lines = [
        "Risk of Ruin Analysis",
        "=" * 50,
        f"Base Bet: ${report.base_bet:.2f}",
        f"Starting Bankroll: ${report.starting_bankroll:.2f}",
        f"Mean Session Profit: ${report.mean_session_profit:.2f}",
        f"Session Profit Std Dev: ${report.session_profit_std:.2f}",
        "",
        "Risk by Bankroll Level:",
        "-" * 50,
    ]

    for i, result in enumerate(report.results):
        bankroll = report.base_bet * result.bankroll_units
        lines.append(f"\nBankroll: {result.bankroll_units} units (${bankroll:.2f})")
        ci_level_pct = int(result.confidence_interval.level * 100)
        lines.append(
            f"  Ruin Probability: {result.ruin_probability:.2%} "
            f"({ci_level_pct}% CI: {result.confidence_interval.lower:.2%} - "
            f"{result.confidence_interval.upper:.2%})"
        )
        lines.append(f"  50% Loss Risk: {result.half_bankroll_risk:.2%}")
        lines.append(f"  25% Loss Risk: {result.quarter_bankroll_risk:.2%}")
        lines.append(f"  Simulations: {result.sessions_simulated:,}")

        if report.analytical_estimates is not None:
            analytical = report.analytical_estimates[i]
            if not math.isnan(analytical):
                lines.append(f"  Analytical Estimate: {analytical:.2%}")

    return "\n".join(lines)
