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
)
from let_it_ride.strategy import (
    AlwaysBonusStrategy,
    BankrollConditionalBonusStrategy,
    BonusContext,
    BonusStrategy,
    NeverBonusStrategy,
    StaticBonusStrategy,
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
            "streak_based",
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
