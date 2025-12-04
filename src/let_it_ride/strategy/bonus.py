"""Bonus betting strategies for the Three-Card Bonus side bet.

This module provides implementations for various bonus betting strategies:
- NeverBonusStrategy: Never places bonus bets
- AlwaysBonusStrategy: Always places a fixed bonus bet amount
- StaticBonusStrategy: Fixed amount or ratio of base bet
- BankrollConditionalBonusStrategy: Bet based on session profit and bankroll conditions

All strategies respect min/max bonus bet limits.
"""

from dataclasses import dataclass
from typing import Protocol

from let_it_ride.config.models import BonusStrategyConfig


@dataclass(frozen=True, slots=True)
class BonusContext:
    """Context available to bonus strategy implementations.

    This context provides session state information that bonus strategies
    use to determine the appropriate bonus bet amount.

    Attributes:
        bankroll: Current bankroll amount.
        starting_bankroll: Initial session bankroll.
        session_profit: Current session profit/loss (positive = profit).
        hands_played: Number of hands played this session.
        main_streak: Current main game win/loss streak.
            Positive = consecutive wins, negative = consecutive losses.
        bonus_streak: Current bonus bet win/loss streak.
            Positive = consecutive wins, negative = consecutive losses.
        base_bet: Current base bet amount for the main game.
        min_bonus_bet: Minimum allowed bonus bet.
        max_bonus_bet: Maximum allowed bonus bet.
    """

    bankroll: float
    starting_bankroll: float
    session_profit: float
    hands_played: int
    main_streak: int
    bonus_streak: int
    base_bet: float
    min_bonus_bet: float
    max_bonus_bet: float


class BonusStrategy(Protocol):
    """Protocol defining the interface for bonus betting strategies.

    A bonus strategy determines the bonus bet amount based on the
    current session context. Strategies must respect min/max limits.
    """

    def get_bonus_bet(self, context: BonusContext) -> float:
        """Determine the bonus bet amount.

        Args:
            context: Current session context for decision making.

        Returns:
            The bonus bet amount (0 means no bonus bet).
            Returns 0 if below min_bonus_bet, otherwise clamped to max_bonus_bet.
        """
        ...


def _clamp_bonus_bet(bet: float, context: BonusContext) -> float:
    """Clamp a bonus bet to valid limits.

    Args:
        bet: The proposed bet amount.
        context: Context with min/max limits.

    Returns:
        The clamped bet amount. Returns 0 if bet is below min_bonus_bet.
    """
    if bet <= 0:
        return 0.0
    if bet < context.min_bonus_bet:
        return 0.0
    return min(bet, context.max_bonus_bet)


class NeverBonusStrategy:
    """Strategy that never places bonus bets.

    This is the simplest bonus strategy - always returns 0 for the
    bonus bet amount, effectively disabling the three-card bonus.
    """

    __slots__ = ()

    def get_bonus_bet(
        self,
        context: BonusContext,  # noqa: ARG002
    ) -> float:
        """Always returns 0 (no bonus bet).

        Args:
            context: Session context (unused).

        Returns:
            Always 0.0.
        """
        return 0.0


class AlwaysBonusStrategy:
    """Strategy that always places a fixed bonus bet.

    This strategy places the same bonus bet amount on every hand,
    clamped to the table limits.
    """

    __slots__ = ("_amount",)

    def __init__(self, amount: float) -> None:
        """Initialize with a fixed bet amount.

        Args:
            amount: The fixed bonus bet amount to place.

        Raises:
            ValueError: If amount is negative.
        """
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self._amount = amount

    def get_bonus_bet(self, context: BonusContext) -> float:
        """Return the fixed bonus bet amount.

        Args:
            context: Session context for limit clamping.

        Returns:
            The fixed amount, clamped to table limits.
        """
        return _clamp_bonus_bet(self._amount, context)


class StaticBonusStrategy:
    """Strategy that places a static bonus bet based on amount or ratio.

    Can be configured with either:
    - A fixed amount: Always bet this amount
    - A ratio: Bet this fraction of the base bet

    Exactly one of amount or ratio must be specified.
    """

    __slots__ = ("_amount", "_ratio")

    def __init__(
        self,
        amount: float | None = None,
        ratio: float | None = None,
    ) -> None:
        """Initialize with either a fixed amount or ratio.

        Args:
            amount: Fixed bonus bet amount. Mutually exclusive with ratio.
            ratio: Fraction of base bet to use as bonus bet.
                Mutually exclusive with amount.

        Raises:
            ValueError: If neither or both amount and ratio are specified,
                or if values are negative.
        """
        if amount is not None and ratio is not None:
            raise ValueError("Specify either amount or ratio, not both")
        if amount is None and ratio is None:
            raise ValueError("Must specify either amount or ratio")
        if amount is not None and amount < 0:
            raise ValueError("amount must be non-negative")
        if ratio is not None and ratio < 0:
            raise ValueError("ratio must be non-negative")

        self._amount = amount
        self._ratio = ratio

    def get_bonus_bet(self, context: BonusContext) -> float:
        """Calculate the bonus bet amount.

        Args:
            context: Session context with base bet and limits.

        Returns:
            The calculated amount, clamped to table limits.
        """
        if self._amount is not None:
            bet = self._amount
        else:
            # ratio is guaranteed to be set due to __init__ validation
            assert self._ratio is not None
            bet = context.base_bet * self._ratio
        return _clamp_bonus_bet(bet, context)


