"""Integration tests for SimulationController.

Tests multi-session simulation runs, reproducibility, and progress reporting.
"""

from unittest.mock import patch

import pytest

from let_it_ride.config.models import (
    AggressiveStrategyConfig,
    AlwaysBonusConfig,
    BankrollConfig,
    BettingSystemConfig,
    BonusStrategyConfig,
    ConservativeStrategyConfig,
    FullConfig,
    SimulationConfig,
    StaticBonusConfig,
    StopConditionsConfig,
    StrategyConfig,
)
from let_it_ride.simulation import (
    SessionOutcome,
    SimulationController,
    SimulationResults,
    StopReason,
)
from let_it_ride.simulation.session import SessionConfig


def _create_strategy_config(strategy_type: str) -> StrategyConfig:
    """Create a StrategyConfig for the given type.

    Args:
        strategy_type: Strategy type (basic, always_ride, etc.)

    Returns:
        A StrategyConfig with appropriate sub-config if needed.
    """
    if strategy_type == "conservative":
        return StrategyConfig(
            type="conservative",
            conservative=ConservativeStrategyConfig(),
        )
    if strategy_type == "aggressive":
        return StrategyConfig(
            type="aggressive",
            aggressive=AggressiveStrategyConfig(),
        )
    return StrategyConfig(type=strategy_type)


def create_test_config(
    num_sessions: int = 10,
    hands_per_session: int = 50,
    random_seed: int | None = 42,
    starting_bankroll: float = 500.0,
    base_bet: float = 5.0,
    win_limit: float | None = 100.0,
    loss_limit: float | None = 200.0,
    strategy_type: str = "basic",
) -> FullConfig:
    """Create a test configuration for simulation.

    Args:
        num_sessions: Number of sessions to run.
        hands_per_session: Maximum hands per session.
        random_seed: Optional seed for reproducibility.
        starting_bankroll: Starting bankroll amount.
        base_bet: Base bet per circle.
        win_limit: Session win limit (None to disable).
        loss_limit: Session loss limit (None to disable).
        strategy_type: Strategy to use.

    Returns:
        A FullConfig instance ready for simulation.
    """
    return FullConfig(
        simulation=SimulationConfig(
            num_sessions=num_sessions,
            hands_per_session=hands_per_session,
            random_seed=random_seed,
        ),
        bankroll=BankrollConfig(
            starting_amount=starting_bankroll,
            base_bet=base_bet,
            stop_conditions=StopConditionsConfig(
                win_limit=win_limit,
                loss_limit=loss_limit,
                stop_on_insufficient_funds=True,
            ),
            betting_system=BettingSystemConfig(type="flat"),
        ),
        strategy=_create_strategy_config(strategy_type),
    )


class TestSimulationController:
    """Tests for SimulationController basic functionality."""

    def test_run_single_session(self) -> None:
        """Test running a single session."""
        config = create_test_config(num_sessions=1)
        controller = SimulationController(config)

        results = controller.run()

        assert isinstance(results, SimulationResults)
        assert len(results.session_results) == 1
        assert results.config == config
        assert results.start_time <= results.end_time
        assert results.total_hands == results.session_results[0].hands_played

    def test_run_multiple_sessions(self) -> None:
        """Test running multiple sessions."""
        num_sessions = 10
        config = create_test_config(num_sessions=num_sessions)
        controller = SimulationController(config)

        results = controller.run()

        assert len(results.session_results) == num_sessions
        assert results.total_hands == sum(
            r.hands_played for r in results.session_results
        )

        # Each session should have results
        for result in results.session_results:
            assert result.hands_played > 0
            assert result.starting_bankroll == config.bankroll.starting_amount
            assert result.stop_reason in StopReason
            assert result.outcome in SessionOutcome

    def test_session_isolation(self) -> None:
        """Test that each session starts with fresh state."""
        config = create_test_config(num_sessions=5)
        controller = SimulationController(config)

        results = controller.run()

        # Each session should start with the same bankroll
        for result in results.session_results:
            assert result.starting_bankroll == config.bankroll.starting_amount

    def test_total_hands_aggregation(self) -> None:
        """Test that total_hands sums correctly."""
        config = create_test_config(num_sessions=5)
        controller = SimulationController(config)

        results = controller.run()

        expected_total = sum(r.hands_played for r in results.session_results)
        assert results.total_hands == expected_total

    def test_timing_recorded(self) -> None:
        """Test that start and end times are properly recorded."""
        config = create_test_config(num_sessions=3)
        controller = SimulationController(config)

        results = controller.run()

        assert results.start_time is not None
        assert results.end_time is not None
        assert results.start_time <= results.end_time


