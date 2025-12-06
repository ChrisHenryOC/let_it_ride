"""Unit tests for factory functions in controller module.

Tests the create_strategy() and create_betting_system() factory functions
with registry pattern implementation.
"""

from typing import Any

import pytest

from let_it_ride.bankroll import (
    DAlembertBetting,
    FibonacciBetting,
    FlatBetting,
    MartingaleBetting,
    ParoliBetting,
    ReverseMartingaleBetting,
)
from let_it_ride.config.models import (
    AggressiveStrategyConfig,
    BankrollConfig,
    BettingSystemConfig,
    ConservativeStrategyConfig,
    CustomBettingConfig,
    CustomStrategyConfig,
    DAlembertBettingConfig,
    FibonacciBettingConfig,
    MartingaleBettingConfig,
    ParoliBettingConfig,
    ProportionalBettingConfig,
    ReverseMartingaleBettingConfig,
    StopConditionsConfig,
    StrategyConfig,
    StrategyRule,
)
from let_it_ride.simulation.controller import (
    _BETTING_SYSTEM_FACTORIES,
    _STRATEGY_FACTORIES,
    create_betting_system,
    create_strategy,
)
from let_it_ride.strategy import (
    AlwaysPullStrategy,
    AlwaysRideStrategy,
    BasicStrategy,
    CustomStrategy,
)


class TestStrategyRegistry:
    """Tests for strategy factory registry."""

    def test_registry_contains_all_types(self) -> None:
        """Test that registry contains all expected strategy types."""
        expected_types = {
            "basic",
            "always_ride",
            "always_pull",
            "conservative",
            "aggressive",
            "custom",
        }
        assert set(_STRATEGY_FACTORIES.keys()) == expected_types

    def test_registry_all_values_are_callable(self) -> None:
        """Test that all registry values are callable."""
        for name, factory in _STRATEGY_FACTORIES.items():
            assert callable(factory), f"Factory for '{name}' is not callable"


class TestCreateStrategy:
    """Tests for create_strategy() factory function."""

    def test_create_basic_strategy(self) -> None:
        """Test creating basic strategy."""
        config = StrategyConfig(type="basic")
        strategy = create_strategy(config)
        assert isinstance(strategy, BasicStrategy)

    def test_create_always_ride_strategy(self) -> None:
        """Test creating always_ride strategy."""
        config = StrategyConfig(type="always_ride")
        strategy = create_strategy(config)
        assert isinstance(strategy, AlwaysRideStrategy)

    def test_create_always_pull_strategy(self) -> None:
        """Test creating always_pull strategy."""
        config = StrategyConfig(type="always_pull")
        strategy = create_strategy(config)
        assert isinstance(strategy, AlwaysPullStrategy)

    def test_create_conservative_strategy(self) -> None:
        """Test creating conservative strategy."""
        config = StrategyConfig(
            type="conservative",
            conservative=ConservativeStrategyConfig(),
        )
        strategy = create_strategy(config)
        # Conservative returns a CustomStrategy configured for conservative play
        assert isinstance(strategy, CustomStrategy)

    def test_create_aggressive_strategy(self) -> None:
        """Test creating aggressive strategy."""
        config = StrategyConfig(
            type="aggressive",
            aggressive=AggressiveStrategyConfig(),
        )
        strategy = create_strategy(config)
        # Aggressive returns a CustomStrategy configured for aggressive play
        assert isinstance(strategy, CustomStrategy)

    def test_create_custom_strategy(self) -> None:
        """Test creating custom strategy with rules."""
        config = StrategyConfig(
            type="custom",
            custom=CustomStrategyConfig(
                bet1_rules=[
                    StrategyRule(condition="has_high_pair", action="ride"),
                    StrategyRule(condition="high_cards >= 3", action="pull"),
                ],
                bet2_rules=[
                    StrategyRule(condition="has_pair", action="ride"),
                    StrategyRule(condition="high_cards >= 2", action="pull"),
                ],
            ),
        )
        strategy = create_strategy(config)
        assert isinstance(strategy, CustomStrategy)

    def test_create_custom_strategy_without_config_raises(self) -> None:
        """Test that custom strategy without config raises ValueError.

        Note: Pydantic validation catches this first with a similar error.
        We test the factory's own validation by bypassing Pydantic.
        """
        # Bypass Pydantic validation to test factory's own validation
        config = StrategyConfig.__new__(StrategyConfig)
        object.__setattr__(config, "type", "custom")
        object.__setattr__(config, "custom", None)
        object.__setattr__(config, "conservative", None)
        object.__setattr__(config, "aggressive", None)

        with pytest.raises(
            ValueError, match="'custom' strategy requires 'custom' config section"
        ):
            create_strategy(config)

    def test_unknown_strategy_type_raises(self) -> None:
        """Test that unknown strategy type raises ValueError."""
        # Create config with invalid type by bypassing Pydantic validation
        config = StrategyConfig.__new__(StrategyConfig)
        object.__setattr__(config, "type", "nonexistent_strategy")
        object.__setattr__(config, "custom", None)
        object.__setattr__(config, "conservative", None)
        object.__setattr__(config, "aggressive", None)

        with pytest.raises(
            ValueError, match="Unknown strategy type: nonexistent_strategy"
        ):
            create_strategy(config)

    def test_all_strategy_types_return_strategy_protocol(self) -> None:
        """Test that all strategy types return objects implementing Strategy protocol."""
        configs: list[StrategyConfig] = [
            StrategyConfig(type="basic"),
            StrategyConfig(type="always_ride"),
            StrategyConfig(type="always_pull"),
            StrategyConfig(
                type="conservative", conservative=ConservativeStrategyConfig()
            ),
            StrategyConfig(type="aggressive", aggressive=AggressiveStrategyConfig()),
            StrategyConfig(
                type="custom",
                custom=CustomStrategyConfig(
                    bet1_rules=[StrategyRule(condition="has_pair", action="pull")],
                    bet2_rules=[StrategyRule(condition="has_pair", action="pull")],
                ),
            ),
        ]

        for config in configs:
            strategy = create_strategy(config)
            # Verify it has the Strategy protocol methods
            assert hasattr(strategy, "decide_bet1")
            assert hasattr(strategy, "decide_bet2")
            assert callable(strategy.decide_bet1)
            assert callable(strategy.decide_bet2)