class BankrollConditionalBonusStrategy:
    """Strategy that bets based on bankroll and profit conditions.

    This strategy only places bonus bets when certain conditions are met:
    - Session profit exceeds a minimum threshold
    - Bankroll ratio (current/starting) exceeds a minimum
    - Drawdown from starting bankroll hasn't exceeded a maximum

    Can also scale bets based on profit tiers.
    """

    __slots__ = (
        "_base_amount",
        "_min_session_profit",
        "_min_bankroll_ratio",
        "_profit_percentage",
        "_max_drawdown",
        "_scaling_tiers",
    )

    def __init__(
        self,
        base_amount: float,
        min_session_profit: float | None = None,
        min_bankroll_ratio: float | None = None,
        profit_percentage: float | None = None,
        max_drawdown: float | None = None,
        scaling_tiers: list[tuple[float, float | None, float]] | None = None,
    ) -> None:
        """Initialize with bankroll conditions.

        Args:
            base_amount: Base bonus bet amount when conditions are met.
            min_session_profit: Minimum session profit required to bet.
                None means no minimum.
            min_bankroll_ratio: Minimum bankroll/starting_bankroll ratio
                required to bet. None means no minimum.
            profit_percentage: If set and session is profitable, bet this
                fraction of session profit. Overrides both base_amount and
                scaling_tiers. None uses base_amount or scaling tiers.
            max_drawdown: Maximum drawdown from starting bankroll as fraction
                (0-1). If exceeded, no bonus bets. None means no limit.
            scaling_tiers: List of (min_profit, max_profit, bet_amount) tuples.
                When profit is in range [min, max), use that bet_amount.
                Tiers are matched in order; provide in ascending min_profit order.
                If None, uses base_amount.

        Raises:
            ValueError: If base_amount or profit_percentage is negative.
        """
        if base_amount < 0:
            raise ValueError("base_amount must be non-negative")
        if profit_percentage is not None and profit_percentage < 0:
            raise ValueError("profit_percentage must be non-negative")
        self._base_amount = base_amount
        self._min_session_profit = min_session_profit
        self._min_bankroll_ratio = min_bankroll_ratio
        self._profit_percentage = profit_percentage
        self._max_drawdown = max_drawdown
        self._scaling_tiers = scaling_tiers

    def get_bonus_bet(self, context: BonusContext) -> float:
        """Calculate the bonus bet based on conditions.

        Args:
            context: Session context with bankroll and profit info.

        Returns:
            The calculated amount if conditions are met, 0 otherwise.
        """
        # Check min session profit condition
        if (
            self._min_session_profit is not None
            and context.session_profit < self._min_session_profit
        ):
            return 0.0

        # Check min bankroll ratio condition
        if self._min_bankroll_ratio is not None and context.starting_bankroll > 0:
            current_ratio = context.bankroll / context.starting_bankroll
            if current_ratio < self._min_bankroll_ratio:
                return 0.0

        # Check max drawdown condition (drawdown from starting bankroll)
        if self._max_drawdown is not None and context.starting_bankroll > 0:
            drawdown = (
                context.starting_bankroll - context.bankroll
            ) / context.starting_bankroll
            if drawdown > self._max_drawdown:
                return 0.0

        # Determine bet amount
        bet = self._base_amount

        # Check scaling tiers
        if self._scaling_tiers:
            for min_profit, max_profit, tier_amount in self._scaling_tiers:
                in_range = context.session_profit >= min_profit and (
                    max_profit is None or context.session_profit < max_profit
                )
                if in_range:
                    bet = tier_amount
                    break

        # Override with profit percentage if set
        if self._profit_percentage is not None and context.session_profit > 0:
            bet = context.session_profit * self._profit_percentage

        return _clamp_bonus_bet(bet, context)


def create_bonus_strategy(config: BonusStrategyConfig) -> BonusStrategy:
    """Factory function to create a bonus strategy from configuration.

    Args:
        config: The bonus strategy configuration.

    Returns:
        An instance of the appropriate BonusStrategy implementation.

    Raises:
        ValueError: If the strategy type is unknown or configuration is invalid.
    """
    strategy_type = config.type

    if strategy_type == "never":
        return NeverBonusStrategy()

    if strategy_type == "always":
        if config.always is None:
            raise ValueError("'always' bonus strategy requires 'always' config section")
        return AlwaysBonusStrategy(amount=config.always.amount)

    if strategy_type == "static":
        if config.static is None:
            raise ValueError("'static' bonus strategy requires 'static' config section")
        return StaticBonusStrategy(
            amount=config.static.amount,
            ratio=config.static.ratio,
        )

    if strategy_type == "bankroll_conditional":
        if config.bankroll_conditional is None:
            raise ValueError(
                "'bankroll_conditional' bonus strategy requires "
                "'bankroll_conditional' config section"
            )
        bc = config.bankroll_conditional
        # Convert scaling config to tuple format
        scaling_tiers = None
        if bc.scaling.enabled and bc.scaling.tiers:
            scaling_tiers = [
                (tier.min_profit, tier.max_profit, tier.bet_amount)
                for tier in bc.scaling.tiers
            ]
        return BankrollConditionalBonusStrategy(
            base_amount=bc.base_amount,
            min_session_profit=bc.min_session_profit,
            min_bankroll_ratio=bc.min_bankroll_ratio,
            profit_percentage=bc.profit_percentage,
            max_drawdown=bc.max_drawdown,
            scaling_tiers=scaling_tiers,
        )

    # Strategies not yet implemented (can be added later)
    if strategy_type in (
        "streak_based",
        "session_conditional",
        "combined",
        "custom",
    ):
        raise NotImplementedError(
            f"Bonus strategy type '{strategy_type}' is not yet implemented"
        )

    raise ValueError(f"Unknown bonus strategy type: {strategy_type}")
