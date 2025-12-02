"""Unit tests for configuration Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from let_it_ride.config.models import (
    AggressiveStrategyConfig,
    BankrollConfig,
    BettingSystemConfig,
    BonusLimitsConfig,
    BonusStrategyConfig,
    ConservativeStrategyConfig,
    CustomBettingConfig,
    CustomBonusStrategyConfig,
    CustomStrategyConfig,
    DAlembertBettingConfig,
    DeckConfig,
    FullConfig,
    MartingaleBettingConfig,
    MetadataConfig,
    OutputConfig,
    PaytablesConfig,
    ProfitTier,
    ProportionalBettingConfig,
    SimulationConfig,
    StaticBonusConfig,
    StopConditionsConfig,
    StrategyConfig,
)


class TestMetadataConfig:
    """Tests for MetadataConfig model."""

    def test_default_values(self) -> None:
        """Test that all defaults are None."""
        config = MetadataConfig()
        assert config.name is None
        assert config.description is None
        assert config.version is None
        assert config.author is None
        assert config.created is None

    def test_all_fields_set(self) -> None:
        """Test setting all metadata fields."""
        config = MetadataConfig(
            name="Test Config",
            description="A test configuration",
            version="1.0",
            author="Test Author",
            created="2024-01-15",
        )
        assert config.name == "Test Config"
        assert config.description == "A test configuration"
        assert config.version == "1.0"
        assert config.author == "Test Author"
        assert config.created == "2024-01-15"

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields raise an error."""
        with pytest.raises(ValidationError) as exc_info:
            MetadataConfig(unknown_field="value")  # type: ignore[call-arg]
        assert "extra_forbidden" in str(exc_info.value)


class TestSimulationConfig:
    """Tests for SimulationConfig model."""

    def test_default_values(self) -> None:
        """Test default simulation config values."""
        config = SimulationConfig()
        assert config.num_sessions == 10000
        assert config.hands_per_session == 200
        assert config.random_seed is None
        assert config.workers == "auto"
        assert config.progress_interval == 10000
        assert config.detailed_logging is False

    def test_valid_values(self) -> None:
        """Test valid simulation config values."""
        config = SimulationConfig(
            num_sessions=1_000_000,
            hands_per_session=500,
            random_seed=42,
            workers=4,
            progress_interval=1000,
            detailed_logging=True,
        )
        assert config.num_sessions == 1_000_000
        assert config.hands_per_session == 500
        assert config.random_seed == 42
        assert config.workers == 4
        assert config.progress_interval == 1000
        assert config.detailed_logging is True

    def test_num_sessions_min(self) -> None:
        """Test num_sessions minimum value."""
        config = SimulationConfig(num_sessions=1)
        assert config.num_sessions == 1

    def test_num_sessions_max(self) -> None:
        """Test num_sessions maximum value."""
        config = SimulationConfig(num_sessions=100_000_000)
        assert config.num_sessions == 100_000_000

    def test_num_sessions_below_min(self) -> None:
        """Test num_sessions below minimum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(num_sessions=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_num_sessions_above_max(self) -> None:
        """Test num_sessions above maximum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(num_sessions=100_000_001)
        assert "less than or equal to 100000000" in str(exc_info.value)

    def test_hands_per_session_below_min(self) -> None:
        """Test hands_per_session below minimum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(hands_per_session=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_hands_per_session_above_max(self) -> None:
        """Test hands_per_session above maximum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(hands_per_session=10_001)
        assert "less than or equal to 10000" in str(exc_info.value)

    def test_workers_auto(self) -> None:
        """Test workers with 'auto' value."""
        config = SimulationConfig(workers="auto")
        assert config.workers == "auto"

    def test_workers_positive_int(self) -> None:
        """Test workers with positive integer."""
        config = SimulationConfig(workers=8)
        assert config.workers == 8

    def test_workers_zero_invalid(self) -> None:
        """Test workers with zero raises error."""
        with pytest.raises(ValidationError):
            SimulationConfig(workers=0)

    def test_workers_negative_invalid(self) -> None:
        """Test workers with negative value raises error."""
        with pytest.raises(ValidationError):
            SimulationConfig(workers=-1)


