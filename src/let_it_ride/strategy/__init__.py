"""Strategy implementations.

This module contains strategy implementations for pull/ride decisions:
- Basic strategy (mathematically optimal)
- Baseline strategies (always ride, always pull)
- Conservative and aggressive variants
- Custom configurable strategies
- Bonus betting strategies
"""

from let_it_ride.strategy.base import Decision, Strategy, StrategyContext
from let_it_ride.strategy.baseline import AlwaysPullStrategy, AlwaysRideStrategy
from let_it_ride.strategy.basic import BasicStrategy
from let_it_ride.strategy.bonus import (
    AlwaysBonusStrategy,
    BankrollConditionalBonusStrategy,
    BonusContext,
    BonusStrategy,
    NeverBonusStrategy,
    StaticBonusStrategy,
    StreakBasedBonusStrategy,
    create_bonus_strategy,
)
from let_it_ride.strategy.custom import (
    ConditionParseError,
    CustomStrategy,
    InvalidFieldError,
    StrategyRule,
)
from let_it_ride.strategy.presets import aggressive_strategy, conservative_strategy
from let_it_ride.strategy.progressive import (
    AlwaysProgressiveStrategy,
    BankrollConditionalProgressiveStrategy,
    JackpotThresholdStrategy,
    NeverProgressiveStrategy,
    ProgressiveContext,
    ProgressiveStrategy,
    create_progressive_strategy,
)

__all__ = [
    "AlwaysBonusStrategy",
    "AlwaysProgressiveStrategy",
    "AlwaysPullStrategy",
    "AlwaysRideStrategy",
    "BankrollConditionalBonusStrategy",
    "BankrollConditionalProgressiveStrategy",
    "BasicStrategy",
    "BonusContext",
    "BonusStrategy",
    "ConditionParseError",
    "CustomStrategy",
    "Decision",
    "InvalidFieldError",
    "JackpotThresholdStrategy",
    "NeverBonusStrategy",
    "NeverProgressiveStrategy",
    "ProgressiveContext",
    "ProgressiveStrategy",
    "StaticBonusStrategy",
    "StreakBasedBonusStrategy",
    "Strategy",
    "StrategyContext",
    "StrategyRule",
    "aggressive_strategy",
    "conservative_strategy",
    "create_bonus_strategy",
    "create_progressive_strategy",
]
