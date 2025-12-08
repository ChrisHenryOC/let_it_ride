"""Simulation results aggregation.

This module provides aggregation of results across multiple sessions:
- AggregateStatistics: Summary statistics across all sessions
- aggregate_results(): Process list of SessionResults into statistics
- merge_aggregates(): Combine two aggregates for parallel execution support
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from statistics import mean, median, stdev

from let_it_ride.simulation.session import SessionOutcome, SessionResult


def _calculate_frequency_percentages(frequencies: dict[str, int]) -> dict[str, float]:
    """Calculate percentage for each frequency entry.

    Args:
        frequencies: Dictionary of hand rank counts.

    Returns:
        Dictionary of hand rank percentages (0.0 to 1.0).
    """
    total = sum(frequencies.values())
    if total == 0:
        return {}
    return {key: count / total for key, count in frequencies.items()}


@dataclass(frozen=True, slots=True)
class AggregateStatistics:
    """Aggregate statistics across multiple sessions.

    Attributes:
        total_sessions: Total number of sessions aggregated.
        winning_sessions: Number of sessions with positive profit.
        losing_sessions: Number of sessions with negative profit.
        push_sessions: Number of sessions with zero profit.
        session_win_rate: Fraction of sessions that were profitable.

        total_hands: Total hands played across all sessions.

        total_wagered: Total amount wagered (main game only).
        total_won: Total amount won (main game only).
        net_result: Net profit/loss across all sessions.
        expected_value_per_hand: Average profit/loss per hand.

        main_wagered: Total main game amount wagered.
        main_won: Total main game amount won.
        main_ev_per_hand: Main game expected value per hand.

        bonus_wagered: Total bonus amount wagered.
        bonus_won: Total bonus amount won.
        bonus_ev_per_hand: Bonus expected value per hand.

        hand_frequencies: Count of each hand rank type.
        hand_frequency_pct: Percentage of each hand rank type.

        session_profit_mean: Mean session profit.
        session_profit_std: Standard deviation of session profits.
        session_profit_median: Median session profit.
        session_profit_min: Minimum session profit.
        session_profit_max: Maximum session profit.

        session_profits: Tuple of individual session profits (for merge support).
            Note: Retained for accurate statistics when merging aggregates.
    """

    # Session metrics
    total_sessions: int
    winning_sessions: int
    losing_sessions: int
    push_sessions: int
    session_win_rate: float

    # Hand metrics
    total_hands: int

    # Financial metrics (combined)
    total_wagered: float
    total_won: float
    net_result: float
    expected_value_per_hand: float

    # Main game breakdown
    main_wagered: float
    main_won: float
    main_ev_per_hand: float

    # Bonus breakdown
    bonus_wagered: float
    bonus_won: float
    bonus_ev_per_hand: float

    # Hand distribution
    hand_frequencies: dict[str, int]
    hand_frequency_pct: dict[str, float]

    # Session outcome distribution
    session_profit_mean: float
    session_profit_std: float
    session_profit_median: float
    session_profit_min: float
    session_profit_max: float

    # Internal: keep session profits for merge support
    session_profits: tuple[float, ...]


def aggregate_results(results: list[SessionResult]) -> AggregateStatistics:
    """Aggregate multiple session results into summary statistics.

    Note: SessionResult does not track main game and bonus payouts separately.
    The main/bonus breakdown assumes bonus is break-even (bonus_won = bonus_wagered),
    with all profit/loss attributed to the main game. For accurate main/bonus
    breakdown, use HandRecord data with aggregate_with_hand_frequencies().

    Args:
        results: List of SessionResult objects to aggregate.

    Returns:
        AggregateStatistics with computed summary metrics.

    Raises:
        ValueError: If results list is empty.
    """
    if not results:
        raise ValueError("Cannot aggregate empty results list")

    # Count session outcomes
    winning_sessions = sum(1 for r in results if r.outcome == SessionOutcome.WIN)
    losing_sessions = sum(1 for r in results if r.outcome == SessionOutcome.LOSS)
    push_sessions = sum(1 for r in results if r.outcome == SessionOutcome.PUSH)
    total_sessions = len(results)

    # Session win rate (total_sessions guaranteed > 0 due to empty check above)
    session_win_rate = winning_sessions / total_sessions

    # Total hands
    total_hands = sum(r.hands_played for r in results)

    # Financial metrics
    main_wagered = sum(r.total_wagered for r in results)
    bonus_wagered = sum(r.total_bonus_wagered for r in results)
    total_wagered = main_wagered + bonus_wagered

    # Net result is sum of session profits
    net_result = sum(r.session_profit for r in results)

    # Total won = net_result + total_wagered (since net = won - wagered)
    total_won = net_result + total_wagered

    # Main/bonus breakdown: without separate payout tracking in SessionResult,
    # we assume bonus is break-even and attribute all profit/loss to main game
    bonus_won = bonus_wagered
    main_won = total_won - bonus_won

    # Expected value per hand
    expected_value_per_hand = net_result / total_hands if total_hands > 0 else 0.0
    main_profit = main_won - main_wagered
    main_ev_per_hand = main_profit / total_hands if total_hands > 0 else 0.0
    bonus_ev_per_hand = 0.0  # Break-even assumption

    # Hand frequencies - not available from SessionResult alone
    # Would need HandRecord data; return empty for now
    hand_frequencies: dict[str, int] = {}
    hand_frequency_pct: dict[str, float] = {}

    # Session profit statistics
    session_profits = tuple(r.session_profit for r in results)
    session_profit_mean = mean(session_profits)
    session_profit_std = stdev(session_profits) if len(session_profits) > 1 else 0.0
    session_profit_median = median(session_profits)
    session_profit_min = min(session_profits)
    session_profit_max = max(session_profits)

    return AggregateStatistics(
        total_sessions=total_sessions,
        winning_sessions=winning_sessions,
        losing_sessions=losing_sessions,
        push_sessions=push_sessions,
        session_win_rate=session_win_rate,
        total_hands=total_hands,
        total_wagered=total_wagered,
        total_won=total_won,
        net_result=net_result,
        expected_value_per_hand=expected_value_per_hand,
        main_wagered=main_wagered,
        main_won=main_won,
        main_ev_per_hand=main_ev_per_hand,
        bonus_wagered=bonus_wagered,
        bonus_won=bonus_won,
        bonus_ev_per_hand=bonus_ev_per_hand,
        hand_frequencies=hand_frequencies,
        hand_frequency_pct=hand_frequency_pct,
        session_profit_mean=session_profit_mean,
        session_profit_std=session_profit_std,
        session_profit_median=session_profit_median,
        session_profit_min=session_profit_min,
        session_profit_max=session_profit_max,
        session_profits=session_profits,
    )


def merge_aggregates(
    agg1: AggregateStatistics, agg2: AggregateStatistics
) -> AggregateStatistics:
    """Merge two aggregate statistics into one.

    This supports incremental aggregation for parallel execution where
    different workers produce separate aggregates that need to be combined.

    Args:
        agg1: First aggregate statistics.
        agg2: Second aggregate statistics.

    Returns:
        Combined AggregateStatistics.
    """
    # Session counts
    total_sessions = agg1.total_sessions + agg2.total_sessions
    winning_sessions = agg1.winning_sessions + agg2.winning_sessions
    losing_sessions = agg1.losing_sessions + agg2.losing_sessions
    push_sessions = agg1.push_sessions + agg2.push_sessions
    session_win_rate = winning_sessions / total_sessions if total_sessions > 0 else 0.0

    # Hand counts
    total_hands = agg1.total_hands + agg2.total_hands

    # Financial metrics
    total_wagered = agg1.total_wagered + agg2.total_wagered
    total_won = agg1.total_won + agg2.total_won
    net_result = agg1.net_result + agg2.net_result
    expected_value_per_hand = net_result / total_hands if total_hands > 0 else 0.0

    # Main game
    main_wagered = agg1.main_wagered + agg2.main_wagered
    main_won = agg1.main_won + agg2.main_won
    main_profit = main_won - main_wagered
    main_ev_per_hand = main_profit / total_hands if total_hands > 0 else 0.0

    # Bonus
    bonus_wagered = agg1.bonus_wagered + agg2.bonus_wagered
    bonus_won = agg1.bonus_won + agg2.bonus_won
    bonus_profit = bonus_won - bonus_wagered
    bonus_ev_per_hand = bonus_profit / total_hands if total_hands > 0 else 0.0

    # Merge hand frequencies using Counter for cleaner semantics
    hand_frequencies = dict(
        Counter(agg1.hand_frequencies) + Counter(agg2.hand_frequencies)
    )
    hand_frequency_pct = _calculate_frequency_percentages(hand_frequencies)

    # Combine session profits for statistics
    combined_profits = agg1.session_profits + agg2.session_profits
    session_profit_mean = mean(combined_profits) if combined_profits else 0.0
    session_profit_std = stdev(combined_profits) if len(combined_profits) > 1 else 0.0
    session_profit_median = median(combined_profits) if combined_profits else 0.0
    session_profit_min = min(combined_profits) if combined_profits else 0.0
    session_profit_max = max(combined_profits) if combined_profits else 0.0

    return AggregateStatistics(
        total_sessions=total_sessions,
        winning_sessions=winning_sessions,
        losing_sessions=losing_sessions,
        push_sessions=push_sessions,
        session_win_rate=session_win_rate,
        total_hands=total_hands,
        total_wagered=total_wagered,
        total_won=total_won,
        net_result=net_result,
        expected_value_per_hand=expected_value_per_hand,
        main_wagered=main_wagered,
        main_won=main_won,
        main_ev_per_hand=main_ev_per_hand,
        bonus_wagered=bonus_wagered,
        bonus_won=bonus_won,
        bonus_ev_per_hand=bonus_ev_per_hand,
        hand_frequencies=hand_frequencies,
        hand_frequency_pct=hand_frequency_pct,
        session_profit_mean=session_profit_mean,
        session_profit_std=session_profit_std,
        session_profit_median=session_profit_median,
        session_profit_min=session_profit_min,
        session_profit_max=session_profit_max,
        session_profits=combined_profits,
    )


def aggregate_with_hand_frequencies(
    results: list[SessionResult],
    hand_frequencies: dict[str, int],
) -> AggregateStatistics:
    """Aggregate session results with provided hand frequency data.

    Use this when you have hand distribution data from HandRecords
    to include in the aggregation.

    Args:
        results: List of SessionResult objects to aggregate.
        hand_frequencies: Pre-computed hand frequency counts.

    Returns:
        AggregateStatistics with hand frequency data included.

    Raises:
        ValueError: If results list is empty.
    """
    base_stats = aggregate_results(results)
    hand_frequency_pct = _calculate_frequency_percentages(hand_frequencies)

    return replace(
        base_stats,
        hand_frequencies=hand_frequencies,
        hand_frequency_pct=hand_frequency_pct,
    )
