"""Unit tests for bonus betting strategy implementations.

This module tests all bonus strategy implementations:
- NeverBonusStrategy: Always returns 0
- AlwaysBonusStrategy: Returns fixed amount
- StaticBonusStrategy: Fixed amount or ratio of base bet
- BankrollConditionalBonusStrategy: Conditional betting based on profit/bankroll
"""

import pytest

from let_it_ride.config.models import (
    AlwaysBonusConfig,
    BankrollConditionalBonusConfig,
    BonusStrategyConfig,
    ProfitTier,
    ScalingConfig,
    StaticBonusConfig,
    StreakActionConfig,
    StreakBasedBonusConfig,
)
from let_it_ride.strategy import (
    AlwaysBonusStrategy,
    BankrollConditionalBonusStrategy,
    BonusContext,
    BonusStrategy,
    NeverBonusStrategy,
    StaticBonusStrategy,
    StreakBasedBonusStrategy,
    create_bonus_strategy,
)


@pytest.fixture
def default_context() -> BonusContext:
    """Create a default BonusContext for testing."""
    return BonusContext(
        bankroll=1000.0,
        starting_bankroll=1000.0,
        session_profit=0.0,
        hands_played=0,
        main_streak=0,
        bonus_streak=0,
        base_bet=10.0,
        min_bonus_bet=1.0,
        max_bonus_bet=25.0,
    )


@pytest.fixture
def profitable_context() -> BonusContext:
    """Create a BonusContext with positive session profit."""
    return BonusContext(
        bankroll=1200.0,
        starting_bankroll=1000.0,
        session_profit=200.0,
        hands_played=50,
        main_streak=3,
        bonus_streak=1,
        base_bet=10.0,
        min_bonus_bet=1.0,
        max_bonus_bet=25.0,
    )


@pytest.fixture
def losing_context() -> BonusContext:
    """Create a BonusContext with negative session profit."""
    return BonusContext(
        bankroll=700.0,
        starting_bankroll=1000.0,
        session_profit=-300.0,
        hands_played=100,
        main_streak=-5,
        bonus_streak=-3,
        base_bet=10.0,
        min_bonus_bet=1.0,
        max_bonus_bet=25.0,
    )


