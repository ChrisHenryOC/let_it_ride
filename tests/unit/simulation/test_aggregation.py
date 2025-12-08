"""Tests for simulation results aggregation."""

import pytest

from let_it_ride.simulation.aggregation import (
    aggregate_results,
    aggregate_with_hand_frequencies,
    merge_aggregates,
)
from let_it_ride.simulation.session import SessionOutcome, SessionResult, StopReason


def create_session_result(
    outcome: SessionOutcome,
    stop_reason: StopReason = StopReason.MAX_HANDS,
    hands_played: int = 100,
    starting_bankroll: float = 1000.0,
    final_bankroll: float = 1100.0,
    session_profit: float = 100.0,
    total_wagered: float = 3000.0,
    total_bonus_wagered: float = 100.0,
    peak_bankroll: float = 1200.0,
    max_drawdown: float = 50.0,
    max_drawdown_pct: float = 0.05,
) -> SessionResult:
    """Create a SessionResult for testing."""
    return SessionResult(
        outcome=outcome,
        stop_reason=stop_reason,
        hands_played=hands_played,
        starting_bankroll=starting_bankroll,
        final_bankroll=final_bankroll,
        session_profit=session_profit,
        total_wagered=total_wagered,
        total_bonus_wagered=total_bonus_wagered,
        peak_bankroll=peak_bankroll,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
    )