class TestBettingSystemRegistry:
    """Tests for betting system factory registry."""

    def test_registry_contains_all_types(self) -> None:
        """Test that registry contains all expected betting system types."""
        expected_types = {
            "flat",
            "martingale",
            "reverse_martingale",
            "paroli",
            "dalembert",
            "fibonacci",
            "proportional",
            "custom",
        }
        assert set(_BETTING_SYSTEM_FACTORIES.keys()) == expected_types

    def test_registry_not_implemented_types_are_none(self) -> None:
        """Test that not-implemented types have None as their factory."""
        assert _BETTING_SYSTEM_FACTORIES["proportional"] is None
        assert _BETTING_SYSTEM_FACTORIES["custom"] is None

    def test_registry_implemented_types_are_callable(self) -> None:
        """Test that implemented types have callable factories."""
        implemented_types = [
            "flat",
            "martingale",
            "reverse_martingale",
            "paroli",
            "dalembert",
            "fibonacci",
        ]
        for name in implemented_types:
            factory = _BETTING_SYSTEM_FACTORIES[name]
            assert factory is not None, f"Factory for '{name}' should not be None"
            assert callable(factory), f"Factory for '{name}' is not callable"


def _create_bankroll_config(
    betting_type: str,
    **kwargs: Any,
) -> BankrollConfig:
    """Create a BankrollConfig for testing.

    Args:
        betting_type: The betting system type.
        **kwargs: Additional config sections to include.

    Returns:
        A BankrollConfig instance.
    """
    return BankrollConfig(
        starting_amount=500.0,
        base_bet=5.0,
        stop_conditions=StopConditionsConfig(),
        betting_system=BettingSystemConfig(type=betting_type, **kwargs),
    )