class TestNeverBonusStrategy:
    """Test NeverBonusStrategy always returns 0."""

    @pytest.fixture
    def strategy(self) -> NeverBonusStrategy:
        """Create a NeverBonusStrategy instance."""
        return NeverBonusStrategy()

    def test_returns_zero_default_context(
        self,
        strategy: NeverBonusStrategy,
        default_context: BonusContext,
    ) -> None:
        """Test that get_bonus_bet returns 0 in default context."""
        result = strategy.get_bonus_bet(default_context)
        assert result == 0.0

    def test_returns_zero_profitable_context(
        self,
        strategy: NeverBonusStrategy,
        profitable_context: BonusContext,
    ) -> None:
        """Test that get_bonus_bet returns 0 even when profitable."""
        result = strategy.get_bonus_bet(profitable_context)
        assert result == 0.0

    def test_returns_zero_losing_context(
        self,
        strategy: NeverBonusStrategy,
        losing_context: BonusContext,
    ) -> None:
        """Test that get_bonus_bet returns 0 even when losing."""
        result = strategy.get_bonus_bet(losing_context)
        assert result == 0.0

    @pytest.mark.parametrize(
        "bankroll,session_profit,base_bet",
        [
            (0.0, 0.0, 5.0),  # Zero bankroll
            (10000.0, 5000.0, 100.0),  # Large bankroll
            (50.0, -450.0, 5.0),  # Near bust
        ],
    )
    def test_always_returns_zero(
        self,
        strategy: NeverBonusStrategy,
        bankroll: float,
        session_profit: float,
        base_bet: float,
    ) -> None:
        """Test that strategy always returns 0 regardless of context."""
        context = BonusContext(
            bankroll=bankroll,
            starting_bankroll=500.0,
            session_profit=session_profit,
            hands_played=50,
            main_streak=0,
            bonus_streak=0,
            base_bet=base_bet,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 0.0


class TestAlwaysBonusStrategy:
    """Test AlwaysBonusStrategy returns fixed amount."""

    def test_returns_fixed_amount(self, default_context: BonusContext) -> None:
        """Test that strategy returns the configured fixed amount."""
        strategy = AlwaysBonusStrategy(amount=5.0)
        result = strategy.get_bonus_bet(default_context)
        assert result == 5.0

    def test_clamps_to_max(self, default_context: BonusContext) -> None:
        """Test that amount is clamped to max_bonus_bet."""
        strategy = AlwaysBonusStrategy(amount=100.0)
        result = strategy.get_bonus_bet(default_context)
        assert result == 25.0  # max_bonus_bet

    def test_returns_zero_below_min(self, default_context: BonusContext) -> None:
        """Test that amount below min_bonus_bet returns 0."""
        strategy = AlwaysBonusStrategy(amount=0.5)
        result = strategy.get_bonus_bet(default_context)
        assert result == 0.0  # Below min_bonus_bet of 1.0

    def test_returns_amount_at_min(self, default_context: BonusContext) -> None:
        """Test that amount exactly at min_bonus_bet is valid."""
        strategy = AlwaysBonusStrategy(amount=1.0)
        result = strategy.get_bonus_bet(default_context)
        assert result == 1.0

    def test_returns_amount_at_max(self, default_context: BonusContext) -> None:
        """Test that amount exactly at max_bonus_bet is valid."""
        strategy = AlwaysBonusStrategy(amount=25.0)
        result = strategy.get_bonus_bet(default_context)
        assert result == 25.0

    def test_ignores_context_state(
        self,
        profitable_context: BonusContext,
        losing_context: BonusContext,
    ) -> None:
        """Test that strategy ignores profit/loss state."""
        strategy = AlwaysBonusStrategy(amount=10.0)
        assert strategy.get_bonus_bet(profitable_context) == 10.0
        assert strategy.get_bonus_bet(losing_context) == 10.0


class TestStaticBonusStrategy:
    """Test StaticBonusStrategy with amount or ratio."""

    def test_fixed_amount(self, default_context: BonusContext) -> None:
        """Test that fixed amount mode works correctly."""
        strategy = StaticBonusStrategy(amount=5.0)
        result = strategy.get_bonus_bet(default_context)
        assert result == 5.0

    def test_ratio_mode(self, default_context: BonusContext) -> None:
        """Test that ratio mode calculates correctly."""
        strategy = StaticBonusStrategy(ratio=0.5)
        # base_bet is 10.0, so ratio of 0.5 = 5.0
        result = strategy.get_bonus_bet(default_context)
        assert result == 5.0

    def test_ratio_with_different_base_bet(self) -> None:
        """Test ratio mode with different base bets."""
        strategy = StaticBonusStrategy(ratio=0.2)
        context = BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=25.0,  # 25 * 0.2 = 5.0
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0

    def test_amount_clamps_to_max(self, default_context: BonusContext) -> None:
        """Test that amount is clamped to max."""
        strategy = StaticBonusStrategy(amount=50.0)
        result = strategy.get_bonus_bet(default_context)
        assert result == 25.0  # max_bonus_bet

    def test_ratio_clamps_to_max(self) -> None:
        """Test that ratio result is clamped to max."""
        strategy = StaticBonusStrategy(ratio=1.0)  # 100% of base bet
        context = BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=50.0,  # Would be 50, but max is 25
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 25.0

    def test_raises_if_both_specified(self) -> None:
        """Test that specifying both amount and ratio raises error."""
        with pytest.raises(ValueError, match="either amount or ratio, not both"):
            StaticBonusStrategy(amount=5.0, ratio=0.5)

    def test_raises_if_neither_specified(self) -> None:
        """Test that specifying neither amount nor ratio raises error."""
        with pytest.raises(ValueError, match="Must specify either amount or ratio"):
            StaticBonusStrategy()


class TestBankrollConditionalBonusStrategy:
    """Test BankrollConditionalBonusStrategy conditional betting."""

    def test_basic_bet_when_conditions_met(
        self,
        default_context: BonusContext,
    ) -> None:
        """Test that base amount is returned when conditions are met."""
        strategy = BankrollConditionalBonusStrategy(base_amount=5.0)
        result = strategy.get_bonus_bet(default_context)
        assert result == 5.0

    def test_no_bet_below_min_session_profit(self) -> None:
        """Test that no bet is placed when session profit is below minimum."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            min_session_profit=100.0,
        )
        context = BonusContext(
            bankroll=1050.0,
            starting_bankroll=1000.0,
            session_profit=50.0,  # Below 100.0 threshold
            hands_played=20,
            main_streak=2,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 0.0

    def test_bets_when_above_min_session_profit(self) -> None:
        """Test that bet is placed when session profit exceeds minimum."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            min_session_profit=100.0,
        )
        context = BonusContext(
            bankroll=1150.0,
            starting_bankroll=1000.0,
            session_profit=150.0,  # Above 100.0 threshold
            hands_played=30,
            main_streak=3,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0

    def test_no_bet_below_min_bankroll_ratio(self) -> None:
        """Test that no bet is placed when bankroll ratio is below minimum."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            min_bankroll_ratio=1.0,  # Require at least starting bankroll
        )
        context = BonusContext(
            bankroll=800.0,  # 80% of starting
            starting_bankroll=1000.0,
            session_profit=-200.0,
            hands_played=50,
            main_streak=-3,
            bonus_streak=-2,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 0.0

    def test_bets_when_above_min_bankroll_ratio(self) -> None:
        """Test that bet is placed when bankroll ratio exceeds minimum."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            min_bankroll_ratio=1.0,
        )
        context = BonusContext(
            bankroll=1100.0,  # 110% of starting
            starting_bankroll=1000.0,
            session_profit=100.0,
            hands_played=30,
            main_streak=2,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0

    def test_no_bet_when_max_drawdown_exceeded(self) -> None:
        """Test that no bet is placed when drawdown exceeds maximum."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            max_drawdown=0.20,  # 20% max drawdown
        )
        context = BonusContext(
            bankroll=700.0,  # 30% drawdown
            starting_bankroll=1000.0,
            session_profit=-300.0,
            hands_played=100,
            main_streak=-5,
            bonus_streak=-3,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 0.0

    def test_bets_when_below_max_drawdown(self) -> None:
        """Test that bet is placed when drawdown is below maximum."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            max_drawdown=0.20,
        )
        context = BonusContext(
            bankroll=900.0,  # 10% drawdown
            starting_bankroll=1000.0,
            session_profit=-100.0,
            hands_played=40,
            main_streak=-1,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0

    def test_profit_percentage_mode(self, profitable_context: BonusContext) -> None:
        """Test betting a percentage of profits."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=1.0,
            profit_percentage=0.10,  # 10% of profits
        )
        # session_profit is 200.0, so 10% = 20.0
        result = strategy.get_bonus_bet(profitable_context)
        assert result == 20.0

    def test_profit_percentage_capped_at_max(self) -> None:
        """Test that profit percentage is capped at max_bonus_bet."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=1.0,
            profit_percentage=0.50,  # 50% of profits
        )
        context = BonusContext(
            bankroll=1200.0,
            starting_bankroll=1000.0,
            session_profit=200.0,  # 50% = 100, but max is 25
            hands_played=50,
            main_streak=3,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 25.0

    def test_profit_percentage_zero_when_not_profitable(
        self,
        losing_context: BonusContext,
    ) -> None:
        """Test that profit percentage doesn't apply when not profitable."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            profit_percentage=0.10,
        )
        # session_profit is negative, so uses base_amount
        result = strategy.get_bonus_bet(losing_context)
        assert result == 5.0

    def test_scaling_tiers(self) -> None:
        """Test profit-based scaling tiers."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=1.0,
            scaling_tiers=[
                (0.0, 50.0, 2.0),  # 0-50 profit: bet 2
                (50.0, 100.0, 5.0),  # 50-100 profit: bet 5
                (100.0, None, 10.0),  # 100+ profit: bet 10
            ],
        )

        # Test tier 1: profit 25
        ctx1 = BonusContext(
            bankroll=1025.0,
            starting_bankroll=1000.0,
            session_profit=25.0,
            hands_played=10,
            main_streak=2,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        assert strategy.get_bonus_bet(ctx1) == 2.0

        # Test tier 2: profit 75
        ctx2 = BonusContext(
            bankroll=1075.0,
            starting_bankroll=1000.0,
            session_profit=75.0,
            hands_played=20,
            main_streak=3,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        assert strategy.get_bonus_bet(ctx2) == 5.0

        # Test tier 3: profit 150
        ctx3 = BonusContext(
            bankroll=1150.0,
            starting_bankroll=1000.0,
            session_profit=150.0,
            hands_played=30,
            main_streak=4,
            bonus_streak=2,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        assert strategy.get_bonus_bet(ctx3) == 10.0

    def test_combined_conditions(self) -> None:
        """Test that all conditions must be met."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            min_session_profit=50.0,
            min_bankroll_ratio=1.05,
            max_drawdown=0.10,
        )

        # Meets all conditions
        good_ctx = BonusContext(
            bankroll=1100.0,
            starting_bankroll=1000.0,
            session_profit=100.0,
            hands_played=20,
            main_streak=3,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        assert strategy.get_bonus_bet(good_ctx) == 5.0

        # Fails min_session_profit
        bad_profit_ctx = BonusContext(
            bankroll=1100.0,
            starting_bankroll=1000.0,
            session_profit=30.0,  # Below 50
            hands_played=20,
            main_streak=1,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        assert strategy.get_bonus_bet(bad_profit_ctx) == 0.0


class TestCreateBonusStrategy:
    """Test the create_bonus_strategy factory function."""

    def test_create_never_strategy(self) -> None:
        """Test creating a NeverBonusStrategy."""
        config = BonusStrategyConfig(type="never")
        strategy = create_bonus_strategy(config)
        assert isinstance(strategy, NeverBonusStrategy)

    def test_create_always_strategy(self) -> None:
        """Test creating an AlwaysBonusStrategy."""
        config = BonusStrategyConfig(
            type="always",
            always=AlwaysBonusConfig(amount=5.0),
        )
        strategy = create_bonus_strategy(config)
        assert isinstance(strategy, AlwaysBonusStrategy)

    def test_create_static_strategy_amount(self) -> None:
        """Test creating a StaticBonusStrategy with amount."""
        config = BonusStrategyConfig(
            type="static",
            static=StaticBonusConfig(amount=10.0, ratio=None),
        )
        strategy = create_bonus_strategy(config)
        assert isinstance(strategy, StaticBonusStrategy)

    def test_create_static_strategy_ratio(self) -> None:
        """Test creating a StaticBonusStrategy with ratio."""
        config = BonusStrategyConfig(
            type="static",
            static=StaticBonusConfig(amount=None, ratio=0.5),
        )
        strategy = create_bonus_strategy(config)
        assert isinstance(strategy, StaticBonusStrategy)

    def test_create_bankroll_conditional_strategy(self) -> None:
        """Test creating a BankrollConditionalBonusStrategy."""
        config = BonusStrategyConfig(
            type="bankroll_conditional",
            bankroll_conditional=BankrollConditionalBonusConfig(
                base_amount=5.0,
                min_session_profit=50.0,
            ),
        )
        strategy = create_bonus_strategy(config)
        assert isinstance(strategy, BankrollConditionalBonusStrategy)

    def test_create_bankroll_conditional_with_scaling(self) -> None:
        """Test creating BankrollConditionalBonusStrategy with scaling tiers."""
        config = BonusStrategyConfig(
            type="bankroll_conditional",
            bankroll_conditional=BankrollConditionalBonusConfig(
                base_amount=5.0,
                scaling=ScalingConfig(
                    enabled=True,
                    tiers=[
                        ProfitTier(min_profit=0.0, max_profit=50.0, bet_amount=2.0),
                        ProfitTier(min_profit=50.0, max_profit=100.0, bet_amount=5.0),
                        ProfitTier(min_profit=100.0, max_profit=None, bet_amount=10.0),
                    ],
                ),
            ),
        )
        strategy = create_bonus_strategy(config)
        assert isinstance(strategy, BankrollConditionalBonusStrategy)

    def test_always_strategy_missing_config_raises(self) -> None:
        """Test that missing config for 'always' raises ValueError."""
        config = BonusStrategyConfig(type="never")
        # Manually override type to bypass Pydantic validation
        object.__setattr__(config, "type", "always")
        with pytest.raises(ValueError, match="'always' bonus strategy requires"):
            create_bonus_strategy(config)

    def test_static_strategy_missing_config_raises(self) -> None:
        """Test that missing config for 'static' raises ValueError."""
        config = BonusStrategyConfig(type="never")
        object.__setattr__(config, "type", "static")
        with pytest.raises(ValueError, match="'static' bonus strategy requires"):
            create_bonus_strategy(config)

    def test_bankroll_conditional_missing_config_raises(self) -> None:
        """Test that missing config for 'bankroll_conditional' raises ValueError."""
        config = BonusStrategyConfig(type="never")
        object.__setattr__(config, "type", "bankroll_conditional")
        with pytest.raises(
            ValueError,
            match="'bankroll_conditional' bonus strategy requires",
        ):
            create_bonus_strategy(config)

    def test_unimplemented_strategies_raise(self) -> None:
        """Test that unimplemented strategies raise NotImplementedError."""
        for strategy_type in [
            "session_conditional",
            "combined",
            "custom",
        ]:
            config = BonusStrategyConfig(type="never")
            object.__setattr__(config, "type", strategy_type)
            with pytest.raises(NotImplementedError, match=f"'{strategy_type}'"):
                create_bonus_strategy(config)


class TestBonusStrategyProtocolConformance:
    """Test that all strategies conform to the BonusStrategy protocol."""

    @pytest.fixture
    def all_strategies(self) -> list[BonusStrategy]:
        """Create instances of all strategy types."""
        return [
            NeverBonusStrategy(),
            AlwaysBonusStrategy(amount=5.0),
            StaticBonusStrategy(amount=5.0),
            BankrollConditionalBonusStrategy(base_amount=5.0),
        ]

    def test_all_have_get_bonus_bet(
        self,
        all_strategies: list[BonusStrategy],
    ) -> None:
        """Test that all strategies have get_bonus_bet method."""
        for strategy in all_strategies:
            assert hasattr(strategy, "get_bonus_bet")
            assert callable(strategy.get_bonus_bet)

    def test_all_return_float(
        self,
        all_strategies: list[BonusStrategy],
        default_context: BonusContext,
    ) -> None:
        """Test that all strategies return float."""
        for strategy in all_strategies:
            result = strategy.get_bonus_bet(default_context)
            assert isinstance(result, float)

    def test_all_respect_max_limit(
        self,
        all_strategies: list[BonusStrategy],
        default_context: BonusContext,
    ) -> None:
        """Test that all strategies respect max_bonus_bet."""
        for strategy in all_strategies:
            result = strategy.get_bonus_bet(default_context)
            assert result <= default_context.max_bonus_bet

    def test_all_return_non_negative(
        self,
        all_strategies: list[BonusStrategy],
        default_context: BonusContext,
    ) -> None:
        """Test that all strategies return non-negative values."""
        for strategy in all_strategies:
            result = strategy.get_bonus_bet(default_context)
            assert result >= 0.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_starting_bankroll(self) -> None:
        """Test handling of zero starting bankroll."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            min_bankroll_ratio=1.0,
        )
        context = BonusContext(
            bankroll=100.0,
            starting_bankroll=0.0,  # Edge case
            session_profit=100.0,
            hands_played=10,
            main_streak=1,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        # Should not raise division by zero
        result = strategy.get_bonus_bet(context)
        assert result == 5.0  # Base amount since ratio check is skipped

    def test_very_large_amounts(self) -> None:
        """Test handling of very large amounts."""
        strategy = AlwaysBonusStrategy(amount=1_000_000.0)
        context = BonusContext(
            bankroll=1_000_000.0,
            starting_bankroll=1_000_000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=1000.0,
            min_bonus_bet=1.0,
            max_bonus_bet=100.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 100.0  # Clamped to max

    def test_zero_max_bonus_bet(self) -> None:
        """Test handling of zero max_bonus_bet."""
        strategy = AlwaysBonusStrategy(amount=5.0)
        context = BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=0.0,
            max_bonus_bet=0.0,  # No bonus bets allowed
        )
        result = strategy.get_bonus_bet(context)
        assert result == 0.0

    def test_min_equals_max(self) -> None:
        """Test when min_bonus_bet equals max_bonus_bet."""
        strategy = AlwaysBonusStrategy(amount=10.0)
        context = BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=5.0,
            max_bonus_bet=5.0,  # Only 5.0 is valid
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0  # Clamped to max (and min)

    def test_negative_session_profit_with_scaling(self) -> None:
        """Test scaling tiers with negative session profit."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            scaling_tiers=[
                (0.0, 50.0, 2.0),
                (50.0, None, 10.0),
            ],
        )
        context = BonusContext(
            bankroll=900.0,
            starting_bankroll=1000.0,
            session_profit=-100.0,  # Negative profit
            hands_played=50,
            main_streak=-2,
            bonus_streak=-1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        # No tier matches negative profit, so uses base_amount
        assert result == 5.0


class TestReviewFindings:
    """Tests addressing code review findings."""

    # Critical: Missing test for unknown strategy type
    def test_unknown_strategy_type_raises(self) -> None:
        """Test that unknown strategy type raises ValueError."""
        config = BonusStrategyConfig(type="never")
        object.__setattr__(config, "type", "unknown_strategy")
        with pytest.raises(ValueError, match="Unknown bonus strategy type"):
            create_bonus_strategy(config)

    # High: Boundary condition at exact min_session_profit threshold
    def test_bets_when_exactly_at_min_session_profit(self) -> None:
        """Test that bet is placed when session profit equals minimum exactly."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            min_session_profit=100.0,
        )
        context = BonusContext(
            bankroll=1100.0,
            starting_bankroll=1000.0,
            session_profit=100.0,  # Exactly at threshold
            hands_played=25,
            main_streak=2,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0  # Should bet at exact threshold (uses <, not <=)

    # High: Boundary condition at exact max_drawdown threshold
    def test_bets_when_exactly_at_max_drawdown(self) -> None:
        """Test that bet is placed when drawdown equals max exactly."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            max_drawdown=0.20,
        )
        context = BonusContext(
            bankroll=800.0,  # Exactly 20% drawdown
            starting_bankroll=1000.0,
            session_profit=-200.0,
            hands_played=50,
            main_streak=-3,
            bonus_streak=-1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0  # Should bet at exact threshold (uses >, not >=)

    # High: Boundary condition at exact min_bankroll_ratio threshold
    def test_bets_when_exactly_at_min_bankroll_ratio(self) -> None:
        """Test that bet is placed when bankroll ratio equals minimum exactly."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            min_bankroll_ratio=1.0,
        )
        context = BonusContext(
            bankroll=1000.0,  # Exactly 100% of starting (ratio = 1.0)
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=20,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0  # Should bet at exact threshold (uses <, not <=)

    # High: Negative amount validation
    def test_always_strategy_negative_amount_raises(self) -> None:
        """Test that negative amount raises ValueError."""
        with pytest.raises(ValueError, match="amount must be non-negative"):
            AlwaysBonusStrategy(amount=-5.0)

    # High: Zero amount returns 0
    def test_always_strategy_zero_amount_returns_zero(
        self,
        default_context: BonusContext,
    ) -> None:
        """Test that zero amount returns 0."""
        strategy = AlwaysBonusStrategy(amount=0.0)
        result = strategy.get_bonus_bet(default_context)
        assert result == 0.0

    # Medium: Static strategy negative amount/ratio validation
    def test_static_strategy_negative_amount_raises(self) -> None:
        """Test that negative amount raises ValueError."""
        with pytest.raises(ValueError, match="amount must be non-negative"):
            StaticBonusStrategy(amount=-5.0)

    def test_static_strategy_negative_ratio_raises(self) -> None:
        """Test that negative ratio raises ValueError."""
        with pytest.raises(ValueError, match="ratio must be non-negative"):
            StaticBonusStrategy(ratio=-0.5)

    # Medium: BankrollConditional negative validation
    def test_bankroll_conditional_negative_base_amount_raises(self) -> None:
        """Test that negative base_amount raises ValueError."""
        with pytest.raises(ValueError, match="base_amount must be non-negative"):
            BankrollConditionalBonusStrategy(base_amount=-5.0)

    def test_bankroll_conditional_negative_profit_percentage_raises(self) -> None:
        """Test that negative profit_percentage raises ValueError."""
        with pytest.raises(ValueError, match="profit_percentage must be non-negative"):
            BankrollConditionalBonusStrategy(
                base_amount=5.0,
                profit_percentage=-0.10,
            )

    # Medium: Zero base_bet with ratio mode
    def test_static_ratio_with_zero_base_bet(self) -> None:
        """Test ratio mode with zero base_bet returns 0."""
        strategy = StaticBonusStrategy(ratio=0.5)
        context = BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=0.0,  # Zero base bet
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 0.0  # 0 * 0.5 = 0, below min_bonus_bet

    # Medium: profit_percentage overrides scaling_tiers
    def test_profit_percentage_overrides_scaling_tiers(self) -> None:
        """Test that profit_percentage takes precedence over scaling tiers."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=1.0,
            profit_percentage=0.05,  # 5% of profit
            scaling_tiers=[
                (0.0, 100.0, 10.0),  # Would select 10.0 for profit 50
            ],
        )
        context = BonusContext(
            bankroll=1050.0,
            starting_bankroll=1000.0,
            session_profit=50.0,  # 5% = 2.5, tier would give 10.0
            hands_played=15,
            main_streak=2,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 2.5  # profit_percentage wins over tier

    # Medium: Scaling tier boundary values
    def test_scaling_tier_at_min_boundary(self) -> None:
        """Test that profit exactly at tier min_profit uses that tier."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=1.0,
            scaling_tiers=[
                (50.0, 100.0, 5.0),  # Uses >= for min
            ],
        )
        context = BonusContext(
            bankroll=1050.0,
            starting_bankroll=1000.0,
            session_profit=50.0,  # Exactly at min_profit boundary
            hands_played=15,
            main_streak=2,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0  # Should match tier (>= 50)

    def test_scaling_tier_at_max_boundary(self) -> None:
        """Test that profit exactly at tier max_profit falls to next tier."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=1.0,
            scaling_tiers=[
                (0.0, 50.0, 2.0),  # Uses < for max
                (50.0, 100.0, 5.0),
            ],
        )
        context = BonusContext(
            bankroll=1050.0,
            starting_bankroll=1000.0,
            session_profit=50.0,  # Exactly at max_profit of first tier
            hands_played=15,
            main_streak=2,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0  # Should match second tier (50 is NOT < 50)

    # Medium: Empty scaling tiers list
    def test_empty_scaling_tiers_uses_base_amount(self) -> None:
        """Test that empty scaling tiers list uses base_amount."""
        strategy = BankrollConditionalBonusStrategy(
            base_amount=5.0,
            scaling_tiers=[],  # Empty list
        )
        context = BonusContext(
            bankroll=1100.0,
            starting_bankroll=1000.0,
            session_profit=100.0,
            hands_played=25,
            main_streak=3,
            bonus_streak=1,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        result = strategy.get_bonus_bet(context)
        assert result == 5.0  # Uses base_amount since no tiers match

    # Medium: Factory creates functional strategy
    def test_factory_creates_functional_always_strategy(self) -> None:
        """Test that factory-created AlwaysBonusStrategy works correctly."""
        config = BonusStrategyConfig(
            type="always",
            always=AlwaysBonusConfig(amount=7.0),
        )
        strategy = create_bonus_strategy(config)
        context = BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=25.0,
        )
        assert strategy.get_bonus_bet(context) == 7.0


class TestStreakBasedBonusStrategy:
    """Tests for StreakBasedBonusStrategy."""

    @pytest.fixture
    def default_context(self) -> BonusContext:
        """Create a default BonusContext for testing."""
        return BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=50.0,
        )

    # Basic functionality tests
    def test_returns_base_amount_before_streak(
        self, default_context: BonusContext
    ) -> None:
        """Test that base amount is returned before streak triggers."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="main_win",
        )
        assert strategy.get_bonus_bet(default_context) == 5.0

    def test_streak_counter_starts_at_zero(self) -> None:
        """Test that streak counter starts at zero."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="main_win",
        )
        assert strategy.current_streak == 0

    def test_current_multiplier_starts_at_one(self) -> None:
        """Test that current multiplier starts at 1."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="main_win",
        )
        assert strategy.current_multiplier == 1.0

    # Trigger type tests
    def test_main_loss_trigger(self) -> None:
        """Test main_loss trigger increments streak on main game loss."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.current_streak == 1
        strategy.record_result(main_won=True, bonus_won=None)  # Should not increment
        assert strategy.current_streak == 1

    def test_main_win_trigger(self) -> None:
        """Test main_win trigger increments streak on main game win."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_win",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=True, bonus_won=None)
        assert strategy.current_streak == 1
        strategy.record_result(main_won=False, bonus_won=None)  # Should not increment
        assert strategy.current_streak == 1

    def test_bonus_loss_trigger(self) -> None:
        """Test bonus_loss trigger increments streak on bonus loss."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=True, bonus_won=False)
        assert strategy.current_streak == 1
        strategy.record_result(main_won=True, bonus_won=True)  # Should not increment
        assert strategy.current_streak == 1
        strategy.record_result(main_won=True, bonus_won=None)  # No bonus bet
        assert strategy.current_streak == 1

    def test_bonus_win_trigger(self) -> None:
        """Test bonus_win trigger increments streak on bonus win."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_win",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=True, bonus_won=True)
        assert strategy.current_streak == 1
        strategy.record_result(main_won=True, bonus_won=False)  # Should not increment
        assert strategy.current_streak == 1

    def test_any_loss_trigger(self) -> None:
        """Test any_loss trigger increments on main or bonus loss."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="any_loss",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)  # Main loss
        assert strategy.current_streak == 1
        strategy.record_result(main_won=True, bonus_won=False)  # Bonus loss
        assert strategy.current_streak == 2
        strategy.record_result(main_won=True, bonus_won=True)  # Both win
        assert strategy.current_streak == 2

    def test_any_win_trigger(self) -> None:
        """Test any_win trigger increments on main or bonus win."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="any_win",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=True, bonus_won=None)  # Main win
        assert strategy.current_streak == 1
        strategy.record_result(main_won=False, bonus_won=True)  # Bonus win
        assert strategy.current_streak == 2
        strategy.record_result(main_won=False, bonus_won=False)  # Both lose
        assert strategy.current_streak == 2

    # Action type tests
    def test_multiply_action(self, default_context: BonusContext) -> None:
        """Test multiply action doubles bet at streak length."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=2,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        # Build up streak
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        # Now at streak 2, should multiply by 2
        assert strategy.get_bonus_bet(default_context) == 10.0
        assert strategy.current_multiplier == 2.0

    def test_multiply_action_multiple_triggers(
        self, default_context: BonusContext
    ) -> None:
        """Test multiply action compounds with multiple streak triggers."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=2,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
            max_multiplier=None,
        )
        # Streak of 4 = 2 triggers, 2^2 = 4x
        for _ in range(4):
            strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.get_bonus_bet(default_context) == 20.0
        assert strategy.current_multiplier == 4.0

    def test_increase_action(self, default_context: BonusContext) -> None:
        """Test increase action adds to bet at streak length."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=2,
            action_type="increase",
            action_value=3.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        # 5 + 3 = 8
        assert strategy.get_bonus_bet(default_context) == 8.0

    def test_decrease_action(self, default_context: BonusContext) -> None:
        """Test decrease action subtracts from bet at streak length."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="bonus_loss",
            streak_length=2,
            action_type="decrease",
            action_value=3.0,
            reset_on="never",
        )
        strategy.record_result(main_won=True, bonus_won=False)
        strategy.record_result(main_won=True, bonus_won=False)
        # 10 - 3 = 7
        assert strategy.get_bonus_bet(default_context) == 7.0

    def test_decrease_action_floor_at_zero(self, default_context: BonusContext) -> None:
        """Test decrease action doesn't go below zero."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_loss",
            streak_length=1,
            action_type="decrease",
            action_value=10.0,
            reset_on="never",
        )
        strategy.record_result(main_won=True, bonus_won=False)
        # 5 - 10 = 0 (floored)
        assert strategy.get_bonus_bet(default_context) == 0.0

    def test_stop_action(self, default_context: BonusContext) -> None:
        """Test stop action stops betting when triggered."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_loss",
            streak_length=3,
            action_type="stop",
            action_value=0.0,
            reset_on="bonus_win",
        )
        # Initially betting
        assert strategy.get_bonus_bet(default_context) == 5.0

        # Build up streak to trigger stop
        strategy.record_result(main_won=True, bonus_won=False)
        strategy.record_result(main_won=True, bonus_won=False)
        strategy.record_result(main_won=True, bonus_won=False)

        # Now stopped
        assert strategy.get_bonus_bet(default_context) == 0.0

    def test_start_action(self, default_context: BonusContext) -> None:
        """Test start action begins betting when triggered."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_win",
            streak_length=2,
            action_type="start",
            action_value=0.0,
            reset_on="bonus_loss",
        )
        # Initially not betting (start action)
        assert strategy.get_bonus_bet(default_context) == 0.0

        # Build up streak to trigger start
        strategy.record_result(main_won=True, bonus_won=True)
        strategy.record_result(main_won=True, bonus_won=True)

        # Now betting
        assert strategy.get_bonus_bet(default_context) == 5.0

    # Reset behavior tests
    def test_reset_on_main_win(self) -> None:
        """Test streak resets on main win."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="main_win",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.current_streak == 2

        strategy.record_result(main_won=True, bonus_won=None)  # Reset!
        assert strategy.current_streak == 0

    def test_reset_on_main_loss(self) -> None:
        """Test streak resets on main loss."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_win",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="main_loss",
        )
        strategy.record_result(main_won=True, bonus_won=None)
        strategy.record_result(main_won=True, bonus_won=None)
        assert strategy.current_streak == 2

        strategy.record_result(main_won=False, bonus_won=None)  # Reset!
        assert strategy.current_streak == 0

    def test_reset_on_bonus_win(self) -> None:
        """Test streak resets on bonus win."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_loss",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="bonus_win",
        )
        strategy.record_result(main_won=True, bonus_won=False)
        strategy.record_result(main_won=True, bonus_won=False)
        assert strategy.current_streak == 2

        strategy.record_result(main_won=True, bonus_won=True)  # Reset!
        assert strategy.current_streak == 0

    def test_reset_on_bonus_loss(self) -> None:
        """Test streak resets on bonus loss."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_win",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="bonus_loss",
        )
        strategy.record_result(main_won=True, bonus_won=True)
        strategy.record_result(main_won=True, bonus_won=True)
        assert strategy.current_streak == 2

        strategy.record_result(main_won=True, bonus_won=False)  # Reset!
        assert strategy.current_streak == 0

    def test_reset_on_any_win(self) -> None:
        """Test streak resets on any win."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="any_loss",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="any_win",
        )
        strategy.record_result(main_won=False, bonus_won=False)
        assert strategy.current_streak == 1

        strategy.record_result(main_won=True, bonus_won=False)  # Main win resets
        assert strategy.current_streak == 0

    def test_reset_on_any_loss(self) -> None:
        """Test streak resets on any loss."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="any_win",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="any_loss",
        )
        strategy.record_result(main_won=True, bonus_won=True)
        assert strategy.current_streak == 1

        strategy.record_result(main_won=True, bonus_won=False)  # Bonus loss resets
        assert strategy.current_streak == 0

    def test_reset_on_never(self) -> None:
        """Test streak never resets when reset_on='never'."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=5,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.current_streak == 2

        # Main win should NOT reset
        strategy.record_result(main_won=True, bonus_won=True)
        assert strategy.current_streak == 2

    def test_reset_method(self) -> None:
        """Test explicit reset() method."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.current_streak == 2

        strategy.reset()
        assert strategy.current_streak == 0
        assert strategy.current_multiplier == 1.0

    def test_reset_restores_betting_for_stop_action(
        self, default_context: BonusContext
    ) -> None:
        """Test that reset() restores betting state for stop action."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_loss",
            streak_length=2,
            action_type="stop",
            action_value=0.0,
            reset_on="bonus_win",
        )
        # Trigger stop
        strategy.record_result(main_won=True, bonus_won=False)
        strategy.record_result(main_won=True, bonus_won=False)
        assert strategy.get_bonus_bet(default_context) == 0.0

        strategy.reset()
        assert strategy.get_bonus_bet(default_context) == 5.0

    def test_reset_restores_not_betting_for_start_action(
        self, default_context: BonusContext
    ) -> None:
        """Test that reset() restores not-betting state for start action."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_win",
            streak_length=2,
            action_type="start",
            action_value=0.0,
            reset_on="bonus_loss",
        )
        # Trigger start
        strategy.record_result(main_won=True, bonus_won=True)
        strategy.record_result(main_won=True, bonus_won=True)
        assert strategy.get_bonus_bet(default_context) == 5.0

        strategy.reset()
        assert strategy.get_bonus_bet(default_context) == 0.0

    # Max multiplier tests
    def test_max_multiplier_caps_multiply_action(
        self, default_context: BonusContext
    ) -> None:
        """Test that max_multiplier caps the multiply action."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=1,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
            max_multiplier=4.0,
        )
        # Each loss doubles: 2, 4, 4 (capped), 4 (capped)
        for _ in range(4):
            strategy.record_result(main_won=False, bonus_won=None)

        # Should be capped at 4x = 20.0
        assert strategy.get_bonus_bet(default_context) == 20.0
        assert strategy.current_multiplier == 4.0

    def test_max_multiplier_caps_increase_action(
        self, default_context: BonusContext
    ) -> None:
        """Test that max_multiplier caps the increase action."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=1,
            action_type="increase",
            action_value=5.0,
            reset_on="never",
            max_multiplier=3.0,  # Max bet = 5 * 3 = 15
        )
        # Each loss adds 5: 10, 15, 15 (capped)
        for _ in range(3):
            strategy.record_result(main_won=False, bonus_won=None)

        # Should be capped at 3x base = 15.0
        assert strategy.get_bonus_bet(default_context) == 15.0

    def test_no_max_multiplier(self, default_context: BonusContext) -> None:
        """Test that None max_multiplier allows unlimited growth."""
        strategy = StreakBasedBonusStrategy(
            base_amount=1.0,
            trigger="main_loss",
            streak_length=1,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
            max_multiplier=None,
        )
        # Each loss doubles: 2, 4, 8, 16, 32
        for _ in range(5):
            strategy.record_result(main_won=False, bonus_won=None)

        assert strategy.get_bonus_bet(default_context) == 32.0
        assert strategy.current_multiplier == 32.0

    # Clamping tests
    def test_bet_clamped_to_max(self, default_context: BonusContext) -> None:
        """Test that bet is clamped to max_bonus_bet."""
        strategy = StreakBasedBonusStrategy(
            base_amount=30.0,
            trigger="main_loss",
            streak_length=1,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
            max_multiplier=None,
        )
        strategy.record_result(main_won=False, bonus_won=None)
        # 30 * 2 = 60, but max is 50
        assert strategy.get_bonus_bet(default_context) == 50.0

    def test_bet_returns_zero_below_min(self) -> None:
        """Test that bet returns 0 if below min_bonus_bet."""
        context = BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=5.0,
            max_bonus_bet=50.0,
        )
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="decrease",
            action_value=8.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        # 10 - 8 = 2, but min is 5, so returns 0
        assert strategy.get_bonus_bet(context) == 0.0

    # Validation tests
    def test_negative_base_amount_raises(self) -> None:
        """Test that negative base_amount raises ValueError."""
        with pytest.raises(ValueError, match="base_amount must be non-negative"):
            StreakBasedBonusStrategy(
                base_amount=-5.0,
                trigger="main_loss",
                streak_length=3,
                action_type="multiply",
                action_value=2.0,
                reset_on="main_win",
            )

    def test_zero_streak_length_raises(self) -> None:
        """Test that streak_length < 1 raises ValueError."""
        with pytest.raises(ValueError, match="streak_length must be at least 1"):
            StreakBasedBonusStrategy(
                base_amount=5.0,
                trigger="main_loss",
                streak_length=0,
                action_type="multiply",
                action_value=2.0,
                reset_on="main_win",
            )

    def test_max_multiplier_below_one_raises(self) -> None:
        """Test that max_multiplier < 1 raises ValueError."""
        with pytest.raises(ValueError, match="max_multiplier must be at least 1"):
            StreakBasedBonusStrategy(
                base_amount=5.0,
                trigger="main_loss",
                streak_length=3,
                action_type="multiply",
                action_value=2.0,
                reset_on="main_win",
                max_multiplier=0.5,
            )

    # Reset via record_result tests
    def test_stop_action_resumes_after_reset_event(
        self, default_context: BonusContext
    ) -> None:
        """Test that stop action resumes betting after reset event."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_loss",
            streak_length=2,
            action_type="stop",
            action_value=0.0,
            reset_on="bonus_win",
        )
        # Trigger stop
        strategy.record_result(main_won=True, bonus_won=False)
        strategy.record_result(main_won=True, bonus_won=False)
        assert strategy.get_bonus_bet(default_context) == 0.0

        # Reset event should resume betting
        strategy.record_result(main_won=True, bonus_won=True)
        assert strategy.get_bonus_bet(default_context) == 5.0
        assert strategy.current_streak == 0

    def test_start_action_stops_after_reset_event(
        self, default_context: BonusContext
    ) -> None:
        """Test that start action stops betting after reset event."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="bonus_win",
            streak_length=2,
            action_type="start",
            action_value=0.0,
            reset_on="bonus_loss",
        )
        # Trigger start
        strategy.record_result(main_won=True, bonus_won=True)
        strategy.record_result(main_won=True, bonus_won=True)
        assert strategy.get_bonus_bet(default_context) == 5.0

        # Reset event should stop betting
        strategy.record_result(main_won=True, bonus_won=False)
        assert strategy.get_bonus_bet(default_context) == 0.0
        assert strategy.current_streak == 0


class TestStreakBasedBonusStrategyFactory:
    """Tests for streak_based strategy factory creation."""

    @pytest.fixture
    def default_context(self) -> BonusContext:
        """Create a default BonusContext for testing."""
        return BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=50.0,
        )

    def test_create_streak_based_strategy(self, default_context: BonusContext) -> None:
        """Test creating StreakBasedBonusStrategy via factory."""
        config = BonusStrategyConfig(
            type="streak_based",
            streak_based=StreakBasedBonusConfig(
                base_amount=5.0,
                trigger="bonus_loss",
                streak_length=3,
                action=StreakActionConfig(type="multiply", value=2.0),
                reset_on="bonus_win",
                max_multiplier=5.0,
            ),
        )
        strategy = create_bonus_strategy(config)
        assert isinstance(strategy, StreakBasedBonusStrategy)
        assert strategy.get_bonus_bet(default_context) == 5.0

    def test_streak_based_missing_config_raises(self) -> None:
        """Test that missing streak_based config raises ValueError."""
        config = BonusStrategyConfig(type="never")
        object.__setattr__(config, "type", "streak_based")
        with pytest.raises(ValueError, match="'streak_based' bonus strategy requires"):
            create_bonus_strategy(config)

    def test_factory_creates_functional_streak_strategy(
        self, default_context: BonusContext
    ) -> None:
        """Test that factory-created strategy works correctly."""
        config = BonusStrategyConfig(
            type="streak_based",
            streak_based=StreakBasedBonusConfig(
                base_amount=5.0,
                trigger="main_loss",
                streak_length=2,
                action=StreakActionConfig(type="multiply", value=2.0),
                reset_on="main_win",
                max_multiplier=5.0,
            ),
        )
        strategy = create_bonus_strategy(config)

        # Initial bet
        assert strategy.get_bonus_bet(default_context) == 5.0

        # Build streak
        assert isinstance(strategy, StreakBasedBonusStrategy)
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)

        # Streak triggered, bet should be doubled
        assert strategy.get_bonus_bet(default_context) == 10.0


class TestStreakBasedBonusStrategyProtocolConformance:
    """Test that StreakBasedBonusStrategy conforms to BonusStrategy protocol."""

    @pytest.fixture
    def default_context(self) -> BonusContext:
        """Create a default BonusContext for testing."""
        return BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=50.0,
        )

    def test_has_get_bonus_bet(self) -> None:
        """Test that strategy has get_bonus_bet method."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="main_win",
        )
        assert hasattr(strategy, "get_bonus_bet")
        assert callable(strategy.get_bonus_bet)

    def test_returns_float(self, default_context: BonusContext) -> None:
        """Test that get_bonus_bet returns float."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="main_win",
        )
        result = strategy.get_bonus_bet(default_context)
        assert isinstance(result, float)

    def test_respects_max_limit(self, default_context: BonusContext) -> None:
        """Test that strategy respects max_bonus_bet."""
        strategy = StreakBasedBonusStrategy(
            base_amount=100.0,
            trigger="main_loss",
            streak_length=1,
            action_type="multiply",
            action_value=10.0,
            reset_on="never",
            max_multiplier=None,
        )
        strategy.record_result(main_won=False, bonus_won=None)
        result = strategy.get_bonus_bet(default_context)
        assert result <= default_context.max_bonus_bet

    def test_returns_non_negative(self, default_context: BonusContext) -> None:
        """Test that strategy returns non-negative values."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=3,
            action_type="multiply",
            action_value=2.0,
            reset_on="main_win",
        )
        result = strategy.get_bonus_bet(default_context)
        assert result >= 0.0