class TestDeckConfig:
    """Tests for DeckConfig model."""

    def test_default_value(self) -> None:
        """Test default shuffle algorithm."""
        config = DeckConfig()
        assert config.shuffle_algorithm == "fisher_yates"

    def test_fisher_yates(self) -> None:
        """Test fisher_yates shuffle algorithm."""
        config = DeckConfig(shuffle_algorithm="fisher_yates")
        assert config.shuffle_algorithm == "fisher_yates"

    def test_cryptographic(self) -> None:
        """Test cryptographic shuffle algorithm."""
        config = DeckConfig(shuffle_algorithm="cryptographic")
        assert config.shuffle_algorithm == "cryptographic"

    def test_invalid_algorithm(self) -> None:
        """Test invalid shuffle algorithm raises error."""
        with pytest.raises(ValidationError):
            DeckConfig(shuffle_algorithm="invalid")  # type: ignore[arg-type]


class TestStopConditionsConfig:
    """Tests for StopConditionsConfig model."""

    def test_default_values(self) -> None:
        """Test default stop conditions."""
        config = StopConditionsConfig()
        assert config.win_limit is None
        assert config.loss_limit is None
        assert config.max_hands is None
        assert config.max_duration_minutes is None
        assert config.stop_on_insufficient_funds is True

    def test_all_conditions_set(self) -> None:
        """Test all stop conditions set."""
        config = StopConditionsConfig(
            win_limit=250.0,
            loss_limit=200.0,
            max_hands=500,
            max_duration_minutes=60,
            stop_on_insufficient_funds=False,
        )
        assert config.win_limit == 250.0
        assert config.loss_limit == 200.0
        assert config.max_hands == 500
        assert config.max_duration_minutes == 60
        assert config.stop_on_insufficient_funds is False

    def test_win_limit_must_be_positive(self) -> None:
        """Test win_limit must be positive."""
        with pytest.raises(ValidationError):
            StopConditionsConfig(win_limit=-100.0)

        with pytest.raises(ValidationError):
            StopConditionsConfig(win_limit=0.0)

    def test_loss_limit_must_be_positive(self) -> None:
        """Test loss_limit must be positive."""
        with pytest.raises(ValidationError):
            StopConditionsConfig(loss_limit=-100.0)

    def test_max_hands_must_be_positive(self) -> None:
        """Test max_hands must be positive."""
        with pytest.raises(ValidationError):
            StopConditionsConfig(max_hands=0)


class TestBettingSystemConfig:
    """Tests for BettingSystemConfig model."""

    def test_default_flat(self) -> None:
        """Test default betting system is flat."""
        config = BettingSystemConfig()
        assert config.type == "flat"

    def test_proportional_config(self) -> None:
        """Test proportional betting configuration."""
        config = BettingSystemConfig(
            type="proportional",
            proportional=ProportionalBettingConfig(bankroll_percentage=0.05),
        )
        assert config.type == "proportional"
        assert config.proportional is not None
        assert config.proportional.bankroll_percentage == 0.05

    def test_martingale_config(self) -> None:
        """Test Martingale betting configuration."""
        config = BettingSystemConfig(
            type="martingale",
            martingale=MartingaleBettingConfig(loss_multiplier=2.5, max_bet=1000.0),
        )
        assert config.type == "martingale"
        assert config.martingale is not None
        assert config.martingale.loss_multiplier == 2.5
        assert config.martingale.max_bet == 1000.0


class TestProportionalBettingConfig:
    """Tests for ProportionalBettingConfig model."""

    def test_default_values(self) -> None:
        """Test default proportional betting values."""
        config = ProportionalBettingConfig()
        assert config.bankroll_percentage == 0.03
        assert config.min_bet == 5.0
        assert config.max_bet == 100.0
        assert config.round_to == 1.0

    def test_bankroll_percentage_min(self) -> None:
        """Test bankroll_percentage minimum value."""
        config = ProportionalBettingConfig(bankroll_percentage=0.001)
        assert config.bankroll_percentage == 0.001

    def test_bankroll_percentage_max(self) -> None:
        """Test bankroll_percentage maximum value."""
        config = ProportionalBettingConfig(bankroll_percentage=0.50)
        assert config.bankroll_percentage == 0.50

    def test_bankroll_percentage_below_min(self) -> None:
        """Test bankroll_percentage below minimum raises error."""
        with pytest.raises(ValidationError):
            ProportionalBettingConfig(bankroll_percentage=0.0001)

    def test_bankroll_percentage_above_max(self) -> None:
        """Test bankroll_percentage above maximum raises error."""
        with pytest.raises(ValidationError):
            ProportionalBettingConfig(bankroll_percentage=0.51)


