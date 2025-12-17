"""Chair position analytics for multi-player table sessions.

This module analyzes outcomes by seat position to answer the research question:
"Does the seat you're in affect your winning percentage?"

Key types:
- SeatStatistics: Per-seat win rates, confidence intervals, and profit metrics
- ChairPositionAnalysis: Complete analysis with chi-square independence test

Main function:
- analyze_chair_positions(): Analyze outcomes by seat position
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from scipy import stats as scipy_stats

from let_it_ride.analytics.validation import calculate_wilson_confidence_interval
from let_it_ride.simulation.session import SessionOutcome

if TYPE_CHECKING:
    from let_it_ride.simulation.session import SessionResult
    from let_it_ride.simulation.table_session import TableSessionResult


@dataclass(frozen=True, slots=True)
class SeatStatistics:
    """Statistics for a single seat position.

    Attributes:
        seat_number: The seat position (1-based).
        total_rounds: Total rounds played at this seat.
        wins: Number of winning sessions.
        losses: Number of losing sessions.
        pushes: Number of push sessions.
        win_rate: Proportion of winning sessions (wins / total_rounds).
        win_rate_ci_lower: Lower bound of CI for win rate (confidence level configurable).
        win_rate_ci_upper: Upper bound of CI for win rate (confidence level configurable).
        expected_value: Average profit per round.
        total_profit: Total profit across all rounds.
    """

    seat_number: int
    total_rounds: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    win_rate_ci_lower: float
    win_rate_ci_upper: float
    expected_value: float
    total_profit: float


@dataclass(frozen=True, slots=True)
class ChairPositionAnalysis:
    """Complete analysis of outcomes by chair position.

    Attributes:
        seat_statistics: Statistics for each seat position.
        chi_square_statistic: Chi-square test statistic for seat independence.
        chi_square_p_value: P-value from chi-square test.
        is_position_independent: True if p > significance_level (cannot reject
            null hypothesis that seat position does not affect outcomes).
    """

    seat_statistics: tuple[SeatStatistics, ...]
    chi_square_statistic: float
    chi_square_p_value: float
    is_position_independent: bool


class _SeatAggregation:
    """Mutable accumulator for per-seat data during aggregation."""

    __slots__ = ("wins", "losses", "pushes", "total_profit")

    def __init__(self) -> None:
        self.wins: int = 0
        self.losses: int = 0
        self.pushes: int = 0
        self.total_profit: float = 0.0

    @property
    def total_rounds(self) -> int:
        """Total rounds (sessions) played at this seat."""
        return self.wins + self.losses + self.pushes


def _aggregate_seat_data(
    results: list[TableSessionResult],
) -> dict[int, _SeatAggregation]:
    """Aggregate session outcomes by seat number.

    Args:
        results: List of table session results.

    Returns:
        Dictionary mapping seat number to aggregated data.
    """
    aggregations: dict[int, _SeatAggregation] = {}

    for table_result in results:
        for seat_result in table_result.seat_results:
            seat_num = seat_result.seat_number
            agg = aggregations.get(seat_num)
            if agg is None:
                agg = _SeatAggregation()
                aggregations[seat_num] = agg

            outcome = seat_result.session_result.outcome

            if outcome == SessionOutcome.WIN:
                agg.wins += 1
            elif outcome == SessionOutcome.LOSS:
                agg.losses += 1
            elif outcome == SessionOutcome.PUSH:
                agg.pushes += 1

            agg.total_profit += seat_result.session_result.session_profit

    return aggregations


def _calculate_seat_statistics(
    seat_number: int,
    agg: _SeatAggregation,
    confidence_level: float,
) -> SeatStatistics:
    """Calculate statistics for a single seat.

    Args:
        seat_number: The seat position (1-based).
        agg: Aggregated data for this seat.
        confidence_level: Confidence level for Wilson CI (e.g., 0.95).

    Returns:
        SeatStatistics with win rate, CI, and profit metrics.
    """
    total = agg.total_rounds

    # Calculate win rate
    win_rate = agg.wins / total if total > 0 else 0.0

    # Calculate Wilson confidence interval for win rate
    if total > 0:
        ci_lower, ci_upper = calculate_wilson_confidence_interval(
            successes=agg.wins,
            total=total,
            confidence_level=confidence_level,
        )
    else:
        ci_lower, ci_upper = 0.0, 0.0

    # Calculate expected value (average profit per round)
    expected_value = agg.total_profit / total if total > 0 else 0.0

    return SeatStatistics(
        seat_number=seat_number,
        total_rounds=total,
        wins=agg.wins,
        losses=agg.losses,
        pushes=agg.pushes,
        win_rate=win_rate,
        win_rate_ci_lower=ci_lower,
        win_rate_ci_upper=ci_upper,
        expected_value=expected_value,
        total_profit=agg.total_profit,
    )


def _test_seat_independence(
    seat_stats: list[SeatStatistics],
    significance_level: float,
) -> tuple[float, float, bool]:
    """Run chi-square test for seat position independence.

    Tests the null hypothesis that seat position does not affect outcomes.
    Under the null, wins should be uniformly distributed across seats.

    Args:
        seat_stats: Statistics for each seat.
        significance_level: P-value threshold (typically 0.05).

    Returns:
        Tuple of (chi_square_statistic, p_value, is_position_independent).
    """
    if len(seat_stats) < 2:
        # Cannot test independence with fewer than 2 seats
        return 0.0, 1.0, True

    # Get observed win counts
    observed_wins = [s.wins for s in seat_stats]
    total_wins = sum(observed_wins)

    if total_wins == 0:
        # No wins to analyze - cannot reject null
        return 0.0, 1.0, True

    # Expected wins under null hypothesis (uniform distribution)
    num_seats = len(seat_stats)
    expected_wins_per_seat = total_wins / num_seats
    expected = [expected_wins_per_seat] * num_seats

    # Perform chi-square test
    statistic, p_value = scipy_stats.chisquare(observed_wins, f_exp=expected)

    # Determine if we can reject the null hypothesis
    is_independent = bool(p_value > significance_level)

    return float(statistic), float(p_value), is_independent


def analyze_chair_positions(
    results: list[TableSessionResult],
    confidence_level: float = 0.95,
    significance_level: float = 0.05,
) -> ChairPositionAnalysis:
    """Analyze outcomes by seat position to test if position affects winning.

    This function aggregates session results by seat number, calculates
    per-seat statistics (win rate, confidence intervals, profit), and
    runs a chi-square test to determine if seat position is independent
    of outcomes.

    Args:
        results: List of TableSessionResult from multi-player simulations.
        confidence_level: Confidence level for Wilson CI (default 0.95).
        significance_level: P-value threshold for chi-square test (default 0.05).

    Returns:
        ChairPositionAnalysis with per-seat statistics and independence test.

    Raises:
        ValueError: If results is empty or has no seat data.
    """
    if not results:
        raise ValueError("Cannot analyze empty results list")

    # Aggregate data by seat
    aggregations = _aggregate_seat_data(results)

    if not aggregations:
        raise ValueError("No seat data found in results")

    # Calculate statistics for each seat
    seat_stats: list[SeatStatistics] = []
    for seat_num in sorted(aggregations.keys()):
        stats_for_seat = _calculate_seat_statistics(
            seat_number=seat_num,
            agg=aggregations[seat_num],
            confidence_level=confidence_level,
        )
        seat_stats.append(stats_for_seat)

    # Test for seat independence
    chi_sq, p_val, is_independent = _test_seat_independence(
        seat_stats, significance_level
    )

    return ChairPositionAnalysis(
        seat_statistics=tuple(seat_stats),
        chi_square_statistic=chi_sq,
        chi_square_p_value=p_val,
        is_position_independent=is_independent,
    )


def _aggregate_session_results_by_seat(
    results: list[SessionResult],
) -> dict[int, _SeatAggregation]:
    """Aggregate session outcomes by seat number from flattened results.

    Args:
        results: List of SessionResult with seat_number populated.

    Returns:
        Dictionary mapping seat number to aggregated data.
    """
    aggregations: dict[int, _SeatAggregation] = {}

    for result in results:
        if result.seat_number is None:
            continue

        seat_num = result.seat_number
        agg = aggregations.get(seat_num)
        if agg is None:
            agg = _SeatAggregation()
            aggregations[seat_num] = agg

        if result.outcome == SessionOutcome.WIN:
            agg.wins += 1
        elif result.outcome == SessionOutcome.LOSS:
            agg.losses += 1
        elif result.outcome == SessionOutcome.PUSH:
            agg.pushes += 1

        agg.total_profit += result.session_profit

    return aggregations


def analyze_session_results_by_seat(
    results: list[SessionResult],
    confidence_level: float = 0.95,
    significance_level: float = 0.05,
) -> ChairPositionAnalysis:
    """Analyze outcomes by seat position from flattened SessionResult list.

    This is an alternative to analyze_chair_positions() that works with
    flattened SessionResult objects (as returned by SimulationResults)
    instead of TableSessionResult objects.

    Args:
        results: List of SessionResult with seat_number populated.
        confidence_level: Confidence level for Wilson CI (default 0.95).
        significance_level: P-value threshold for chi-square test (default 0.05).

    Returns:
        ChairPositionAnalysis with per-seat statistics and independence test.

    Raises:
        ValueError: If results is empty or has no seat data.
    """
    if not results:
        raise ValueError("Cannot analyze empty results list")

    # Aggregate data by seat
    aggregations = _aggregate_session_results_by_seat(results)

    if not aggregations:
        raise ValueError("No seat data found in results")

    # Calculate statistics for each seat
    seat_stats: list[SeatStatistics] = []
    for seat_num in sorted(aggregations.keys()):
        stats_for_seat = _calculate_seat_statistics(
            seat_number=seat_num,
            agg=aggregations[seat_num],
            confidence_level=confidence_level,
        )
        seat_stats.append(stats_for_seat)

    # Test for seat independence
    chi_sq, p_val, is_independent = _test_seat_independence(
        seat_stats, significance_level
    )

    return ChairPositionAnalysis(
        seat_statistics=tuple(seat_stats),
        chi_square_statistic=chi_sq,
        chi_square_p_value=p_val,
        is_position_independent=is_independent,
    )
