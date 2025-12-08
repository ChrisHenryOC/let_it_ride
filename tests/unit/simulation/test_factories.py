"""Unit tests for factory functions in controller and utils modules.

Tests the create_strategy(), create_betting_system(), get_main_paytable(),
and get_bonus_paytable() factory functions with registry pattern implementation.
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
    BonusPaytableConfig,
    BonusStrategyConfig,
    ConservativeStrategyConfig,
    CustomBettingConfig,
    CustomStrategyConfig,
    DAlembertBettingConfig,
    FibonacciBettingConfig,
    FullConfig,
    MainGamePaytableConfig,
    MartingaleBettingConfig,
    ParoliBettingConfig,
    PaytablesConfig,
    ProportionalBettingConfig,
    ReverseMartingaleBettingConfig,
    StopConditionsConfig,
    StrategyConfig,
    StrategyRule,
)
from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_a,
    bonus_paytable_b,
    bonus_paytable_c,
    standard_main_paytable,
)
from let_it_ride.simulation.controller import (
    _BETTING_SYSTEM_FACTORIES,
    _STRATEGY_FACTORIES,
    _action_to_decision,
    create_betting_system,
    create_strategy,
)
from let_it_ride.simulation.utils import (
    get_bonus_paytable,
    get_main_paytable,
)
from let_it_ride.strategy import (
    AlwaysPullStrategy,
    AlwaysRideStrategy,
    BasicStrategy,
    CustomStrategy,
)
from let_it_ride.strategy.base import Decision


class TestActionToDecision:
    """Tests for _action_to_decision helper function."""

    def test_ride_action_returns_ride_decision(self) -> None:
        """Test that 'ride' returns Decision.RIDE."""
        assert _action_to_decision("ride") == Decision.RIDE

    def test_pull_action_returns_pull_decision(self) -> None:
        """Test that 'pull' returns Decision.PULL."""
        assert _action_to_decision("pull") == Decision.PULL

    def test_unknown_action_returns_pull_decision(self) -> None:
        """Test that unknown actions default to Decision.PULL.

        This documents the implicit behavior that any non-"ride" string
        defaults to PULL. This is intentional - the config validation
        layer (Pydantic) ensures only valid values reach this function.
        """
        assert _action_to_decision("invalid") == Decision.PULL
        assert _action_to_decision("") == Decision.PULL

    def test_action_is_case_sensitive(self) -> None:
        """Test that action matching is case-sensitive.

        Only lowercase 'ride' returns Decision.RIDE. Pydantic validation
        ensures case-correct values, so this documents the raw behavior.
        """
        assert _action_to_decision("Ride") == Decision.PULL
        assert _action_to_decision("RIDE") == Decision.PULL
        assert _action_to_decision("Pull") == Decision.PULL
        assert _action_to_decision("PULL") == Decision.PULL


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

    def test_create_custom_strategy_verifies_rule_conversion(self) -> None:
        """Test that custom strategy rules are correctly converted.

        Verifies that string actions ("ride"/"pull") are converted to
        Decision enum values in the resulting strategy.
        """
        config = StrategyConfig(
            type="custom",
            custom=CustomStrategyConfig(
                bet1_rules=[
                    StrategyRule(condition="has_high_pair", action="ride"),
                ],
                bet2_rules=[
                    StrategyRule(condition="has_pair", action="pull"),
                ],
            ),
        )
        strategy = create_strategy(config)
        assert isinstance(strategy, CustomStrategy)

        # Verify bet1 rules were converted correctly
        assert len(strategy.bet1_rules) == 1
        assert strategy.bet1_rules[0].condition == "has_high_pair"
        assert strategy.bet1_rules[0].action == Decision.RIDE

        # Verify bet2 rules were converted correctly
        assert len(strategy.bet2_rules) == 1
        assert strategy.bet2_rules[0].condition == "has_pair"
        assert strategy.bet2_rules[0].action == Decision.PULL

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

    def test_create_martingale_betting_verifies_parameter_passthrough(self) -> None:
        """Test that martingale parameters are correctly passed through.

        Verifies that config parameters are applied to the created instance.
        Uses non-default values to ensure parameters are actually used.
        """
        config = _create_bankroll_config(
            "martingale",
            martingale=MartingaleBettingConfig(
                loss_multiplier=2.5,  # Non-default value
                max_bet=150.0,
                max_progressions=7,
            ),
        )
        system = create_betting_system(config)
        assert isinstance(system, MartingaleBetting)
        # Verify parameters were correctly applied
        assert system._base_bet == 5.0  # From base_bet in _create_bankroll_config
        assert system._loss_multiplier == 2.5
        assert system._max_bet == 150.0
        assert system._max_progressions == 7

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


def _create_full_config(
    main_paytable_type: str = "standard",
    bonus_enabled: bool = False,
    bonus_paytable_type: str = "paytable_b",
) -> FullConfig:
    """Create a FullConfig for testing paytable factories.

    Args:
        main_paytable_type: Type of main game paytable.
        bonus_enabled: Whether bonus betting is enabled.
        bonus_paytable_type: Type of bonus paytable.

    Returns:
        A FullConfig instance.
    """
    return FullConfig(
        paytables=PaytablesConfig(
            main_game=MainGamePaytableConfig(type=main_paytable_type),
            bonus=BonusPaytableConfig(type=bonus_paytable_type),
        ),
        bonus_strategy=BonusStrategyConfig(enabled=bonus_enabled),
    )


def _create_full_config_bypassing_validation(
    main_paytable_type: str = "standard",
    bonus_enabled: bool = False,
    bonus_paytable_type: str = "paytable_b",
) -> FullConfig:
    """Create a FullConfig bypassing Pydantic validation.

    This is used to test the factory function's own validation logic
    independent of Pydantic model validators.

    Args:
        main_paytable_type: Type of main game paytable (can be invalid).
        bonus_enabled: Whether bonus betting is enabled.
        bonus_paytable_type: Type of bonus paytable (can be invalid).

    Returns:
        A FullConfig with potentially invalid values.
    """
    # Create main paytable config bypassing validation
    main_game = MainGamePaytableConfig.__new__(MainGamePaytableConfig)
    object.__setattr__(main_game, "type", main_paytable_type)
    object.__setattr__(main_game, "custom", None)

    # Create bonus paytable config bypassing validation
    bonus = BonusPaytableConfig.__new__(BonusPaytableConfig)
    object.__setattr__(bonus, "type", bonus_paytable_type)
    object.__setattr__(bonus, "custom", None)
    object.__setattr__(bonus, "progressive", None)

    # Create paytables config
    paytables = PaytablesConfig.__new__(PaytablesConfig)
    object.__setattr__(paytables, "main_game", main_game)
    object.__setattr__(paytables, "bonus", bonus)

    # Create bonus strategy config
    bonus_strategy = BonusStrategyConfig.__new__(BonusStrategyConfig)
    object.__setattr__(bonus_strategy, "enabled", bonus_enabled)
    object.__setattr__(bonus_strategy, "paytable", bonus_paytable_type)
    object.__setattr__(bonus_strategy, "type", "never")

    # Create full config with real defaults for other sections
    config = FullConfig()
    # Bypass immutability to set our test values
    object.__setattr__(config, "paytables", paytables)
    object.__setattr__(config, "bonus_strategy", bonus_strategy)

    return config


class TestGetMainPaytable:
    """Tests for get_main_paytable() factory function."""

    def test_standard_paytable_returns_correct_type(self) -> None:
        """Test that standard paytable type returns a MainGamePaytable."""
        config = _create_full_config(main_paytable_type="standard")
        paytable = get_main_paytable(config)
        assert isinstance(paytable, MainGamePaytable)

    def test_standard_paytable_matches_expected_instance(self) -> None:
        """Test that standard paytable returns the same values as standard_main_paytable()."""
        config = _create_full_config(main_paytable_type="standard")
        paytable = get_main_paytable(config)
        expected = standard_main_paytable()
        # Verify name and payouts match
        assert paytable.name == expected.name
        assert paytable.payouts == expected.payouts

    def test_liberal_paytable_raises_not_implemented(self) -> None:
        """Test that liberal paytable type raises NotImplementedError."""
        config = _create_full_config_bypassing_validation(main_paytable_type="liberal")
        with pytest.raises(
            NotImplementedError,
            match="Main paytable type 'liberal' is not yet implemented",
        ):
            get_main_paytable(config)

    def test_tight_paytable_raises_not_implemented(self) -> None:
        """Test that tight paytable type raises NotImplementedError."""
        config = _create_full_config_bypassing_validation(main_paytable_type="tight")
        with pytest.raises(
            NotImplementedError,
            match="Main paytable type 'tight' is not yet implemented",
        ):
            get_main_paytable(config)

    def test_custom_paytable_raises_not_implemented(self) -> None:
        """Test that custom paytable type raises NotImplementedError."""
        config = _create_full_config_bypassing_validation(main_paytable_type="custom")
        with pytest.raises(
            NotImplementedError,
            match="Main paytable type 'custom' is not yet implemented",
        ):
            get_main_paytable(config)


class TestGetBonusPaytable:
    """Tests for get_bonus_paytable() factory function."""

    def test_bonus_disabled_returns_none(self) -> None:
        """Test that disabled bonus returns None."""
        config = _create_full_config(bonus_enabled=False)
        paytable = get_bonus_paytable(config)
        assert paytable is None

    def test_paytable_a_returns_correct_type(self) -> None:
        """Test that paytable_a returns a BonusPaytable."""
        config = _create_full_config(
            bonus_enabled=True, bonus_paytable_type="paytable_a"
        )
        paytable = get_bonus_paytable(config)
        assert isinstance(paytable, BonusPaytable)

    def test_paytable_a_matches_expected_instance(self) -> None:
        """Test that paytable_a returns the same values as bonus_paytable_a()."""
        config = _create_full_config(
            bonus_enabled=True, bonus_paytable_type="paytable_a"
        )
        paytable = get_bonus_paytable(config)
        expected = bonus_paytable_a()
        assert paytable is not None
        assert paytable.name == expected.name
        assert paytable.payouts == expected.payouts

    def test_paytable_b_returns_correct_type(self) -> None:
        """Test that paytable_b returns a BonusPaytable."""
        config = _create_full_config(
            bonus_enabled=True, bonus_paytable_type="paytable_b"
        )
        paytable = get_bonus_paytable(config)
        assert isinstance(paytable, BonusPaytable)

    def test_paytable_b_matches_expected_instance(self) -> None:
        """Test that paytable_b returns the same values as bonus_paytable_b()."""
        config = _create_full_config(
            bonus_enabled=True, bonus_paytable_type="paytable_b"
        )
        paytable = get_bonus_paytable(config)
        expected = bonus_paytable_b()
        assert paytable is not None
        assert paytable.name == expected.name
        assert paytable.payouts == expected.payouts

    def test_paytable_c_returns_correct_type(self) -> None:
        """Test that paytable_c returns a BonusPaytable."""
        config = _create_full_config(
            bonus_enabled=True, bonus_paytable_type="paytable_c"
        )
        paytable = get_bonus_paytable(config)
        assert isinstance(paytable, BonusPaytable)

    def test_paytable_c_matches_expected_instance(self) -> None:
        """Test that paytable_c returns the same values as bonus_paytable_c()."""
        config = _create_full_config(
            bonus_enabled=True, bonus_paytable_type="paytable_c"
        )
        paytable = get_bonus_paytable(config)
        expected = bonus_paytable_c()
        assert paytable is not None
        assert paytable.name == expected.name
        assert paytable.payouts == expected.payouts

    def test_unknown_paytable_type_raises_value_error(self) -> None:
        """Test that unknown bonus paytable type raises ValueError."""
        config = _create_full_config_bypassing_validation(
            bonus_enabled=True, bonus_paytable_type="unknown_paytable"
        )
        with pytest.raises(
            ValueError,
            match="Unknown bonus paytable type: 'unknown_paytable'",
        ):
            get_bonus_paytable(config)

    def test_custom_paytable_type_raises_value_error(self) -> None:
        """Test that custom bonus paytable type raises ValueError.

        Custom paytables are defined in the config schema but not yet
        implemented in the factory function.
        """
        config = _create_full_config_bypassing_validation(
            bonus_enabled=True, bonus_paytable_type="custom"
        )
        with pytest.raises(
            ValueError,
            match="Unknown bonus paytable type: 'custom'",
        ):
            get_bonus_paytable(config)