class TestBankrollConfig:
    """Tests for BankrollConfig model."""

    def test_default_values(self) -> None:
        """Test default bankroll values."""
        config = BankrollConfig()
        assert config.starting_amount == 500.0
        assert config.base_bet == 5.0
        assert config.stop_conditions is not None
        assert config.betting_system is not None

    def test_valid_values(self) -> None:
        """Test valid bankroll values."""
        config = BankrollConfig(
            starting_amount=1000.0,
            base_bet=10.0,
        )
        assert config.starting_amount == 1000.0
        assert config.base_bet == 10.0

    def test_starting_amount_must_be_positive(self) -> None:
        """Test starting_amount must be positive."""
        with pytest.raises(ValidationError):
            BankrollConfig(starting_amount=0)

        with pytest.raises(ValidationError):
            BankrollConfig(starting_amount=-100)

    def test_base_bet_must_be_positive(self) -> None:
        """Test base_bet must be positive."""
        with pytest.raises(ValidationError):
            BankrollConfig(base_bet=0)

    def test_starting_amount_must_cover_initial_wager(self) -> None:
        """Test starting_amount must be at least 3x base_bet."""
        # This should fail: 10 < 3 * 5 = 15
        with pytest.raises(ValidationError) as exc_info:
            BankrollConfig(starting_amount=10.0, base_bet=5.0)
        assert "3x base_bet" in str(exc_info.value)

    def test_exactly_3x_base_bet_valid(self) -> None:
        """Test starting_amount equal to 3x base_bet is valid."""
        config = BankrollConfig(starting_amount=15.0, base_bet=5.0)
        assert config.starting_amount == 15.0
        assert config.base_bet == 5.0


