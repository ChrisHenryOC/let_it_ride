"""Progressive jackpot side bet strategies.

This module provides implementations for various progressive betting strategies
that determine when a player places the optional progressive jackpot side bet.
Unlike the three-card bonus (where the house edge is fixed), the progressive
side bet's expected value shifts as the jackpot grows.

Strategies:
- NeverProgressiveStrategy: Never places the progressive bet
- AlwaysProgressiveStrategy: Always places the progressive bet
- JackpotThresholdStrategy: Only bet when jackpot exceeds a threshold
- BankrollConditionalProgressiveStrategy: Bet based on session profit/bankroll
"""

from dataclasses import dataclass
from typing import Protocol

from let_it_ride.config.models import ProgressiveStrategyConfig


@dataclass(frozen=True, slots=True)
class ProgressiveContext:
    """Context available to progressive strategy implementations.

    Extends the information available in BonusContext with jackpot state,
    enabling strategies that consider the current jackpot size.

    Attributes:
        bankroll: Current bankroll amount.
        starting_bankroll: Initial session bankroll.
        session_profit: Current session profit/loss (positive = profit).
        hands_played: Number of hands played this session.
        main_streak: Current main game win/loss streak.
            Positive = consecutive wins, negative = consecutive losses.
        base_bet: Current base bet amount for the main game.
        current_jackpot: Current jackpot pool value.
        seed_amount: Jackpot seed/reset value.
        progressive_bet_amount: Standard bet amount (e.g., $1).
    """

    bankroll: float
    starting_bankroll: float
    session_profit: float
    hands_played: int
    main_streak: int
    base_bet: float
    current_jackpot: float
    seed_amount: float
    progressive_bet_amount: float


class ProgressiveStrategy(Protocol):
    """Protocol defining the interface for progressive betting strategies.

    A progressive strategy determines whether the player places the optional
    progressive jackpot side bet based on the current session and jackpot context.
    """

    def get_progressive_bet(self, context: ProgressiveContext) -> float:
        """Determine the progressive bet amount.

        Args:
            context: Current session and jackpot context for decision making.

        Returns:
            The progressive bet amount (0 means don't bet).
        """
        ...


class NeverProgressiveStrategy:
    """Strategy that never places the progressive bet.

    Always returns 0, effectively disabling the progressive side bet.
    """

    __slots__ = ()

    def get_progressive_bet(
        self,
        context: ProgressiveContext,  # noqa: ARG002
    ) -> float:
        """Always returns 0 (no progressive bet).

        Args:
            context: Session context (unused).

        Returns:
            Always 0.0.
        """
        return 0.0


class AlwaysProgressiveStrategy:
    """Strategy that always places the progressive bet.

    Places the standard progressive bet amount on every hand.
    """

    __slots__ = ()

    def get_progressive_bet(self, context: ProgressiveContext) -> float:
        """Return the standard progressive bet amount.

        Args:
            context: Session context with progressive bet amount.

        Returns:
            The standard progressive bet amount.
        """
        return context.progressive_bet_amount


class JackpotThresholdStrategy:
    """Strategy that only bets when the jackpot meets or exceeds a threshold.

    This is the most strategically interesting progressive strategy. It allows
    simulating "smart" progressive play where the player only places the bet
    when the expected value improves due to a large jackpot.

    The threshold represents the minimum jackpot size at which the player
    considers the bet worthwhile.
    """

    __slots__ = ("_min_jackpot",)

    def __init__(self, min_jackpot: float) -> None:
        """Initialize with a jackpot threshold.

        Args:
            min_jackpot: Minimum jackpot pool value to place the bet.

        Raises:
            ValueError: If min_jackpot is negative.
        """
        if min_jackpot < 0:
            raise ValueError("min_jackpot must be non-negative")
        self._min_jackpot = min_jackpot

    def get_progressive_bet(self, context: ProgressiveContext) -> float:
        """Return the bet amount if jackpot meets threshold, else 0.

        Args:
            context: Session context with current jackpot value.

        Returns:
            The progressive bet amount if jackpot >= threshold, else 0.
        """
        if context.current_jackpot >= self._min_jackpot:
            return context.progressive_bet_amount
        return 0.0


class BankrollConditionalProgressiveStrategy:
    """Strategy that bets based on bankroll and profit conditions.

    Similar to the BankrollConditionalBonusStrategy, this places the
    progressive bet only when session profit and/or bankroll ratio
    conditions are met.
    """

    __slots__ = ("_min_session_profit", "_min_bankroll_ratio")

    def __init__(
        self,
        min_session_profit: float | None = None,
        min_bankroll_ratio: float | None = None,
    ) -> None:
        """Initialize with bankroll conditions.

        Args:
            min_session_profit: Minimum session profit required to bet.
                None means no minimum.
            min_bankroll_ratio: Minimum bankroll/starting_bankroll ratio
                required to bet. None means no minimum.
        """
        self._min_session_profit = min_session_profit
        self._min_bankroll_ratio = min_bankroll_ratio

    def get_progressive_bet(self, context: ProgressiveContext) -> float:
        """Return the bet amount if conditions are met, else 0.

        Args:
            context: Session context with bankroll and profit info.

        Returns:
            The progressive bet amount if conditions met, else 0.
        """
        if (
            self._min_session_profit is not None
            and context.session_profit < self._min_session_profit
        ):
            return 0.0

        if self._min_bankroll_ratio is not None:
            if context.starting_bankroll <= 0:
                # Fail-closed: cannot compute ratio, skip bet
                return 0.0
            current_ratio = context.bankroll / context.starting_bankroll
            if current_ratio < self._min_bankroll_ratio:
                return 0.0

        return context.progressive_bet_amount


def create_progressive_strategy(
    config: ProgressiveStrategyConfig,
) -> ProgressiveStrategy:
    """Factory function to create a progressive strategy from configuration.

    Args:
        config: The progressive strategy configuration.

    Returns:
        An instance of the appropriate ProgressiveStrategy implementation.

    Raises:
        ValueError: If the strategy type is unknown or configuration is invalid.
    """
    strategy_type = config.type

    if strategy_type == "never":
        return NeverProgressiveStrategy()

    if strategy_type == "always":
        return AlwaysProgressiveStrategy()

    # Note: The None checks below duplicate Pydantic's model_validator on
    # ProgressiveStrategyConfig. They are intentionally defensive to guard
    # against callers using model_construct() which bypasses validation.
    if strategy_type == "jackpot_threshold":
        if config.jackpot_threshold is None:
            raise ValueError(
                "'jackpot_threshold' progressive strategy requires "
                "'jackpot_threshold' config section"
            )
        return JackpotThresholdStrategy(
            min_jackpot=config.jackpot_threshold.min_jackpot,
        )

    if strategy_type == "bankroll_conditional":
        if config.bankroll_conditional is None:
            raise ValueError(
                "'bankroll_conditional' progressive strategy requires "
                "'bankroll_conditional' config section"
            )
        bc = config.bankroll_conditional
        return BankrollConditionalProgressiveStrategy(
            min_session_profit=bc.min_session_profit,
            min_bankroll_ratio=bc.min_bankroll_ratio,
        )

    raise ValueError(f"Unknown progressive strategy type: {strategy_type}")