def _create_bankroll_config_bypassing_validation(betting_type: str) -> BankrollConfig:
    """Create a BankrollConfig bypassing Pydantic validation.

    This is used to test the factory function's own validation logic
    independent of Pydantic model validators.

    Args:
        betting_type: The betting system type.

    Returns:
        A BankrollConfig with a betting system that has no subsection config.
    """
    # Bypass Pydantic validation for the betting system config
    betting_system = BettingSystemConfig.__new__(BettingSystemConfig)
    object.__setattr__(betting_system, "type", betting_type)
    object.__setattr__(betting_system, "martingale", None)
    object.__setattr__(betting_system, "reverse_martingale", None)
    object.__setattr__(betting_system, "paroli", None)
    object.__setattr__(betting_system, "dalembert", None)
    object.__setattr__(betting_system, "fibonacci", None)
    object.__setattr__(betting_system, "proportional", None)
    object.__setattr__(betting_system, "custom", None)

    # Also bypass BankrollConfig validation
    config = BankrollConfig.__new__(BankrollConfig)
    object.__setattr__(config, "starting_amount", 500.0)
    object.__setattr__(config, "base_bet", 5.0)
    object.__setattr__(config, "stop_conditions", StopConditionsConfig())
    object.__setattr__(config, "betting_system", betting_system)

    return config