class TestStrategyConfig:
    """Tests for StrategyConfig model."""

    def test_default_basic(self) -> None:
        """Test default strategy is basic."""
        config = StrategyConfig()
        assert config.type == "basic"

    def test_all_strategy_types(self) -> None:
        """Test all valid strategy types with required configs."""
        # Types that don't require config sections
        for strategy_type in ["basic", "always_ride", "always_pull"]:
            config = StrategyConfig(type=strategy_type)  # type: ignore[arg-type]
            assert config.type == strategy_type

        # Types that require config sections - tested with valid configs
        config = StrategyConfig(
            type="conservative",
            conservative=ConservativeStrategyConfig(),
        )
        assert config.type == "conservative"

        config = StrategyConfig(
            type="aggressive",
            aggressive=AggressiveStrategyConfig(),
        )
        assert config.type == "aggressive"

        config = StrategyConfig(
            type="custom",
            custom=CustomStrategyConfig(),
        )
        assert config.type == "custom"

    def test_invalid_strategy_type(self) -> None:
        """Test invalid strategy type raises error."""
        with pytest.raises(ValidationError):
            StrategyConfig(type="invalid")  # type: ignore[arg-type]

    def test_conservative_config(self) -> None:
        """Test conservative strategy configuration."""
        config = StrategyConfig(
            type="conservative",
            conservative=ConservativeStrategyConfig(
                made_hands_only=True,
                min_strength_bet1=8,
            ),
        )
        assert config.type == "conservative"
        assert config.conservative is not None
        assert config.conservative.min_strength_bet1 == 8

    def test_aggressive_config(self) -> None:
        """Test aggressive strategy configuration."""
        config = StrategyConfig(
            type="aggressive",
            aggressive=AggressiveStrategyConfig(
                ride_on_draws=True,
                include_gutshots=False,
            ),
        )
        assert config.type == "aggressive"
        assert config.aggressive is not None
        assert config.aggressive.include_gutshots is False

    def test_conservative_type_without_config_raises_error(self) -> None:
        """Test conservative type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyConfig(type="conservative")
        assert "requires 'conservative' config section" in str(exc_info.value)

    def test_aggressive_type_without_config_raises_error(self) -> None:
        """Test aggressive type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyConfig(type="aggressive")
        assert "requires 'aggressive' config section" in str(exc_info.value)

    def test_custom_type_without_config_raises_error(self) -> None:
        """Test custom type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyConfig(type="custom")
        assert "requires 'custom' config section" in str(exc_info.value)

    def test_basic_type_without_config_is_valid(self) -> None:
        """Test basic type works without config section."""
        config = StrategyConfig(type="basic")
        assert config.type == "basic"

    def test_always_ride_without_config_is_valid(self) -> None:
        """Test always_ride type works without config section."""
        config = StrategyConfig(type="always_ride")
        assert config.type == "always_ride"

    def test_always_pull_without_config_is_valid(self) -> None:
        """Test always_pull type works without config section."""
        config = StrategyConfig(type="always_pull")
        assert config.type == "always_pull"


class TestConservativeStrategyConfig:
    """Tests for ConservativeStrategyConfig model."""

    def test_default_values(self) -> None:
        """Test default conservative strategy values."""
        config = ConservativeStrategyConfig()
        assert config.made_hands_only is True
        assert config.min_strength_bet1 == 7
        assert config.min_strength_bet2 == 5

    def test_min_strength_range(self) -> None:
        """Test min_strength values must be in range 1-10."""
        config = ConservativeStrategyConfig(min_strength_bet1=1, min_strength_bet2=10)
        assert config.min_strength_bet1 == 1
        assert config.min_strength_bet2 == 10

    def test_min_strength_below_range(self) -> None:
        """Test min_strength below 1 raises error."""
        with pytest.raises(ValidationError):
            ConservativeStrategyConfig(min_strength_bet1=0)

    def test_min_strength_above_range(self) -> None:
        """Test min_strength above 10 raises error."""
        with pytest.raises(ValidationError):
            ConservativeStrategyConfig(min_strength_bet1=11)


class TestBonusStrategyConfig:
    """Tests for BonusStrategyConfig model."""

    def test_default_values(self) -> None:
        """Test default bonus strategy values."""
        config = BonusStrategyConfig()
        assert config.enabled is False
        assert config.paytable == "paytable_b"
        assert config.type == "never"

    def test_enabled_static(self) -> None:
        """Test enabled bonus with static strategy."""
        config = BonusStrategyConfig(
            enabled=True,
            type="static",
            static=StaticBonusConfig(amount=2.0),
        )
        assert config.enabled is True
        assert config.type == "static"
        assert config.static is not None
        assert config.static.amount == 2.0

    def test_all_paytable_types(self) -> None:
        """Test all valid paytable types."""
        for paytable in ["paytable_a", "paytable_b", "paytable_c", "custom"]:
            config = BonusStrategyConfig(paytable=paytable)  # type: ignore[arg-type]
            assert config.paytable == paytable

    def test_always_type_without_config_raises_error(self) -> None:
        """Test always type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BonusStrategyConfig(type="always")
        assert "requires 'always' config section" in str(exc_info.value)

    def test_static_type_without_config_raises_error(self) -> None:
        """Test static type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BonusStrategyConfig(type="static")
        assert "requires 'static' config section" in str(exc_info.value)

    def test_bankroll_conditional_type_without_config_raises_error(self) -> None:
        """Test bankroll_conditional type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BonusStrategyConfig(type="bankroll_conditional")
        assert "requires 'bankroll_conditional' config section" in str(exc_info.value)

    def test_streak_based_type_without_config_raises_error(self) -> None:
        """Test streak_based type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BonusStrategyConfig(type="streak_based")
        assert "requires 'streak_based' config section" in str(exc_info.value)

    def test_session_conditional_type_without_config_raises_error(self) -> None:
        """Test session_conditional type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BonusStrategyConfig(type="session_conditional")
        assert "requires 'session_conditional' config section" in str(exc_info.value)

    def test_combined_type_without_config_raises_error(self) -> None:
        """Test combined type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BonusStrategyConfig(type="combined")
        assert "requires 'combined' config section" in str(exc_info.value)

    def test_custom_type_without_config_raises_error(self) -> None:
        """Test custom type without config section raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BonusStrategyConfig(type="custom")
        assert "requires 'custom' config section" in str(exc_info.value)

    def test_never_type_without_config_is_valid(self) -> None:
        """Test never type works without config section."""
        config = BonusStrategyConfig(type="never")
        assert config.type == "never"