class TestAggregateResults:
    """Tests for aggregate_results function."""

    def test_empty_results_raises_error(self) -> None:
        """Empty results list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot aggregate empty results list"):
            aggregate_results([])

    def test_single_winning_session(self) -> None:
        """Aggregation of a single winning session."""
        results = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=100,
                session_profit=100.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            )
        ]
        stats = aggregate_results(results)

        assert stats.total_sessions == 1
        assert stats.winning_sessions == 1
        assert stats.losing_sessions == 0
        assert stats.push_sessions == 0
        assert stats.session_win_rate == 1.0
        assert stats.total_hands == 100
        assert stats.net_result == 100.0

    def test_single_losing_session(self) -> None:
        """Aggregation of a single losing session."""
        results = [
            create_session_result(
                outcome=SessionOutcome.LOSS,
                hands_played=50,
                session_profit=-200.0,
                final_bankroll=800.0,
                total_wagered=1500.0,
                total_bonus_wagered=50.0,
            )
        ]
        stats = aggregate_results(results)

        assert stats.total_sessions == 1
        assert stats.winning_sessions == 0
        assert stats.losing_sessions == 1
        assert stats.push_sessions == 0
        assert stats.session_win_rate == 0.0
        assert stats.total_hands == 50
        assert stats.net_result == -200.0

    def test_single_push_session(self) -> None:
        """Aggregation of a single push session."""
        results = [
            create_session_result(
                outcome=SessionOutcome.PUSH,
                hands_played=25,
                session_profit=0.0,
                final_bankroll=1000.0,
                total_wagered=750.0,
                total_bonus_wagered=25.0,
            )
        ]
        stats = aggregate_results(results)

        assert stats.total_sessions == 1
        assert stats.winning_sessions == 0
        assert stats.losing_sessions == 0
        assert stats.push_sessions == 1
        assert stats.session_win_rate == 0.0
        assert stats.total_hands == 25
        assert stats.net_result == 0.0

    def test_multiple_sessions_mixed_outcomes(self) -> None:
        """Aggregation of multiple sessions with mixed outcomes."""
        results = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=100,
                session_profit=100.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                hands_played=100,
                session_profit=-150.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=100,
                session_profit=50.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
            create_session_result(
                outcome=SessionOutcome.PUSH,
                hands_played=100,
                session_profit=0.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
        ]
        stats = aggregate_results(results)

        assert stats.total_sessions == 4
        assert stats.winning_sessions == 2
        assert stats.losing_sessions == 1
        assert stats.push_sessions == 1
        assert stats.session_win_rate == 0.5  # 2/4
        assert stats.total_hands == 400
        assert stats.net_result == 0.0  # 100 - 150 + 50 + 0

    def test_session_win_rate_calculation(self) -> None:
        """Session win rate should be winning_sessions / total_sessions."""
        results = [
            create_session_result(outcome=SessionOutcome.WIN, session_profit=100.0),
            create_session_result(outcome=SessionOutcome.WIN, session_profit=50.0),
            create_session_result(outcome=SessionOutcome.LOSS, session_profit=-75.0),
        ]
        stats = aggregate_results(results)

        assert stats.session_win_rate == pytest.approx(2 / 3)

    def test_expected_value_per_hand_calculation(self) -> None:
        """Expected value per hand = net_result / total_hands."""
        results = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=100,
                session_profit=100.0,
                total_wagered=3000.0,
                total_bonus_wagered=0.0,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                hands_played=100,
                session_profit=-50.0,
                total_wagered=3000.0,
                total_bonus_wagered=0.0,
            ),
        ]
        stats = aggregate_results(results)

        # net_result = 100 - 50 = 50, total_hands = 200
        assert stats.expected_value_per_hand == pytest.approx(0.25)  # 50/200

    def test_total_wagered_calculation(self) -> None:
        """Total wagered should sum main and bonus wagered."""
        results = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                total_wagered=2000.0,
                total_bonus_wagered=50.0,
            ),
        ]
        stats = aggregate_results(results)

        assert stats.main_wagered == 5000.0  # 3000 + 2000
        assert stats.bonus_wagered == 150.0  # 100 + 50
        assert stats.total_wagered == 5150.0  # 5000 + 150

    def test_session_profit_statistics(self) -> None:
        """Session profit statistics (mean, std, median, min, max)."""
        results = [
            create_session_result(outcome=SessionOutcome.WIN, session_profit=100.0),
            create_session_result(outcome=SessionOutcome.WIN, session_profit=200.0),
            create_session_result(outcome=SessionOutcome.LOSS, session_profit=-50.0),
            create_session_result(outcome=SessionOutcome.PUSH, session_profit=0.0),
        ]
        stats = aggregate_results(results)

        # Mean: (100 + 200 - 50 + 0) / 4 = 62.5
        assert stats.session_profit_mean == pytest.approx(62.5)
        assert stats.session_profit_min == -50.0
        assert stats.session_profit_max == 200.0
        # Median of [-50, 0, 100, 200] = (0 + 100) / 2 = 50
        assert stats.session_profit_median == pytest.approx(50.0)

    def test_session_profit_std_single_session(self) -> None:
        """Standard deviation with single session should be 0."""
        results = [
            create_session_result(outcome=SessionOutcome.WIN, session_profit=100.0)
        ]
        stats = aggregate_results(results)

        assert stats.session_profit_std == 0.0

    def test_session_profits_preserved(self) -> None:
        """Session profits should be preserved in tuple for merge support."""
        results = [
            create_session_result(outcome=SessionOutcome.WIN, session_profit=100.0),
            create_session_result(outcome=SessionOutcome.LOSS, session_profit=-50.0),
        ]
        stats = aggregate_results(results)

        assert stats.session_profits == (100.0, -50.0)

    def test_hand_frequencies_empty_without_hand_records(self) -> None:
        """Hand frequencies should be empty when aggregating SessionResults only."""
        results = [
            create_session_result(outcome=SessionOutcome.WIN),
        ]
        stats = aggregate_results(results)

        assert stats.hand_frequencies == {}
        assert stats.hand_frequency_pct == {}


class TestMergeAggregates:
    """Tests for merge_aggregates function."""

    def test_merge_two_simple_aggregates(self) -> None:
        """Merging two aggregates should sum counts and recalculate rates."""
        results1 = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=100,
                session_profit=100.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
        ]
        results2 = [
            create_session_result(
                outcome=SessionOutcome.LOSS,
                hands_played=100,
                session_profit=-50.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
        ]
        agg1 = aggregate_results(results1)
        agg2 = aggregate_results(results2)

        merged = merge_aggregates(agg1, agg2)

        assert merged.total_sessions == 2
        assert merged.winning_sessions == 1
        assert merged.losing_sessions == 1
        assert merged.push_sessions == 0
        assert merged.session_win_rate == 0.5
        assert merged.total_hands == 200
        assert merged.net_result == 50.0  # 100 - 50

    def test_merge_preserves_session_profits(self) -> None:
        """Merged aggregate should preserve all session profits."""
        results1 = [
            create_session_result(outcome=SessionOutcome.WIN, session_profit=100.0),
        ]
        results2 = [
            create_session_result(outcome=SessionOutcome.LOSS, session_profit=-50.0),
            create_session_result(outcome=SessionOutcome.WIN, session_profit=75.0),
        ]
        agg1 = aggregate_results(results1)
        agg2 = aggregate_results(results2)

        merged = merge_aggregates(agg1, agg2)

        assert merged.session_profits == (100.0, -50.0, 75.0)

    def test_merge_recalculates_statistics(self) -> None:
        """Merged aggregate should recalculate profit statistics."""
        results1 = [
            create_session_result(outcome=SessionOutcome.WIN, session_profit=100.0),
            create_session_result(outcome=SessionOutcome.WIN, session_profit=200.0),
        ]
        results2 = [
            create_session_result(outcome=SessionOutcome.LOSS, session_profit=-50.0),
            create_session_result(outcome=SessionOutcome.PUSH, session_profit=0.0),
        ]
        agg1 = aggregate_results(results1)
        agg2 = aggregate_results(results2)

        merged = merge_aggregates(agg1, agg2)

        # Mean: (100 + 200 - 50 + 0) / 4 = 62.5
        assert merged.session_profit_mean == pytest.approx(62.5)
        assert merged.session_profit_min == -50.0
        assert merged.session_profit_max == 200.0
        # Median of [-50, 0, 100, 200] = 50
        assert merged.session_profit_median == pytest.approx(50.0)

    def test_merge_hand_frequencies(self) -> None:
        """Merged aggregate should combine hand frequencies."""
        results1 = [create_session_result(outcome=SessionOutcome.WIN)]
        results2 = [create_session_result(outcome=SessionOutcome.WIN)]
        agg1 = aggregate_with_hand_frequencies(
            results1, {"pair_tens_or_better": 10, "two_pair": 5}
        )
        agg2 = aggregate_with_hand_frequencies(
            results2, {"pair_tens_or_better": 15, "three_of_a_kind": 2}
        )

        merged = merge_aggregates(agg1, agg2)

        assert merged.hand_frequencies["pair_tens_or_better"] == 25
        assert merged.hand_frequencies["two_pair"] == 5
        assert merged.hand_frequencies["three_of_a_kind"] == 2

    def test_merge_recalculates_frequency_percentages(self) -> None:
        """Merged aggregate should recalculate frequency percentages."""
        results1 = [create_session_result(outcome=SessionOutcome.WIN)]
        results2 = [create_session_result(outcome=SessionOutcome.WIN)]
        agg1 = aggregate_with_hand_frequencies(results1, {"pair": 50})
        agg2 = aggregate_with_hand_frequencies(results2, {"pair": 50})

        merged = merge_aggregates(agg1, agg2)

        assert merged.hand_frequencies["pair"] == 100
        assert merged.hand_frequency_pct["pair"] == 1.0

    def test_merge_financial_totals(self) -> None:
        """Merged aggregate should sum financial totals correctly."""
        results1 = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                session_profit=100.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
        ]
        results2 = [
            create_session_result(
                outcome=SessionOutcome.LOSS,
                session_profit=-50.0,
                total_wagered=2000.0,
                total_bonus_wagered=75.0,
            ),
        ]
        agg1 = aggregate_results(results1)
        agg2 = aggregate_results(results2)

        merged = merge_aggregates(agg1, agg2)

        assert merged.main_wagered == 5000.0
        assert merged.bonus_wagered == 175.0
        assert merged.total_wagered == 5175.0
        assert merged.net_result == 50.0


class TestAggregateWithHandFrequencies:
    """Tests for aggregate_with_hand_frequencies function."""

    def test_adds_hand_frequencies(self) -> None:
        """Should include provided hand frequencies in aggregation."""
        results = [
            create_session_result(outcome=SessionOutcome.WIN, hands_played=100),
        ]
        frequencies = {
            "pair_tens_or_better": 15,
            "two_pair": 8,
            "three_of_a_kind": 3,
            "straight": 2,
            "flush": 1,
            "high_card": 71,
        }

        stats = aggregate_with_hand_frequencies(results, frequencies)

        assert stats.hand_frequencies == frequencies
        # Total = 100 hands
        assert stats.hand_frequency_pct["high_card"] == pytest.approx(0.71)
        assert stats.hand_frequency_pct["pair_tens_or_better"] == pytest.approx(0.15)

    def test_preserves_base_statistics(self) -> None:
        """Should preserve all base statistics from aggregate_results."""
        results = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=100,
                session_profit=100.0,
            ),
        ]
        frequencies = {"high_card": 100}

        stats = aggregate_with_hand_frequencies(results, frequencies)

        assert stats.total_sessions == 1
        assert stats.winning_sessions == 1
        assert stats.total_hands == 100
        assert stats.net_result == 100.0

    def test_empty_frequencies(self) -> None:
        """Should handle empty frequency dictionary."""
        results = [create_session_result(outcome=SessionOutcome.WIN)]

        stats = aggregate_with_hand_frequencies(results, {})

        assert stats.hand_frequencies == {}
        assert stats.hand_frequency_pct == {}


class TestAggregateStatisticsDataclass:
    """Tests for AggregateStatistics dataclass properties."""

    def test_dataclass_is_frozen(self) -> None:
        """AggregateStatistics should be immutable."""
        results = [create_session_result(outcome=SessionOutcome.WIN)]
        stats = aggregate_results(results)

        with pytest.raises(AttributeError):
            stats.total_sessions = 999  # type: ignore[misc]

    def test_all_required_fields_present(self) -> None:
        """AggregateStatistics should have all required fields."""
        results = [create_session_result(outcome=SessionOutcome.WIN)]
        stats = aggregate_results(results)

        # Session metrics
        assert hasattr(stats, "total_sessions")
        assert hasattr(stats, "winning_sessions")
        assert hasattr(stats, "losing_sessions")
        assert hasattr(stats, "push_sessions")
        assert hasattr(stats, "session_win_rate")

        # Hand metrics
        assert hasattr(stats, "total_hands")

        # Financial metrics
        assert hasattr(stats, "total_wagered")
        assert hasattr(stats, "total_won")
        assert hasattr(stats, "net_result")
        assert hasattr(stats, "expected_value_per_hand")

        # Main game breakdown
        assert hasattr(stats, "main_wagered")
        assert hasattr(stats, "main_won")
        assert hasattr(stats, "main_ev_per_hand")

        # Bonus breakdown
        assert hasattr(stats, "bonus_wagered")
        assert hasattr(stats, "bonus_won")
        assert hasattr(stats, "bonus_ev_per_hand")

        # Hand distribution
        assert hasattr(stats, "hand_frequencies")
        assert hasattr(stats, "hand_frequency_pct")

        # Session profit distribution
        assert hasattr(stats, "session_profit_mean")
        assert hasattr(stats, "session_profit_std")
        assert hasattr(stats, "session_profit_median")
        assert hasattr(stats, "session_profit_min")
        assert hasattr(stats, "session_profit_max")


class TestKnownDatasetVerification:
    """Tests with known data sets to verify calculation accuracy."""

    def test_known_dataset_simple(self) -> None:
        """Verify calculations with a simple known dataset."""
        # 5 sessions with known outcomes
        results = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=10,
                session_profit=50.0,
                total_wagered=300.0,
                total_bonus_wagered=10.0,
            ),
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=10,
                session_profit=100.0,
                total_wagered=300.0,
                total_bonus_wagered=10.0,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                hands_played=10,
                session_profit=-75.0,
                total_wagered=300.0,
                total_bonus_wagered=10.0,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                hands_played=10,
                session_profit=-100.0,
                total_wagered=300.0,
                total_bonus_wagered=10.0,
            ),
            create_session_result(
                outcome=SessionOutcome.PUSH,
                hands_played=10,
                session_profit=0.0,
                total_wagered=300.0,
                total_bonus_wagered=10.0,
            ),
        ]

        stats = aggregate_results(results)

        # Verify counts
        assert stats.total_sessions == 5
        assert stats.winning_sessions == 2
        assert stats.losing_sessions == 2
        assert stats.push_sessions == 1
        assert stats.session_win_rate == pytest.approx(0.4)  # 2/5

        # Verify totals
        assert stats.total_hands == 50
        assert stats.main_wagered == 1500.0  # 5 * 300
        assert stats.bonus_wagered == 50.0  # 5 * 10
        assert stats.total_wagered == 1550.0

        # Verify net result
        # 50 + 100 - 75 - 100 + 0 = -25
        assert stats.net_result == pytest.approx(-25.0)

        # Verify EV per hand
        # -25 / 50 = -0.5
        assert stats.expected_value_per_hand == pytest.approx(-0.5)

        # Verify profit statistics
        # Profits: [50, 100, -75, -100, 0]
        # Mean: -25/5 = -5
        assert stats.session_profit_mean == pytest.approx(-5.0)
        # Min: -100, Max: 100
        assert stats.session_profit_min == -100.0
        assert stats.session_profit_max == 100.0
        # Median: sorted = [-100, -75, 0, 50, 100] -> 0
        assert stats.session_profit_median == pytest.approx(0.0)

    def test_known_dataset_parallel_merge_equivalence(self) -> None:
        """Verify that merging produces same results as direct aggregation."""
        # Split into two groups
        results_group1 = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=100,
                session_profit=100.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
            create_session_result(
                outcome=SessionOutcome.LOSS,
                hands_played=100,
                session_profit=-50.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
        ]
        results_group2 = [
            create_session_result(
                outcome=SessionOutcome.WIN,
                hands_played=100,
                session_profit=75.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
            create_session_result(
                outcome=SessionOutcome.PUSH,
                hands_played=100,
                session_profit=0.0,
                total_wagered=3000.0,
                total_bonus_wagered=100.0,
            ),
        ]

        # Method 1: Direct aggregation
        all_results = results_group1 + results_group2
        direct_stats = aggregate_results(all_results)

        # Method 2: Merge aggregates (simulating parallel execution)
        agg1 = aggregate_results(results_group1)
        agg2 = aggregate_results(results_group2)
        merged_stats = merge_aggregates(agg1, agg2)

        # Verify equivalence
        assert merged_stats.total_sessions == direct_stats.total_sessions
        assert merged_stats.winning_sessions == direct_stats.winning_sessions
        assert merged_stats.losing_sessions == direct_stats.losing_sessions
        assert merged_stats.push_sessions == direct_stats.push_sessions
        assert merged_stats.session_win_rate == pytest.approx(
            direct_stats.session_win_rate
        )
        assert merged_stats.total_hands == direct_stats.total_hands
        assert merged_stats.total_wagered == pytest.approx(direct_stats.total_wagered)
        assert merged_stats.net_result == pytest.approx(direct_stats.net_result)
        assert merged_stats.expected_value_per_hand == pytest.approx(
            direct_stats.expected_value_per_hand
        )
        assert merged_stats.session_profit_mean == pytest.approx(
            direct_stats.session_profit_mean
        )
        assert merged_stats.session_profit_min == direct_stats.session_profit_min
        assert merged_stats.session_profit_max == direct_stats.session_profit_max