class TestCreateBettingSystem:
    """Tests for create_betting_system() factory function."""

    def test_create_flat_betting(self) -> None:
        """Test creating flat betting system."""
        config = _create_bankroll_config("flat")
        system = create_betting_system(config)
        assert isinstance(system, FlatBetting)

    def test_create_martingale_betting(self) -> None:
        """Test creating martingale betting system."""
        config = _create_bankroll_config(
            "martingale",
            martingale=MartingaleBettingConfig(
                loss_multiplier=2.0,
                max_bet=100.0,
                max_progressions=5,
            ),
        )
        system = create_betting_system(config)
        assert isinstance(system, MartingaleBetting)

    def test_create_reverse_martingale_betting(self) -> None:
        """Test creating reverse martingale betting system."""
        config = _create_bankroll_config(
            "reverse_martingale",
            reverse_martingale=ReverseMartingaleBettingConfig(
                win_multiplier=2.0,
                max_bet=100.0,
                profit_target_streak=3,
            ),
        )
        system = create_betting_system(config)
        assert isinstance(system, ReverseMartingaleBetting)

    def test_create_paroli_betting(self) -> None:
        """Test creating paroli betting system."""
        config = _create_bankroll_config(
            "paroli",
            paroli=ParoliBettingConfig(
                win_multiplier=2.0,
                max_bet=100.0,
                wins_before_reset=3,
            ),
        )
        system = create_betting_system(config)
        assert isinstance(system, ParoliBetting)

    def test_create_dalembert_betting(self) -> None:
        """Test creating D'Alembert betting system."""
        config = _create_bankroll_config(
            "dalembert",
            dalembert=DAlembertBettingConfig(
                unit=5.0,
                min_bet=5.0,
                max_bet=100.0,
            ),
        )
        system = create_betting_system(config)
        assert isinstance(system, DAlembertBetting)

    def test_create_fibonacci_betting(self) -> None:
        """Test creating Fibonacci betting system."""
        config = _create_bankroll_config(
            "fibonacci",
            fibonacci=FibonacciBettingConfig(
                unit=5.0,
                max_bet=100.0,
                max_position=10,
                win_regression=2,
            ),
        )
        system = create_betting_system(config)
        assert isinstance(system, FibonacciBetting)

    def test_proportional_betting_not_implemented(self) -> None:
        """Test that proportional betting raises NotImplementedError."""
        config = _create_bankroll_config(
            "proportional",
            proportional=ProportionalBettingConfig(),
        )
        with pytest.raises(
            NotImplementedError, match="'proportional' is not yet implemented"
        ):
            create_betting_system(config)

    def test_custom_betting_not_implemented(self) -> None:
        """Test that custom betting raises NotImplementedError."""
        config = _create_bankroll_config(
            "custom",
            custom=CustomBettingConfig(),
        )
        with pytest.raises(
            NotImplementedError, match="'custom' is not yet implemented"
        ):
            create_betting_system(config)

    def test_unknown_betting_type_raises(self) -> None:
        """Test that unknown betting type raises ValueError."""
        # Create config with invalid type by bypassing Pydantic validation
        betting_system = BettingSystemConfig.__new__(BettingSystemConfig)
        object.__setattr__(betting_system, "type", "nonexistent_system")
        object.__setattr__(betting_system, "martingale", None)
        object.__setattr__(betting_system, "reverse_martingale", None)
        object.__setattr__(betting_system, "paroli", None)
        object.__setattr__(betting_system, "dalembert", None)
        object.__setattr__(betting_system, "fibonacci", None)
        object.__setattr__(betting_system, "proportional", None)
        object.__setattr__(betting_system, "custom", None)

        config = BankrollConfig(
            starting_amount=500.0,
            base_bet=5.0,
            stop_conditions=StopConditionsConfig(),
            betting_system=betting_system,
        )

        with pytest.raises(
            ValueError, match="Unknown betting system type: nonexistent_system"
        ):
            create_betting_system(config)

    def test_martingale_without_config_raises(self) -> None:
        """Test that martingale without config section raises ValueError.

        Note: Pydantic validation catches this first. We bypass it to test factory validation.
        """
        config = _create_bankroll_config_bypassing_validation("martingale")
        with pytest.raises(
            ValueError, match="'martingale' betting requires 'martingale' config"
        ):
            create_betting_system(config)

    def test_reverse_martingale_without_config_raises(self) -> None:
        """Test that reverse_martingale without config section raises ValueError.

        Note: Pydantic validation catches this first. We bypass it to test factory validation.
        """
        config = _create_bankroll_config_bypassing_validation("reverse_martingale")
        with pytest.raises(
            ValueError,
            match="'reverse_martingale' betting requires 'reverse_martingale' config",
        ):
            create_betting_system(config)

    def test_paroli_without_config_raises(self) -> None:
        """Test that paroli without config section raises ValueError.

        Note: Pydantic validation catches this first. We bypass it to test factory validation.
        """
        config = _create_bankroll_config_bypassing_validation("paroli")
        with pytest.raises(
            ValueError, match="'paroli' betting requires 'paroli' config"
        ):
            create_betting_system(config)

    def test_dalembert_without_config_raises(self) -> None:
        """Test that dalembert without config section raises ValueError.

        Note: Pydantic validation catches this first. We bypass it to test factory validation.
        """
        config = _create_bankroll_config_bypassing_validation("dalembert")
        with pytest.raises(
            ValueError, match="'dalembert' betting requires 'dalembert' config"
        ):
            create_betting_system(config)

    def test_fibonacci_without_config_raises(self) -> None:
        """Test that fibonacci without config section raises ValueError.

        Note: Pydantic validation catches this first. We bypass it to test factory validation.
        """
        config = _create_bankroll_config_bypassing_validation("fibonacci")
        with pytest.raises(
            ValueError, match="'fibonacci' betting requires 'fibonacci' config"
        ):
            create_betting_system(config)

    def test_all_implemented_types_return_betting_system_protocol(self) -> None:
        """Test that all implemented types return objects implementing BettingSystem protocol."""
        configs: list[BankrollConfig] = [
            _create_bankroll_config("flat"),
            _create_bankroll_config(
                "martingale",
                martingale=MartingaleBettingConfig(
                    loss_multiplier=2.0, max_bet=100.0, max_progressions=5
                ),
            ),
            _create_bankroll_config(
                "reverse_martingale",
                reverse_martingale=ReverseMartingaleBettingConfig(
                    win_multiplier=2.0, max_bet=100.0, profit_target_streak=3
                ),
            ),
            _create_bankroll_config(
                "paroli",
                paroli=ParoliBettingConfig(
                    win_multiplier=2.0, max_bet=100.0, wins_before_reset=3
                ),
            ),
            _create_bankroll_config(
                "dalembert",
                dalembert=DAlembertBettingConfig(unit=5.0, min_bet=5.0, max_bet=100.0),
            ),
            _create_bankroll_config(
                "fibonacci",
                fibonacci=FibonacciBettingConfig(
                    unit=5.0, max_bet=100.0, max_position=10, win_regression=2
                ),
            ),
        ]

        for config in configs:
            system = create_betting_system(config)
            # Verify it has the BettingSystem protocol methods
            assert hasattr(system, "get_bet")
            assert hasattr(system, "record_result")
            assert hasattr(system, "reset")
            assert callable(system.get_bet)
            assert callable(system.record_result)
            assert callable(system.reset)