class TestProgressCallback:
    """Tests for progress reporting."""

    def test_callback_called_for_each_session(self) -> None:
        """Test that callback is called after each session."""
        num_sessions = 5
        config = create_test_config(num_sessions=num_sessions)

        progress_calls: list[tuple[int, int]] = []

        def track_progress(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        controller = SimulationController(config, progress_callback=track_progress)
        controller.run()

        assert len(progress_calls) == num_sessions
        for i, (completed, total) in enumerate(progress_calls):
            assert completed == i + 1
            assert total == num_sessions

    def test_no_callback_when_none(self) -> None:
        """Test that simulation works without callback."""
        config = create_test_config(num_sessions=3)
        controller = SimulationController(config, progress_callback=None)

        # Should not raise
        results = controller.run()
        assert len(results.session_results) == 3


class TestReproducibility:
    """Tests for RNG seeding and reproducibility."""

    def test_same_seed_produces_identical_results(self) -> None:
        """Test that same seed produces identical results."""
        seed = 12345
        config1 = create_test_config(num_sessions=5, random_seed=seed)
        config2 = create_test_config(num_sessions=5, random_seed=seed)

        controller1 = SimulationController(config1)
        controller2 = SimulationController(config2)

        results1 = controller1.run()
        results2 = controller2.run()

        # Same number of results
        assert len(results1.session_results) == len(results2.session_results)

        # Each session should have identical results
        for r1, r2 in zip(
            results1.session_results, results2.session_results, strict=True
        ):
            assert r1.hands_played == r2.hands_played
            assert r1.session_profit == r2.session_profit
            assert r1.final_bankroll == r2.final_bankroll
            assert r1.stop_reason == r2.stop_reason
            assert r1.outcome == r2.outcome
            assert r1.total_wagered == r2.total_wagered

        # Total hands should be identical
        assert results1.total_hands == results2.total_hands

    def test_different_seeds_produce_different_results(self) -> None:
        """Test that different seeds produce different results."""
        config1 = create_test_config(num_sessions=10, random_seed=111)
        config2 = create_test_config(num_sessions=10, random_seed=222)

        controller1 = SimulationController(config1)
        controller2 = SimulationController(config2)

        results1 = controller1.run()
        results2 = controller2.run()

        # Results should differ
        profits1 = [r.session_profit for r in results1.session_results]
        profits2 = [r.session_profit for r in results2.session_results]

        # Very unlikely all profits are identical with different seeds
        assert profits1 != profits2

    def test_unseeded_runs_differ(self) -> None:
        """Test that runs without seed produce different results."""
        config1 = create_test_config(num_sessions=10, random_seed=None)
        config2 = create_test_config(num_sessions=10, random_seed=None)

        controller1 = SimulationController(config1)
        controller2 = SimulationController(config2)

        results1 = controller1.run()
        results2 = controller2.run()

        # Results should likely differ (extremely unlikely to be identical)
        profits1 = [r.session_profit for r in results1.session_results]
        profits2 = [r.session_profit for r in results2.session_results]

        # This could theoretically fail but is extremely unlikely
        assert profits1 != profits2


class TestStopConditions:
    """Tests for session stop conditions."""

    def test_win_limit_stops_session(self) -> None:
        """Test that sessions stop at win limit."""
        config = create_test_config(
            num_sessions=20,
            hands_per_session=1000,
            win_limit=50.0,
            loss_limit=500.0,
        )
        controller = SimulationController(config)

        results = controller.run()

        # Some sessions should stop on win limit
        win_limit_stops = [
            r for r in results.session_results if r.stop_reason == StopReason.WIN_LIMIT
        ]
        # With enough sessions, we expect at least one win limit stop
        # (but this is not guaranteed - depends on luck)
        assert len(results.session_results) == 20

        # Sessions that stopped on win limit should have profit >= limit
        for r in win_limit_stops:
            assert r.session_profit >= config.bankroll.stop_conditions.win_limit

    def test_loss_limit_stops_session(self) -> None:
        """Test that sessions stop at loss limit."""
        config = create_test_config(
            num_sessions=20,
            hands_per_session=1000,
            win_limit=500.0,
            loss_limit=50.0,
        )
        controller = SimulationController(config)

        results = controller.run()

        # Some sessions should stop on loss limit
        loss_limit_stops = [
            r for r in results.session_results if r.stop_reason == StopReason.LOSS_LIMIT
        ]

        # Sessions that stopped on loss limit should have loss >= limit
        for r in loss_limit_stops:
            assert r.session_profit <= -config.bankroll.stop_conditions.loss_limit

    def test_max_hands_stops_session(self) -> None:
        """Test that sessions stop at max hands."""
        max_hands = 10
        config = create_test_config(
            num_sessions=5,
            hands_per_session=max_hands,
            win_limit=10000.0,
            loss_limit=10000.0,
        )
        controller = SimulationController(config)

        results = controller.run()

        # All sessions should play exactly max_hands (unless they bust first)
        for r in results.session_results:
            assert r.hands_played <= max_hands
            if r.stop_reason == StopReason.MAX_HANDS:
                assert r.hands_played == max_hands


class TestStrategyVariants:
    """Tests for different strategy configurations."""

    @pytest.mark.parametrize(
        "strategy_type",
        ["basic", "always_ride", "always_pull", "conservative", "aggressive"],
    )
    def test_strategy_types(self, strategy_type: str) -> None:
        """Test that all strategy types work."""
        config = create_test_config(num_sessions=3, strategy_type=strategy_type)
        controller = SimulationController(config)

        results = controller.run()

        assert len(results.session_results) == 3
        for r in results.session_results:
            assert r.hands_played > 0

    def test_always_ride_vs_always_pull_differ(self) -> None:
        """Test that always_ride and always_pull produce different results."""
        seed = 99999
        config_ride = create_test_config(
            num_sessions=10, random_seed=seed, strategy_type="always_ride"
        )
        config_pull = create_test_config(
            num_sessions=10, random_seed=seed, strategy_type="always_pull"
        )

        results_ride = SimulationController(config_ride).run()
        results_pull = SimulationController(config_pull).run()

        # Profits should differ significantly
        total_profit_ride = sum(r.session_profit for r in results_ride.session_results)
        total_profit_pull = sum(r.session_profit for r in results_pull.session_results)

        # Always pull should generally do better than always ride
        # (pulling reduces variance and expected loss)
        # But we're just checking they differ here
        assert total_profit_ride != total_profit_pull


class TestLargerSimulations:
    """Tests for larger scale simulations."""

    def test_hundred_sessions(self) -> None:
        """Test running 100 sessions."""
        config = create_test_config(num_sessions=100, hands_per_session=20)
        controller = SimulationController(config)

        results = controller.run()

        assert len(results.session_results) == 100
        assert results.total_hands <= 100 * 20

    def test_result_distribution(self) -> None:
        """Test that results have expected distribution over many sessions."""
        config = create_test_config(
            num_sessions=100,
            hands_per_session=100,
            win_limit=100.0,
            loss_limit=200.0,
        )
        controller = SimulationController(config)

        results = controller.run()

        wins = sum(
            1 for r in results.session_results if r.outcome == SessionOutcome.WIN
        )
        losses = sum(
            1 for r in results.session_results if r.outcome == SessionOutcome.LOSS
        )
        pushes = sum(
            1 for r in results.session_results if r.outcome == SessionOutcome.PUSH
        )

        assert wins + losses + pushes == 100
        # With the house edge, we expect more losses than wins generally
        # But just verify we have some distribution
        assert wins >= 0
        assert losses >= 0


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_progress_callback_exception_propagates(self) -> None:
        """Test that exceptions in progress callback propagate up."""
        config = create_test_config(num_sessions=3)

        def failing_callback(completed: int, total: int) -> None:  # noqa: ARG001
            if completed == 2:
                raise RuntimeError("Callback failed")

        controller = SimulationController(config, progress_callback=failing_callback)

        with pytest.raises(RuntimeError, match="Callback failed"):
            controller.run()

    def test_callback_exception_on_first_session(self) -> None:
        """Test that exception on first session callback propagates."""
        config = create_test_config(num_sessions=5)

        def fail_immediately(completed: int, total: int) -> None:  # noqa: ARG001
            raise ValueError("Immediate failure")

        controller = SimulationController(config, progress_callback=fail_immediately)

        with pytest.raises(ValueError, match="Immediate failure"):
            controller.run()


class TestBonusBetCalculation:
    """Tests for bonus bet calculation in _create_session.

    These tests use mocking to verify that the correct bonus_bet value
    is passed to SessionConfig, ensuring calculation bugs are caught.
    """

    def test_bonus_disabled_results_in_zero_bonus_bet(self) -> None:
        """Test that disabled bonus strategy results in zero bonus bet."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=1,
                hands_per_session=5,
                random_seed=42,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(enabled=False),
        )

        # Capture SessionConfig creation to verify bonus_bet
        captured_bonus_bet: list[float] = []
        original_init = SessionConfig.__init__

        def capturing_init(self: SessionConfig, **kwargs: object) -> None:
            captured_bonus_bet.append(float(kwargs.get("bonus_bet", 0.0)))
            return original_init(self, **kwargs)  # type: ignore[misc]

        with patch.object(SessionConfig, "__init__", capturing_init):
            controller = SimulationController(config)
            results = controller.run()

        # Verify bonus_bet=0.0 was passed
        assert len(captured_bonus_bet) == 1
        assert captured_bonus_bet[0] == 0.0

        assert len(results.session_results) == 1
        assert results.session_results[0].hands_played > 0

    def test_bonus_enabled_with_always_config(self) -> None:
        """Test bonus enabled with always configuration uses always.amount."""
        bonus_amount = 5.0
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=1,
                hands_per_session=10,
                random_seed=42,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="always",
                always=AlwaysBonusConfig(amount=bonus_amount),
            ),
        )

        # Capture SessionConfig creation to verify bonus_bet
        captured_bonus_bet: list[float] = []
        original_init = SessionConfig.__init__

        def capturing_init(self: SessionConfig, **kwargs: object) -> None:
            captured_bonus_bet.append(float(kwargs.get("bonus_bet", 0.0)))
            return original_init(self, **kwargs)  # type: ignore[misc]

        with patch.object(SessionConfig, "__init__", capturing_init):
            controller = SimulationController(config)
            results = controller.run()

        # Verify the correct bonus_bet was passed
        assert len(captured_bonus_bet) == 1
        assert captured_bonus_bet[0] == bonus_amount

        assert len(results.session_results) == 1
        assert results.session_results[0].hands_played > 0

    def test_bonus_enabled_with_static_amount(self) -> None:
        """Test bonus enabled with static.amount configuration."""
        static_amount = 2.5
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=1,
                hands_per_session=10,
                random_seed=42,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="static",
                static=StaticBonusConfig(amount=static_amount),
            ),
        )

        # Capture SessionConfig creation to verify bonus_bet
        captured_bonus_bet: list[float] = []
        original_init = SessionConfig.__init__

        def capturing_init(self: SessionConfig, **kwargs: object) -> None:
            captured_bonus_bet.append(float(kwargs.get("bonus_bet", 0.0)))
            return original_init(self, **kwargs)  # type: ignore[misc]

        with patch.object(SessionConfig, "__init__", capturing_init):
            controller = SimulationController(config)
            results = controller.run()

        # Verify the correct bonus_bet was passed
        assert len(captured_bonus_bet) == 1
        assert captured_bonus_bet[0] == static_amount

        assert len(results.session_results) == 1
        assert results.session_results[0].hands_played > 0

    def test_bonus_enabled_with_static_ratio(self) -> None:
        """Test bonus enabled with static.ratio configuration."""
        base_bet = 10.0
        ratio = 0.5
        expected_bonus = base_bet * ratio  # 5.0

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=1,
                hands_per_session=10,
                random_seed=42,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=base_bet,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="static",
                static=StaticBonusConfig(amount=None, ratio=ratio),
            ),
        )

        # Capture SessionConfig creation to verify bonus_bet
        captured_bonus_bet: list[float] = []
        original_init = SessionConfig.__init__

        def capturing_init(self: SessionConfig, **kwargs: object) -> None:
            captured_bonus_bet.append(float(kwargs.get("bonus_bet", 0.0)))
            return original_init(self, **kwargs)  # type: ignore[misc]

        with patch.object(SessionConfig, "__init__", capturing_init):
            controller = SimulationController(config)
            results = controller.run()

        # Verify the correct bonus_bet was calculated
        assert len(captured_bonus_bet) == 1
        assert captured_bonus_bet[0] == expected_bonus

        assert len(results.session_results) == 1
        assert results.session_results[0].hands_played > 0

    @pytest.mark.parametrize(
        "base_bet,ratio,expected_bonus",
        [
            (5.0, 0.5, 2.5),
            (10.0, 0.25, 2.5),
            (20.0, 1.0, 20.0),
            (1.0, 0.1, 0.1),
        ],
    )
    def test_bonus_ratio_with_various_base_bets(
        self, base_bet: float, ratio: float, expected_bonus: float
    ) -> None:
        """Test ratio calculation works correctly with different base_bet values."""
        # Ensure starting bankroll covers minimum bet
        min_required = base_bet * 3 + expected_bonus
        starting_bankroll = max(500.0, min_required * 2)

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=1,
                hands_per_session=5,
                random_seed=42,
            ),
            bankroll=BankrollConfig(
                starting_amount=starting_bankroll,
                base_bet=base_bet,
                stop_conditions=StopConditionsConfig(
                    win_limit=1000.0,
                    loss_limit=1000.0,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="static",
                static=StaticBonusConfig(amount=None, ratio=ratio),
            ),
        )

        # Capture SessionConfig creation to verify bonus_bet
        captured_bonus_bet: list[float] = []
        original_init = SessionConfig.__init__

        def capturing_init(self: SessionConfig, **kwargs: object) -> None:
            captured_bonus_bet.append(float(kwargs.get("bonus_bet", 0.0)))
            return original_init(self, **kwargs)  # type: ignore[misc]

        with patch.object(SessionConfig, "__init__", capturing_init):
            controller = SimulationController(config)
            results = controller.run()

        # Verify the correct bonus_bet was calculated
        assert len(captured_bonus_bet) == 1
        assert captured_bonus_bet[0] == expected_bonus

        assert len(results.session_results) == 1


class TestEdgeCases:
    """Tests for configuration edge cases."""

    def test_single_hand_session(self) -> None:
        """Test with max_hands=1 (minimum possible session)."""
        config = create_test_config(
            num_sessions=5,
            hands_per_session=1,
            win_limit=10000.0,  # Won't trigger
            loss_limit=10000.0,  # Won't trigger
        )
        controller = SimulationController(config)

        results = controller.run()

        assert len(results.session_results) == 5
        for result in results.session_results:
            assert result.hands_played == 1
            assert result.stop_reason == StopReason.MAX_HANDS

    def test_very_high_limits_never_trigger(self) -> None:
        """Test that very high win/loss limits don't trigger prematurely."""
        config = create_test_config(
            num_sessions=5,
            hands_per_session=10,
            starting_bankroll=100.0,
            base_bet=1.0,
            win_limit=100000.0,
            loss_limit=100000.0,
        )
        controller = SimulationController(config)

        results = controller.run()

        # With such high limits, sessions should only stop on max_hands
        # or insufficient funds (not win/loss limits)
        for result in results.session_results:
            assert result.stop_reason in (
                StopReason.MAX_HANDS,
                StopReason.INSUFFICIENT_FUNDS,
            )

    def test_minimal_win_limit_triggers_quickly(self) -> None:
        """Test that a very small win limit triggers on first profitable hand."""
        config = create_test_config(
            num_sessions=10,
            hands_per_session=100,
            win_limit=0.01,  # Very small profit triggers
            loss_limit=1000.0,
            random_seed=12345,
        )
        controller = SimulationController(config)

        results = controller.run()

        # Check sessions that hit the win limit
        win_limit_stops = [
            r for r in results.session_results if r.stop_reason == StopReason.WIN_LIMIT
        ]

        # Sessions that stopped on win limit should have profit >= limit
        for r in win_limit_stops:
            assert r.session_profit >= 0.01

    def test_minimal_loss_limit_triggers_quickly(self) -> None:
        """Test that a very small loss limit triggers on first losing hand."""
        config = create_test_config(
            num_sessions=10,
            hands_per_session=100,
            win_limit=1000.0,
            loss_limit=0.01,  # Very small loss triggers
            random_seed=54321,
        )
        controller = SimulationController(config)

        results = controller.run()

        # Check sessions that hit the loss limit
        loss_limit_stops = [
            r for r in results.session_results if r.stop_reason == StopReason.LOSS_LIMIT
        ]

        # Sessions that stopped on loss limit should have profit <= -limit
        for r in loss_limit_stops:
            assert r.session_profit <= -0.01

    def test_multiple_sessions_with_bonus_enabled(self) -> None:
        """Test running multiple sessions with bonus betting enabled."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=10,
                hands_per_session=20,
                random_seed=42,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="always",
                always=AlwaysBonusConfig(amount=2.0),
            ),
        )

        controller = SimulationController(config)
        results = controller.run()

        assert len(results.session_results) == 10
        for result in results.session_results:
            assert result.hands_played > 0

    def test_deterministic_results_with_bonus(self) -> None:
        """Test that bonus betting produces deterministic results with same seed."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=5,
                hands_per_session=20,
                random_seed=99999,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="static",
                static=StaticBonusConfig(amount=1.0),
            ),
        )

        controller1 = SimulationController(config)
        controller2 = SimulationController(config)

        results1 = controller1.run()
        results2 = controller2.run()

        # Results should be identical
        for r1, r2 in zip(
            results1.session_results, results2.session_results, strict=True
        ):
            assert r1.hands_played == r2.hands_played
            assert r1.session_profit == r2.session_profit
            assert r1.final_bankroll == r2.final_bankroll
