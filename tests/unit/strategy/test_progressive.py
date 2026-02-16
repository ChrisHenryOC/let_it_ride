"""Unit tests for progressive jackpot side bet strategy implementations.

This module tests all progressive strategy implementations:
- NeverProgressiveStrategy: Always returns 0
- AlwaysProgressiveStrategy: Always returns the bet amount
- JackpotThresholdStrategy: Only bets when jackpot exceeds threshold
- BankrollConditionalProgressiveStrategy: Conditional based on profit/bankroll
"""

import pytest

from let_it_ride.config.models import (
    BankrollConditionalProgressiveConfig,
    JackpotThresholdConfig,
    ProgressiveStrategyConfig,
)
from let_it_ride.strategy import (
    AlwaysProgressiveStrategy,
    BankrollConditionalProgressiveStrategy,
    JackpotThresholdStrategy,
    NeverProgressiveStrategy,
    ProgressiveContext,
    ProgressiveStrategy,
    create_progressive_strategy,
)


@pytest.fixture
def default_context() -> ProgressiveContext:
    """Create a default ProgressiveContext for testing."""
    return ProgressiveContext(
        bankroll=1000.0,
        starting_bankroll=1000.0,
        session_profit=0.0,
        hands_played=0,
        main_streak=0,
        base_bet=10.0,
        current_jackpot=10000.0,
        seed_amount=10000.0,
        progressive_bet_amount=1.0,
    )


@pytest.fixture
def high_jackpot_context() -> ProgressiveContext:
    """Create a ProgressiveContext with a large jackpot."""
    return ProgressiveContext(
        bankroll=1000.0,
        starting_bankroll=1000.0,
        session_profit=0.0,
        hands_played=50,
        main_streak=0,
        base_bet=10.0,
        current_jackpot=50000.0,
        seed_amount=10000.0,
        progressive_bet_amount=1.0,
    )


@pytest.fixture
def profitable_context() -> ProgressiveContext:
    """Create a ProgressiveContext with positive session profit."""
    return ProgressiveContext(
        bankroll=1200.0,
        starting_bankroll=1000.0,
        session_profit=200.0,
        hands_played=50,
        main_streak=3,
        base_bet=10.0,
        current_jackpot=15000.0,
        seed_amount=10000.0,
        progressive_bet_amount=1.0,
    )


@pytest.fixture
def losing_context() -> ProgressiveContext:
    """Create a ProgressiveContext with negative session profit."""
    return ProgressiveContext(
        bankroll=700.0,
        starting_bankroll=1000.0,
        session_profit=-300.0,
        hands_played=100,
        main_streak=-5,
        base_bet=10.0,
        current_jackpot=12000.0,
        seed_amount=10000.0,
        progressive_bet_amount=1.0,
    )


# ---- ProgressiveContext Tests ----


class TestProgressiveContext:
    """Tests for ProgressiveContext dataclass."""

    def test_context_creation(self, default_context: ProgressiveContext) -> None:
        """Test basic context creation."""
        assert default_context.bankroll == 1000.0
        assert default_context.current_jackpot == 10000.0
        assert default_context.progressive_bet_amount == 1.0

    def test_context_is_frozen(self, default_context: ProgressiveContext) -> None:
        """Test context is immutable."""
        with pytest.raises(AttributeError):
            default_context.bankroll = 2000.0  # type: ignore[misc]


# ---- NeverProgressiveStrategy Tests ----


class TestNeverProgressiveStrategy:
    """Tests for NeverProgressiveStrategy."""

    def test_always_returns_zero(self, default_context: ProgressiveContext) -> None:
        strategy = NeverProgressiveStrategy()
        assert strategy.get_progressive_bet(default_context) == 0.0

    def test_returns_zero_with_high_jackpot(
        self, high_jackpot_context: ProgressiveContext
    ) -> None:
        strategy = NeverProgressiveStrategy()
        assert strategy.get_progressive_bet(high_jackpot_context) == 0.0

    def test_satisfies_protocol(self) -> None:
        strategy: ProgressiveStrategy = NeverProgressiveStrategy()
        assert hasattr(strategy, "get_progressive_bet")


# ---- AlwaysProgressiveStrategy Tests ----


class TestAlwaysProgressiveStrategy:
    """Tests for AlwaysProgressiveStrategy."""

    def test_returns_bet_amount(self, default_context: ProgressiveContext) -> None:
        strategy = AlwaysProgressiveStrategy()
        assert strategy.get_progressive_bet(default_context) == 1.0

    def test_returns_bet_amount_from_context(self) -> None:
        context = ProgressiveContext(
            bankroll=500.0,
            starting_bankroll=1000.0,
            session_profit=-500.0,
            hands_played=100,
            main_streak=-10,
            base_bet=5.0,
            current_jackpot=5000.0,
            seed_amount=10000.0,
            progressive_bet_amount=2.0,
        )
        strategy = AlwaysProgressiveStrategy()
        assert strategy.get_progressive_bet(context) == 2.0

    def test_satisfies_protocol(self) -> None:
        strategy: ProgressiveStrategy = AlwaysProgressiveStrategy()
        assert hasattr(strategy, "get_progressive_bet")