class TestStreakBasedBonusStrategyMultiplierCalculations:
    """Test current_multiplier property calculations."""

    def test_multiplier_for_multiply_action(self) -> None:
        """Test multiplier calculation for multiply action."""
        strategy = StreakBasedBonusStrategy(
            base_amount=5.0,
            trigger="main_loss",
            streak_length=2,
            action_type="multiply",
            action_value=3.0,
            reset_on="never",
            max_multiplier=None,  # No cap
        )
        # Before trigger
        assert strategy.current_multiplier == 1.0

        # At streak 2 (1 trigger): 3^1 = 3
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.current_multiplier == 3.0

        # At streak 4 (2 triggers): 3^2 = 9
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.current_multiplier == 9.0

    def test_multiplier_for_increase_action(self) -> None:
        """Test multiplier calculation for increase action."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=2,
            action_type="increase",
            action_value=5.0,
            reset_on="never",
        )
        # Before trigger
        assert strategy.current_multiplier == 1.0

        # At streak 2: 10 + 5 = 15, multiplier = 1.5
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.current_multiplier == 1.5

    def test_multiplier_for_decrease_action(self) -> None:
        """Test multiplier calculation for decrease action."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=2,
            action_type="decrease",
            action_value=5.0,
            reset_on="never",
        )
        # At streak 2: 10 - 5 = 5, multiplier = 0.5
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy.current_multiplier == 0.5

    def test_multiplier_for_decrease_at_zero_base(self) -> None:
        """Test multiplier calculation when base_amount is 0."""
        strategy = StreakBasedBonusStrategy(
            base_amount=0.0,
            trigger="main_loss",
            streak_length=2,
            action_type="decrease",
            action_value=5.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        # Should return 0.0 when base is 0
        assert strategy.current_multiplier == 0.0

    def test_multiplier_for_increase_at_zero_base(self) -> None:
        """Test multiplier calculation when base_amount is 0 (increase action)."""
        strategy = StreakBasedBonusStrategy(
            base_amount=0.0,
            trigger="main_loss",
            streak_length=2,
            action_type="increase",
            action_value=5.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        # Should return 1.0 when base is 0
        assert strategy.current_multiplier == 1.0


class TestStreakBasedBonusStrategyEdgeCases:
    """Tests for edge cases and validation scenarios in StreakBasedBonusStrategy."""

    @pytest.fixture
    def default_context(self) -> BonusContext:
        """Create a default BonusContext for testing."""
        return BonusContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            hands_played=0,
            main_streak=0,
            bonus_streak=0,
            base_bet=10.0,
            min_bonus_bet=1.0,
            max_bonus_bet=100.0,
        )

    def test_invalid_trigger_returns_false_on_match(self) -> None:
        """Test that invalid trigger string silently returns False for matches.

        Note: The current implementation accepts any string but invalid triggers
        never match any event, effectively disabling streak tracking.
        """
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="invalid_trigger",  # type: ignore[arg-type]
            streak_length=1,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        # Should not trigger on any result
        strategy.record_result(main_won=True, bonus_won=True)
        strategy.record_result(main_won=False, bonus_won=False)
        assert strategy._current_streak == 0  # Never incremented

    def test_invalid_action_type_returns_base_amount(
        self, default_context: BonusContext
    ) -> None:
        """Test that invalid action_type silently returns base_amount.

        Note: The current implementation falls through to base_amount for
        unknown action types.
        """
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="invalid_action",  # type: ignore[arg-type]
            action_value=2.0,
            reset_on="never",
        )
        # Trigger a streak
        strategy.record_result(main_won=False, bonus_won=None)
        # Invalid action type should still return base_amount
        bet = strategy.get_bonus_bet(default_context)
        assert bet == 10.0

    def test_invalid_reset_on_never_resets(self) -> None:
        """Test that invalid reset_on string never resets the streak.

        Note: The current implementation accepts any string but invalid reset_on
        values never match any event, so streak never resets.
        """
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="multiply",
            action_value=2.0,
            reset_on="invalid_reset",  # type: ignore[arg-type]
        )
        # Build up streak
        strategy.record_result(main_won=False, bonus_won=None)
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy._current_streak == 2
        # Try to reset - won't work with invalid reset_on
        strategy.record_result(main_won=True, bonus_won=True)
        strategy.record_result(main_won=True, bonus_won=True)
        # Streak doesn't reset (main_win doesn't match "invalid_reset")
        assert strategy._current_streak == 2

    def test_trigger_equals_reset_on_conflict(
        self, default_context: BonusContext
    ) -> None:
        """Test behavior when trigger and reset_on are the same event.

        When trigger == reset_on, the reset check happens after trigger check,
        so the streak resets immediately, preventing any streak from building.
        """
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=3,  # Needs 3 to trigger
            action_type="multiply",
            action_value=2.0,
            reset_on="main_loss",  # Same as trigger!
        )
        # Each main_loss triggers but then immediately resets
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy._current_streak == 0  # Reset after trigger
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy._current_streak == 0  # Reset after trigger
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy._current_streak == 0  # Never reaches 3

        # Bet should always be base_amount since streak never builds
        bet = strategy.get_bonus_bet(default_context)
        assert bet == 10.0

    def test_action_value_zero_for_multiply(
        self, default_context: BonusContext
    ) -> None:
        """Test multiply action with value=0 (multiplies to 0)."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="multiply",
            action_value=0.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        # 10 * 0^1 = 0, clamped to min
        bet = strategy.get_bonus_bet(default_context)
        # Returns 0 because 0 < min_bonus_bet (1.0)
        assert bet == 0.0

    def test_action_value_zero_for_increase(
        self, default_context: BonusContext
    ) -> None:
        """Test increase action with value=0 (no change)."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="increase",
            action_value=0.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        # 10 + (1 trigger * 0) = 10
        bet = strategy.get_bonus_bet(default_context)
        assert bet == 10.0

    def test_action_value_zero_for_decrease(
        self, default_context: BonusContext
    ) -> None:
        """Test decrease action with value=0 (no change)."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="decrease",
            action_value=0.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        # 10 - (1 trigger * 0) = 10
        bet = strategy.get_bonus_bet(default_context)
        assert bet == 10.0

    def test_negative_action_value_for_multiply(
        self, default_context: BonusContext
    ) -> None:
        """Test multiply action with negative value (results in 0 bet)."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="multiply",
            action_value=-2.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        # 10 * (-2)^1 = -20, clamped to 0
        bet = strategy.get_bonus_bet(default_context)
        assert bet == 0.0

    def test_negative_action_value_for_increase(
        self, default_context: BonusContext
    ) -> None:
        """Test increase action with negative value (decreases bet)."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="increase",
            action_value=-5.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        # 10 + (1 * -5) = 5
        bet = strategy.get_bonus_bet(default_context)
        assert bet == 5.0

    def test_negative_action_value_for_decrease(
        self, default_context: BonusContext
    ) -> None:
        """Test decrease action with negative value (increases bet)."""
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="main_loss",
            streak_length=1,
            action_type="decrease",
            action_value=-5.0,
            reset_on="never",
        )
        strategy.record_result(main_won=False, bonus_won=None)
        # 10 - (1 * -5) = 15
        bet = strategy.get_bonus_bet(default_context)
        assert bet == 15.0

    def test_any_win_trigger_with_bonus_won_none(self) -> None:
        """Test any_win trigger when bonus_won is None (no bonus bet placed).

        When bonus_won is None, only main_won matters for any_win/any_loss.
        """
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="any_win",
            streak_length=1,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        # Main win with no bonus bet
        strategy.record_result(main_won=True, bonus_won=None)
        assert strategy._current_streak == 1
        # Main loss with no bonus bet
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy._current_streak == 1  # Loss doesn't add to win streak

    def test_any_loss_trigger_with_bonus_won_none(self) -> None:
        """Test any_loss trigger when bonus_won is None (no bonus bet placed).

        When bonus_won is None, only main_won matters for any_win/any_loss.
        """
        strategy = StreakBasedBonusStrategy(
            base_amount=10.0,
            trigger="any_loss",
            streak_length=1,
            action_type="multiply",
            action_value=2.0,
            reset_on="never",
        )
        # Main loss with no bonus bet
        strategy.record_result(main_won=False, bonus_won=None)
        assert strategy._current_streak == 1
        # Main win with no bonus bet
        strategy.record_result(main_won=True, bonus_won=None)
        assert strategy._current_streak == 1  # Win doesn't add to loss streak