class TestStaticBonusConfig:
    """Tests for StaticBonusConfig model."""

    def test_default_amount(self) -> None:
        """Test default static bonus with amount."""
        config = StaticBonusConfig()
        assert config.amount == 1.0
        assert config.ratio is None

    def test_amount_only(self) -> None:
        """Test static bonus with amount only."""
        config = StaticBonusConfig(amount=5.0, ratio=None)
        assert config.amount == 5.0
        assert config.ratio is None

    def test_ratio_only(self) -> None:
        """Test static bonus with ratio only."""
        config = StaticBonusConfig(amount=None, ratio=0.2)
        assert config.amount is None
        assert config.ratio == 0.2

    def test_both_amount_and_ratio_invalid(self) -> None:
        """Test that specifying both amount and ratio raises error."""
        with pytest.raises(ValidationError) as exc_info:
            StaticBonusConfig(amount=5.0, ratio=0.2)
        assert "amount or ratio" in str(exc_info.value)

    def test_neither_amount_nor_ratio_invalid(self) -> None:
        """Test that specifying neither amount nor ratio raises error."""
        with pytest.raises(ValidationError) as exc_info:
            StaticBonusConfig(amount=None, ratio=None)
        assert "amount or ratio" in str(exc_info.value)


class TestBonusLimitsConfig:
    """Tests for BonusLimitsConfig model."""

    def test_default_values(self) -> None:
        """Test default bonus limits."""
        config = BonusLimitsConfig()
        assert config.min_bet == 1.0
        assert config.max_bet == 25.0
        assert config.increment == 1.0

    def test_min_bet_can_be_zero(self) -> None:
        """Test min_bet can be zero."""
        config = BonusLimitsConfig(min_bet=0.0)
        assert config.min_bet == 0.0

    def test_max_bet_must_be_positive(self) -> None:
        """Test max_bet must be positive."""
        with pytest.raises(ValidationError):
            BonusLimitsConfig(max_bet=0.0)


class TestPaytablesConfig:
    """Tests for PaytablesConfig model."""

    def test_default_values(self) -> None:
        """Test default paytables configuration."""
        config = PaytablesConfig()
        assert config.main_game.type == "standard"
        assert config.bonus.type == "paytable_b"


class TestOutputConfig:
    """Tests for OutputConfig model."""

    def test_default_values(self) -> None:
        """Test default output configuration."""
        config = OutputConfig()
        assert config.directory == "./results"
        assert config.prefix == "simulation"
        assert config.formats.csv.enabled is True
        assert config.formats.json_output.enabled is True
        assert config.formats.html.enabled is False
        assert config.console.progress_bar is True

    def test_verbosity_range(self) -> None:
        """Test verbosity values in range 0-3."""
        for level in [0, 1, 2, 3]:
            config = OutputConfig(console={"verbosity": level})
            assert config.console.verbosity == level

    def test_verbosity_above_range(self) -> None:
        """Test verbosity above 3 raises error."""
        with pytest.raises(ValidationError):
            OutputConfig(console={"verbosity": 4})  # type: ignore[arg-type]