# ---- JackpotThresholdStrategy Tests ----


class TestJackpotThresholdStrategy:
    """Tests for JackpotThresholdStrategy."""

    def test_bets_when_jackpot_above_threshold(
        self, high_jackpot_context: ProgressiveContext
    ) -> None:
        strategy = JackpotThresholdStrategy(min_jackpot=25000.0)
        assert strategy.get_progressive_bet(high_jackpot_context) == 1.0

    def test_no_bet_when_jackpot_below_threshold(
        self, default_context: ProgressiveContext
    ) -> None:
        strategy = JackpotThresholdStrategy(min_jackpot=25000.0)
        assert strategy.get_progressive_bet(default_context) == 0.0

    def test_bets_when_jackpot_equals_threshold(self) -> None:
        context = ProgressiveContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            base_bet=10.0,
            current_jackpot=25000.0,
            seed_amount=10000.0,
            progressive_bet_amount=1.0,
        )
        strategy = JackpotThresholdStrategy(min_jackpot=25000.0)
        assert strategy.get_progressive_bet(context) == 1.0

    def test_zero_threshold_always_bets(
        self, default_context: ProgressiveContext
    ) -> None:
        strategy = JackpotThresholdStrategy(min_jackpot=0.0)
        assert strategy.get_progressive_bet(default_context) == 1.0

    def test_negative_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="min_jackpot must be non-negative"):
            JackpotThresholdStrategy(min_jackpot=-1.0)

    def test_satisfies_protocol(self) -> None:
        strategy: ProgressiveStrategy = JackpotThresholdStrategy(min_jackpot=25000.0)
        assert hasattr(strategy, "get_progressive_bet")


# ---- BankrollConditionalProgressiveStrategy Tests ----


class TestBankrollConditionalProgressiveStrategy:
    """Tests for BankrollConditionalProgressiveStrategy."""

    def test_bets_when_profitable(self, profitable_context: ProgressiveContext) -> None:
        strategy = BankrollConditionalProgressiveStrategy(min_session_profit=50.0)
        assert strategy.get_progressive_bet(profitable_context) == 1.0

    def test_no_bet_when_unprofitable(self, losing_context: ProgressiveContext) -> None:
        strategy = BankrollConditionalProgressiveStrategy(min_session_profit=50.0)
        assert strategy.get_progressive_bet(losing_context) == 0.0

    def test_no_bet_when_profit_below_threshold(
        self, default_context: ProgressiveContext
    ) -> None:
        strategy = BankrollConditionalProgressiveStrategy(min_session_profit=50.0)
        assert strategy.get_progressive_bet(default_context) == 0.0

    def test_bets_when_bankroll_ratio_met(
        self, profitable_context: ProgressiveContext
    ) -> None:
        # profitable_context: bankroll=1200, starting=1000, ratio=1.2
        strategy = BankrollConditionalProgressiveStrategy(min_bankroll_ratio=1.1)
        assert strategy.get_progressive_bet(profitable_context) == 1.0

    def test_no_bet_when_bankroll_ratio_not_met(
        self, losing_context: ProgressiveContext
    ) -> None:
        # losing_context: bankroll=700, starting=1000, ratio=0.7
        strategy = BankrollConditionalProgressiveStrategy(min_bankroll_ratio=1.1)
        assert strategy.get_progressive_bet(losing_context) == 0.0

    def test_both_conditions_must_be_met(self) -> None:
        context = ProgressiveContext(
            bankroll=1100.0,
            starting_bankroll=1000.0,
            session_profit=100.0,
            hands_played=50,
            main_streak=2,
            base_bet=10.0,
            current_jackpot=15000.0,
            seed_amount=10000.0,
            progressive_bet_amount=1.0,
        )
        # Both conditions met: profit=100 >= 50, ratio=1.1 >= 1.1
        strategy = BankrollConditionalProgressiveStrategy(
            min_session_profit=50.0, min_bankroll_ratio=1.1
        )
        assert strategy.get_progressive_bet(context) == 1.0

    def test_fails_when_one_condition_not_met(self) -> None:
        context = ProgressiveContext(
            bankroll=1050.0,
            starting_bankroll=1000.0,
            session_profit=50.0,
            hands_played=50,
            main_streak=2,
            base_bet=10.0,
            current_jackpot=15000.0,
            seed_amount=10000.0,
            progressive_bet_amount=1.0,
        )
        # Profit=50 >= 50 OK, but ratio=1.05 < 1.1 NOT OK
        strategy = BankrollConditionalProgressiveStrategy(
            min_session_profit=50.0, min_bankroll_ratio=1.1
        )
        assert strategy.get_progressive_bet(context) == 0.0

    def test_no_conditions_always_bets(
        self, default_context: ProgressiveContext
    ) -> None:
        strategy = BankrollConditionalProgressiveStrategy()
        assert strategy.get_progressive_bet(default_context) == 1.0

    def test_zero_starting_bankroll_skips_ratio_check(self) -> None:
        context = ProgressiveContext(
            bankroll=100.0,
            starting_bankroll=0.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            base_bet=10.0,
            current_jackpot=10000.0,
            seed_amount=10000.0,
            progressive_bet_amount=1.0,
        )
        strategy = BankrollConditionalProgressiveStrategy(min_bankroll_ratio=1.1)
        assert strategy.get_progressive_bet(context) == 1.0

    def test_satisfies_protocol(self) -> None:
        strategy: ProgressiveStrategy = BankrollConditionalProgressiveStrategy(
            min_session_profit=50.0
        )
        assert hasattr(strategy, "get_progressive_bet")