class TestFullConfig:
    """Tests for FullConfig root model."""

    def test_default_config(self) -> None:
        """Test that default config has all required sections."""
        config = FullConfig()
        assert config.metadata is not None
        assert config.simulation is not None
        assert config.deck is not None
        assert config.bankroll is not None
        assert config.strategy is not None
        assert config.bonus_strategy is not None
        assert config.paytables is not None
        assert config.output is not None

    def test_partial_config(self) -> None:
        """Test creating config with only some sections."""
        config = FullConfig(
            simulation=SimulationConfig(num_sessions=1000),
            bankroll=BankrollConfig(starting_amount=1000.0, base_bet=10.0),
        )
        assert config.simulation.num_sessions == 1000
        assert config.bankroll.starting_amount == 1000.0
        # Other sections should have defaults
        assert config.strategy.type == "basic"
        assert config.deck.shuffle_algorithm == "fisher_yates"

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields at root level raise error."""
        with pytest.raises(ValidationError) as exc_info:
            FullConfig(unknown_section={"key": "value"})  # type: ignore[call-arg]
        assert "extra_forbidden" in str(exc_info.value)

    def test_nested_extra_fields_forbidden(self) -> None:
        """Test that extra fields in nested sections raise error."""
        with pytest.raises(ValidationError):
            FullConfig(simulation={"num_sessions": 1000, "unknown_field": "value"})

    def test_full_valid_config(self) -> None:
        """Test a comprehensive valid configuration."""
        config = FullConfig(
            metadata=MetadataConfig(
                name="Full Test Config",
                description="Testing all configuration options",
                version="1.0",
            ),
            simulation=SimulationConfig(
                num_sessions=100_000,
                hands_per_session=200,
                random_seed=42,
                workers=4,
            ),
            deck=DeckConfig(shuffle_algorithm="fisher_yates"),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=250.0,
                    loss_limit=200.0,
                    max_hands=200,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="static",
                static=StaticBonusConfig(amount=1.0),
            ),
            paytables=PaytablesConfig(),
            output=OutputConfig(
                directory="./results",
                prefix="test",
            ),
        )

        # Verify key values
        assert config.metadata.name == "Full Test Config"
        assert config.simulation.num_sessions == 100_000
        assert config.simulation.random_seed == 42
        assert config.bankroll.stop_conditions.win_limit == 250.0
        assert config.bonus_strategy.enabled is True
        assert config.output.prefix == "test"


class TestMinMaxBetValidation:
    """Tests for min_bet/max_bet cross-field validation."""

    def test_proportional_betting_min_bet_exceeds_max_bet(self) -> None:
        """Test ProportionalBettingConfig rejects min_bet > max_bet."""
        with pytest.raises(ValidationError) as exc_info:
            ProportionalBettingConfig(min_bet=100.0, max_bet=50.0)
        assert "min_bet cannot exceed max_bet" in str(exc_info.value)

    def test_proportional_betting_valid_min_max(self) -> None:
        """Test ProportionalBettingConfig accepts valid min_bet <= max_bet."""
        config = ProportionalBettingConfig(min_bet=10.0, max_bet=100.0)
        assert config.min_bet == 10.0
        assert config.max_bet == 100.0

    def test_proportional_betting_equal_min_max(self) -> None:
        """Test ProportionalBettingConfig accepts min_bet == max_bet."""
        config = ProportionalBettingConfig(min_bet=50.0, max_bet=50.0)
        assert config.min_bet == config.max_bet

    def test_dalembert_betting_min_bet_exceeds_max_bet(self) -> None:
        """Test DAlembertBettingConfig rejects min_bet > max_bet."""
        with pytest.raises(ValidationError) as exc_info:
            DAlembertBettingConfig(min_bet=600.0, max_bet=500.0)
        assert "min_bet cannot exceed max_bet" in str(exc_info.value)

    def test_dalembert_betting_valid_min_max(self) -> None:
        """Test DAlembertBettingConfig accepts valid min_bet <= max_bet."""
        config = DAlembertBettingConfig(min_bet=5.0, max_bet=500.0)
        assert config.min_bet == 5.0
        assert config.max_bet == 500.0

    def test_custom_betting_min_bet_exceeds_max_bet(self) -> None:
        """Test CustomBettingConfig rejects min_bet > max_bet."""
        with pytest.raises(ValidationError) as exc_info:
            CustomBettingConfig(min_bet=100.0, max_bet=50.0)
        assert "min_bet cannot exceed max_bet" in str(exc_info.value)

    def test_custom_betting_valid_min_max(self) -> None:
        """Test CustomBettingConfig accepts valid min_bet <= max_bet."""
        config = CustomBettingConfig(min_bet=5.0, max_bet=500.0)
        assert config.min_bet == 5.0
        assert config.max_bet == 500.0

    def test_bonus_limits_min_bet_exceeds_max_bet(self) -> None:
        """Test BonusLimitsConfig rejects min_bet > max_bet."""
        with pytest.raises(ValidationError) as exc_info:
            BonusLimitsConfig(min_bet=30.0, max_bet=25.0)
        assert "min_bet cannot exceed max_bet" in str(exc_info.value)

    def test_bonus_limits_valid_min_max(self) -> None:
        """Test BonusLimitsConfig accepts valid min_bet <= max_bet."""
        config = BonusLimitsConfig(min_bet=1.0, max_bet=25.0)
        assert config.min_bet == 1.0
        assert config.max_bet == 25.0

    def test_custom_bonus_strategy_min_bet_exceeds_max_bet(self) -> None:
        """Test CustomBonusStrategyConfig rejects min_bet > max_bet."""
        with pytest.raises(ValidationError) as exc_info:
            CustomBonusStrategyConfig(min_bet=30.0, max_bet=25.0)
        assert "min_bet cannot exceed max_bet" in str(exc_info.value)

    def test_custom_bonus_strategy_valid_min_max(self) -> None:
        """Test CustomBonusStrategyConfig accepts valid min_bet <= max_bet."""
        config = CustomBonusStrategyConfig(min_bet=0.0, max_bet=25.0)
        assert config.min_bet == 0.0
        assert config.max_bet == 25.0


class TestBettingSystemTypeConfigMatch:
    """Tests for BettingSystemConfig type-config match validation."""

    def test_flat_type_no_config_required(self) -> None:
        """Test flat betting type doesn't require additional config."""
        config = BettingSystemConfig(type="flat")
        assert config.type == "flat"

    def test_proportional_type_without_config_fails(self) -> None:
        """Test proportional type without config raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BettingSystemConfig(type="proportional")
        assert "'proportional' betting system requires 'proportional' config" in str(
            exc_info.value
        )

    def test_proportional_type_with_config_succeeds(self) -> None:
        """Test proportional type with config succeeds."""
        config = BettingSystemConfig(
            type="proportional", proportional=ProportionalBettingConfig()
        )
        assert config.type == "proportional"
        assert config.proportional is not None

    def test_martingale_type_without_config_fails(self) -> None:
        """Test martingale type without config raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BettingSystemConfig(type="martingale")
        assert "'martingale' betting system requires 'martingale' config" in str(
            exc_info.value
        )

    def test_martingale_type_with_config_succeeds(self) -> None:
        """Test martingale type with config succeeds."""
        config = BettingSystemConfig(
            type="martingale", martingale=MartingaleBettingConfig()
        )
        assert config.type == "martingale"
        assert config.martingale is not None

    def test_dalembert_type_without_config_fails(self) -> None:
        """Test dalembert type without config raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BettingSystemConfig(type="dalembert")
        assert "'dalembert' betting system requires 'dalembert' config" in str(
            exc_info.value
        )

    def test_custom_type_without_config_fails(self) -> None:
        """Test custom type without config raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BettingSystemConfig(type="custom")
        assert "'custom' betting system requires 'custom' config" in str(exc_info.value)

    def test_custom_type_with_config_succeeds(self) -> None:
        """Test custom type with config succeeds."""
        config = BettingSystemConfig(type="custom", custom=CustomBettingConfig())
        assert config.type == "custom"
        assert config.custom is not None