# ---- Factory Function Tests ----


class TestCreateProgressiveStrategy:
    """Tests for create_progressive_strategy factory function."""

    def test_create_never_strategy(self) -> None:
        config = ProgressiveStrategyConfig(type="never")
        strategy = create_progressive_strategy(config)
        assert isinstance(strategy, NeverProgressiveStrategy)

    def test_create_always_strategy(self) -> None:
        config = ProgressiveStrategyConfig(type="always")
        strategy = create_progressive_strategy(config)
        assert isinstance(strategy, AlwaysProgressiveStrategy)

    def test_create_jackpot_threshold_strategy(self) -> None:
        config = ProgressiveStrategyConfig(
            type="jackpot_threshold",
            jackpot_threshold=JackpotThresholdConfig(min_jackpot=30000.0),
        )
        strategy = create_progressive_strategy(config)
        assert isinstance(strategy, JackpotThresholdStrategy)

    def test_create_bankroll_conditional_strategy(self) -> None:
        config = ProgressiveStrategyConfig(
            type="bankroll_conditional",
            bankroll_conditional=BankrollConditionalProgressiveConfig(
                min_session_profit=100.0, min_bankroll_ratio=1.2
            ),
        )
        strategy = create_progressive_strategy(config)
        assert isinstance(strategy, BankrollConditionalProgressiveStrategy)

    def test_jackpot_threshold_missing_config_raises(self) -> None:
        config = ProgressiveStrategyConfig.model_construct(
            type="jackpot_threshold", jackpot_threshold=None, bankroll_conditional=None
        )
        with pytest.raises(ValueError, match="requires.*jackpot_threshold.*config"):
            create_progressive_strategy(config)

    def test_bankroll_conditional_missing_config_raises(self) -> None:
        config = ProgressiveStrategyConfig.model_construct(
            type="bankroll_conditional",
            jackpot_threshold=None,
            bankroll_conditional=None,
        )
        with pytest.raises(ValueError, match="requires.*bankroll_conditional.*config"):
            create_progressive_strategy(config)

    def test_unknown_type_raises(self) -> None:
        config = ProgressiveStrategyConfig.model_construct(
            type="unknown",  # type: ignore[arg-type]
            jackpot_threshold=None,
            bankroll_conditional=None,
        )
        with pytest.raises(ValueError, match="Unknown progressive strategy type"):
            create_progressive_strategy(config)


# ---- Config Model Validation Tests ----


class TestProgressiveStrategyConfig:
    """Tests for ProgressiveStrategyConfig Pydantic model."""

    def test_default_config(self) -> None:
        config = ProgressiveStrategyConfig()
        assert config.type == "never"

    def test_never_type(self) -> None:
        config = ProgressiveStrategyConfig(type="never")
        assert config.type == "never"

    def test_always_type(self) -> None:
        config = ProgressiveStrategyConfig(type="always")
        assert config.type == "always"

    def test_jackpot_threshold_type_with_config(self) -> None:
        config = ProgressiveStrategyConfig(
            type="jackpot_threshold",
            jackpot_threshold=JackpotThresholdConfig(min_jackpot=50000.0),
        )
        assert config.type == "jackpot_threshold"
        assert config.jackpot_threshold is not None
        assert config.jackpot_threshold.min_jackpot == 50000.0

    def test_jackpot_threshold_type_without_config_raises(self) -> None:
        with pytest.raises(ValueError, match="requires.*jackpot_threshold.*config"):
            ProgressiveStrategyConfig(type="jackpot_threshold")

    def test_bankroll_conditional_type_with_config(self) -> None:
        config = ProgressiveStrategyConfig(
            type="bankroll_conditional",
            bankroll_conditional=BankrollConditionalProgressiveConfig(
                min_session_profit=100.0
            ),
        )
        assert config.type == "bankroll_conditional"
        assert config.bankroll_conditional is not None

    def test_bankroll_conditional_type_without_config_raises(self) -> None:
        with pytest.raises(ValueError, match="requires.*bankroll_conditional.*config"):
            ProgressiveStrategyConfig(type="bankroll_conditional")

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValueError):
            ProgressiveStrategyConfig(type="invalid")  # type: ignore[arg-type]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ProgressiveStrategyConfig(type="never", unknown_field="value")  # type: ignore[call-arg]