class TestProfitTierValidation:
    """Tests for ProfitTier tier range validation."""

    def test_valid_tier_range(self) -> None:
        """Test valid profit tier with min_profit < max_profit."""
        tier = ProfitTier(min_profit=0.0, max_profit=100.0, bet_amount=5.0)
        assert tier.min_profit == 0.0
        assert tier.max_profit == 100.0

    def test_no_max_profit_valid(self) -> None:
        """Test tier with no max_profit is valid."""
        tier = ProfitTier(min_profit=100.0, max_profit=None, bet_amount=10.0)
        assert tier.min_profit == 100.0
        assert tier.max_profit is None

    def test_min_profit_equals_max_profit_invalid(self) -> None:
        """Test tier with min_profit == max_profit raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ProfitTier(min_profit=50.0, max_profit=50.0, bet_amount=5.0)
        assert "min_profit must be less than max_profit" in str(exc_info.value)

    def test_min_profit_exceeds_max_profit_invalid(self) -> None:
        """Test tier with min_profit > max_profit raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ProfitTier(min_profit=100.0, max_profit=50.0, bet_amount=5.0)
        assert "min_profit must be less than max_profit" in str(exc_info.value)

    def test_negative_min_profit_valid(self) -> None:
        """Test tier with negative min_profit is valid."""
        tier = ProfitTier(min_profit=-100.0, max_profit=0.0, bet_amount=1.0)
        assert tier.min_profit == -100.0
        assert tier.max_profit == 0.0
