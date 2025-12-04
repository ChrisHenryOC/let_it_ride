"""Pydantic models for YAML configuration.

This module defines all configuration models for the Let It Ride simulator.
Each model validates its inputs and provides sensible defaults where appropriate.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MetadataConfig(BaseModel):
    """Optional metadata about the configuration file.

    Attributes:
        name: A descriptive name for this configuration.
        description: Detailed description of what this configuration tests.
        version: Version string for tracking changes.
        author: Author of this configuration.
        created: Creation date string (any format).
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    version: str | None = None
    author: str | None = None
    created: str | None = None


class SimulationConfig(BaseModel):
    """Configuration for the simulation run parameters.

    Attributes:
        num_sessions: Number of complete sessions to simulate (1-100M).
        hands_per_session: Maximum hands per session (1-10,000).
        random_seed: Optional seed for reproducible results.
        workers: Number of parallel workers or "auto" for CPU count.
        progress_interval: Report progress every N sessions.
        detailed_logging: Enable per-hand logging (warning: large output).
    """

    model_config = ConfigDict(extra="forbid")

    num_sessions: Annotated[int, Field(ge=1, le=100_000_000)] = 10000
    hands_per_session: Annotated[int, Field(ge=1, le=10_000)] = 200
    random_seed: int | None = None
    workers: int | Literal["auto"] = "auto"
    progress_interval: Annotated[int, Field(ge=1)] = 10000
    detailed_logging: bool = False

    @model_validator(mode="after")
    def validate_workers(self) -> SimulationConfig:
        """Validate workers is positive if numeric."""
        if isinstance(self.workers, int) and self.workers < 1:
            raise ValueError("workers must be positive or 'auto'")
        return self


class DeckConfig(BaseModel):
    """Configuration for deck handling.

    Attributes:
        shuffle_algorithm: Algorithm for shuffling.
            - fisher_yates: Standard Fisher-Yates shuffle (fast, good quality)
            - cryptographic: Use system random source (slower, better randomness)
    """

    model_config = ConfigDict(extra="forbid")

    shuffle_algorithm: Literal["fisher_yates", "cryptographic"] = "fisher_yates"


class DealerConfig(BaseModel):
    """Configuration for dealer card handling.

    In some casino variations, the dealer takes cards and discards before
    dealing to players. This affects the composition of cards available
    for player hands.

    Attributes:
        discard_enabled: Enable dealer discard before player deal.
        discard_cards: Number of cards dealer discards before player deal.
    """

    model_config = ConfigDict(extra="forbid")

    discard_enabled: bool = False
    discard_cards: Annotated[int, Field(ge=1, le=10)] = 3


class TableConfig(BaseModel):
    """Configuration for table settings.

    Controls the number of player seats at the table.
    A standard Let It Ride table can accommodate 1-6 players.

    Attributes:
        num_seats: Number of player positions at the table (1-6).
    """

    model_config = ConfigDict(extra="forbid")

    num_seats: Annotated[int, Field(ge=1, le=6)] = 1


class StopConditionsConfig(BaseModel):
    """Configuration for session stop conditions.

    A session ends when any configured condition is met.

    Attributes:
        win_limit: Stop when profit reaches this amount.
        loss_limit: Stop when loss reaches this amount.
        max_hands: Stop after this many hands.
        max_duration_minutes: Stop after this duration (simulated).
        stop_on_insufficient_funds: Stop if bankroll < minimum bet.
    """

    model_config = ConfigDict(extra="forbid")

    win_limit: Annotated[float, Field(gt=0)] | None = None
    loss_limit: Annotated[float, Field(gt=0)] | None = None
    max_hands: Annotated[int, Field(ge=1)] | None = None
    max_duration_minutes: Annotated[int, Field(ge=1)] | None = None
    stop_on_insufficient_funds: bool = True


class ProportionalBettingConfig(BaseModel):
    """Configuration for proportional betting system.

    Bet a percentage of current bankroll each hand.

    Attributes:
        bankroll_percentage: Fraction of bankroll to bet (0.001-0.50).
        min_bet: Minimum bet floor.
        max_bet: Maximum bet ceiling.
        round_to: Round bets to nearest increment.
    """

    model_config = ConfigDict(extra="forbid")

    bankroll_percentage: Annotated[float, Field(ge=0.001, le=0.50)] = 0.03
    min_bet: Annotated[float, Field(gt=0)] = 5.0
    max_bet: Annotated[float, Field(gt=0)] = 100.0
    round_to: Annotated[float, Field(gt=0)] = 1.0

    @model_validator(mode="after")
    def validate_bet_limits(self) -> ProportionalBettingConfig:
        """Validate that min_bet does not exceed max_bet."""
        if self.min_bet > self.max_bet:
            raise ValueError("min_bet cannot exceed max_bet")
        return self


class MartingaleBettingConfig(BaseModel):
    """Configuration for Martingale betting system.

    Double bet after losses, reset after wins.

    Attributes:
        loss_multiplier: Multiplier applied after loss.
        reset_on_win: Reset to base bet after win.
        max_bet: Maximum bet cap (table limit).
        max_progressions: Maximum consecutive progressions.
    """

    model_config = ConfigDict(extra="forbid")

    loss_multiplier: Annotated[float, Field(gt=1)] = 2.0
    reset_on_win: bool = True
    max_bet: Annotated[float, Field(gt=0)] = 500.0
    max_progressions: Annotated[int, Field(ge=1)] = 6


class ReverseMartingaleBettingConfig(BaseModel):
    """Configuration for Reverse Martingale (Parlay) betting system.

    Increase bet after wins, reset after losses.

    Attributes:
        win_multiplier: Multiplier applied after win.
        reset_on_loss: Reset to base bet after loss.
        profit_target_streak: Take profit after N consecutive wins.
        max_bet: Maximum bet cap.
    """

    model_config = ConfigDict(extra="forbid")

    win_multiplier: Annotated[float, Field(gt=1)] = 2.0
    reset_on_loss: bool = True
    profit_target_streak: Annotated[int, Field(ge=1)] = 3
    max_bet: Annotated[float, Field(gt=0)] = 500.0


class ParoliBettingConfig(BaseModel):
    """Configuration for Paroli betting system.

    Increase bet after wins for a fixed number of wins.

    Attributes:
        win_multiplier: Multiplier applied after win.
        wins_before_reset: Number of wins before resetting.
        max_bet: Maximum bet cap.
    """

    model_config = ConfigDict(extra="forbid")

    win_multiplier: Annotated[float, Field(gt=1)] = 2.0
    wins_before_reset: Annotated[int, Field(ge=1)] = 3
    max_bet: Annotated[float, Field(gt=0)] = 500.0


class DAlembertBettingConfig(BaseModel):
    """Configuration for D'Alembert betting system.

    Increase bet by unit after loss, decrease after win.

    Attributes:
        unit: Unit to add after loss.
        decrease_unit: Unit to subtract after win.
        min_bet: Minimum bet floor.
        max_bet: Maximum bet ceiling.
    """

    model_config = ConfigDict(extra="forbid")

    unit: Annotated[float, Field(gt=0)] = 5.0
    decrease_unit: Annotated[float, Field(gt=0)] = 5.0
    min_bet: Annotated[float, Field(gt=0)] = 5.0
    max_bet: Annotated[float, Field(gt=0)] = 500.0

    @model_validator(mode="after")
    def validate_bet_limits(self) -> DAlembertBettingConfig:
        """Validate that min_bet does not exceed max_bet."""
        if self.min_bet > self.max_bet:
            raise ValueError("min_bet cannot exceed max_bet")
        return self


class FibonacciBettingConfig(BaseModel):
    """Configuration for Fibonacci betting system.

    Follow Fibonacci sequence for bet progression.

    Attributes:
        unit: Base unit for sequence.
        win_regression: Move back N positions after win.
        max_bet: Maximum bet cap.
        max_position: Maximum sequence position.
    """

    model_config = ConfigDict(extra="forbid")

    unit: Annotated[float, Field(gt=0)] = 5.0
    win_regression: Annotated[int, Field(ge=1)] = 2
    max_bet: Annotated[float, Field(gt=0)] = 500.0
    max_position: Annotated[int, Field(ge=1)] = 10


class CustomBettingConfig(BaseModel):
    """Configuration for custom betting system.

    Use a Python expression for bet sizing.

    Attributes:
        expression: Python expression returning bet amount.
            Available variables: bankroll, base_bet, last_result,
            streak, session_profit, hands_played.
        min_bet: Minimum bet floor.
        max_bet: Maximum bet ceiling.
    """

    model_config = ConfigDict(extra="forbid")

    expression: str = "base_bet"
    min_bet: Annotated[float, Field(gt=0)] = 5.0
    max_bet: Annotated[float, Field(gt=0)] = 500.0

    @model_validator(mode="after")
    def validate_bet_limits(self) -> CustomBettingConfig:
        """Validate that min_bet does not exceed max_bet."""
        if self.min_bet > self.max_bet:
            raise ValueError("min_bet cannot exceed max_bet")
        return self


class BettingSystemConfig(BaseModel):
    """Configuration for betting progression system.

    Attributes:
        type: The betting system type.
        proportional: Config for proportional betting.
        martingale: Config for Martingale betting.
        reverse_martingale: Config for Reverse Martingale.
        paroli: Config for Paroli betting.
        dalembert: Config for D'Alembert betting.
        fibonacci: Config for Fibonacci betting.
        custom: Config for custom betting expression.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "flat",
        "proportional",
        "martingale",
        "reverse_martingale",
        "paroli",
        "dalembert",
        "fibonacci",
        "custom",
    ] = "flat"

    proportional: ProportionalBettingConfig | None = None
    martingale: MartingaleBettingConfig | None = None
    reverse_martingale: ReverseMartingaleBettingConfig | None = None
    paroli: ParoliBettingConfig | None = None
    dalembert: DAlembertBettingConfig | None = None
    fibonacci: FibonacciBettingConfig | None = None
    custom: CustomBettingConfig | None = None

    @model_validator(mode="after")
    def validate_type_config_match(self) -> BettingSystemConfig:
        """Validate that required config is provided for non-flat betting types."""
        type_to_config = {
            "proportional": self.proportional,
            "martingale": self.martingale,
            "reverse_martingale": self.reverse_martingale,
            "paroli": self.paroli,
            "dalembert": self.dalembert,
            "fibonacci": self.fibonacci,
            "custom": self.custom,
        }
        if self.type in type_to_config and type_to_config[self.type] is None:
            raise ValueError(
                f"'{self.type}' betting system requires '{self.type}' config"
            )
        return self


class BankrollConfig(BaseModel):
    """Configuration for bankroll management.

    Attributes:
        starting_amount: Initial bankroll in dollars.
        base_bet: Base bet amount per betting circle.
            Total initial wager = base_bet * 3.
        stop_conditions: Session stop conditions.
        betting_system: Betting progression configuration.
    """

    model_config = ConfigDict(extra="forbid")

    starting_amount: Annotated[float, Field(gt=0)] = 500.0
    base_bet: Annotated[float, Field(gt=0)] = 5.0
    stop_conditions: StopConditionsConfig = Field(default_factory=StopConditionsConfig)
    betting_system: BettingSystemConfig = Field(default_factory=BettingSystemConfig)

    @model_validator(mode="after")
    def validate_bet_vs_bankroll(self) -> BankrollConfig:
        """Validate that base bet doesn't exceed starting bankroll."""
        min_required = self.base_bet * 3  # Need 3 betting circles
        if self.starting_amount < min_required:
            raise ValueError(
                f"starting_amount ({self.starting_amount}) must be at least "
                f"3x base_bet ({min_required}) for initial wager"
            )
        return self


class ConservativeStrategyConfig(BaseModel):
    """Configuration for conservative strategy.

    Attributes:
        made_hands_only: Only let it ride with made paying hands.
        min_strength_bet1: Minimum hand strength for Bet 1 (1-10 scale).
        min_strength_bet2: Minimum hand strength for Bet 2 (1-10 scale).
    """

    model_config = ConfigDict(extra="forbid")

    made_hands_only: bool = True
    min_strength_bet1: Annotated[int, Field(ge=1, le=10)] = 7
    min_strength_bet2: Annotated[int, Field(ge=1, le=10)] = 5


class AggressiveStrategyConfig(BaseModel):
    """Configuration for aggressive strategy.

    Attributes:
        ride_on_draws: Let it ride with any draw.
        include_gutshots: Include inside straight draws.
        include_backdoor_flush: Include backdoor flush draws.
    """

    model_config = ConfigDict(extra="forbid")

    ride_on_draws: bool = True
    include_gutshots: bool = True
    include_backdoor_flush: bool = True


class StrategyRule(BaseModel):
    """A single strategy rule.

    Attributes:
        condition: Condition expression to evaluate.
        action: Action to take if condition matches.
    """

    model_config = ConfigDict(extra="forbid")

    condition: str
    action: Literal["ride", "pull"]


class CustomStrategyConfig(BaseModel):
    """Configuration for custom strategy rules.

    Attributes:
        bet1_rules: Rules for Bet 1 decision.
        bet2_rules: Rules for Bet 2 decision.
    """

    model_config = ConfigDict(extra="forbid")

    bet1_rules: list[StrategyRule] = Field(default_factory=list)
    bet2_rules: list[StrategyRule] = Field(default_factory=list)


class StrategyConfig(BaseModel):
    """Configuration for main game strategy.

    Attributes:
        type: Strategy type selection.
        conservative: Config for conservative strategy.
        aggressive: Config for aggressive strategy.
        custom: Config for custom strategy rules.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "basic",
        "always_ride",
        "always_pull",
        "conservative",
        "aggressive",
        "custom",
    ] = "basic"

    conservative: ConservativeStrategyConfig | None = None
    aggressive: AggressiveStrategyConfig | None = None
    custom: CustomStrategyConfig | None = None

    @model_validator(mode="after")
    def validate_type_config_match(self) -> StrategyConfig:
        """Validate that required config is provided for strategies that need it."""
        type_to_config = {
            "conservative": self.conservative,
            "aggressive": self.aggressive,
            "custom": self.custom,
        }
        if self.type in type_to_config and type_to_config[self.type] is None:
            raise ValueError(
                f"'{self.type}' strategy requires '{self.type}' config section"
            )
        return self


class BonusLimitsConfig(BaseModel):
    """Configuration for bonus bet limits.

    Attributes:
        min_bet: Minimum bonus bet.
        max_bet: Maximum bonus bet (table limit).
        increment: Bet increment.
    """

    model_config = ConfigDict(extra="forbid")

    min_bet: Annotated[float, Field(ge=0)] = 1.0
    max_bet: Annotated[float, Field(gt=0)] = 25.0
    increment: Annotated[float, Field(gt=0)] = 1.0

    @model_validator(mode="after")
    def validate_bet_limits(self) -> BonusLimitsConfig:
        """Validate that min_bet does not exceed max_bet."""
        if self.min_bet > self.max_bet:
            raise ValueError("min_bet cannot exceed max_bet")
        return self


class AlwaysBonusConfig(BaseModel):
    """Configuration for always bonus betting.

    Attributes:
        amount: Fixed bet amount.
    """

    model_config = ConfigDict(extra="forbid")

    amount: Annotated[float, Field(gt=0)] = 1.0


class StaticBonusConfig(BaseModel):
    """Configuration for static bonus betting.

    Attributes:
        amount: Fixed amount (mutually exclusive with ratio).
        ratio: Ratio of base bet (mutually exclusive with amount).
    """

    model_config = ConfigDict(extra="forbid")

    amount: Annotated[float, Field(gt=0)] | None = 1.0
    ratio: Annotated[float, Field(gt=0, le=1.0)] | None = None

    @model_validator(mode="after")
    def validate_amount_or_ratio(self) -> StaticBonusConfig:
        """Ensure amount or ratio is set, not both."""
        if self.amount is not None and self.ratio is not None:
            raise ValueError("Specify either amount or ratio, not both")
        if self.amount is None and self.ratio is None:
            raise ValueError("Must specify either amount or ratio")
        return self


class ProfitTier(BaseModel):
    """A profit tier for scaled bonus betting.

    Attributes:
        min_profit: Minimum profit for this tier.
        max_profit: Maximum profit for this tier (None = no limit).
        bet_amount: Bet amount for this tier.
    """

    model_config = ConfigDict(extra="forbid")

    min_profit: float = 0
    max_profit: float | None = None
    bet_amount: Annotated[float, Field(ge=0)] = 1.0

    @model_validator(mode="after")
    def validate_tier_range(self) -> ProfitTier:
        """Validate that min_profit is less than max_profit when max_profit is set."""
        if self.max_profit is not None and self.min_profit >= self.max_profit:
            raise ValueError("min_profit must be less than max_profit")
        return self


class ScalingConfig(BaseModel):
    """Configuration for profit-based bonus scaling.

    Attributes:
        enabled: Enable profit-based scaling.
        tiers: Profit tiers and corresponding bet amounts.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    tiers: list[ProfitTier] = Field(default_factory=list)


class BankrollConditionalBonusConfig(BaseModel):
    """Configuration for bankroll-conditional bonus betting.

    Attributes:
        base_amount: Base bonus bet amount when conditions met.
        min_session_profit: Only bet when session profit exceeds this.
        min_bankroll_ratio: Only bet when bankroll ratio exceeds this.
        profit_percentage: Bet percentage of profits instead of fixed.
        max_drawdown: Stop bonus betting after this drawdown percentage.
        scaling: Profit-based scaling configuration.
    """

    model_config = ConfigDict(extra="forbid")

    base_amount: Annotated[float, Field(gt=0)] = 1.0
    min_session_profit: float | None = 0.0
    min_bankroll_ratio: Annotated[float, Field(gt=0, le=1.0)] | None = None
    profit_percentage: Annotated[float, Field(gt=0, le=1.0)] | None = None
    max_drawdown: Annotated[float, Field(gt=0, le=1.0)] | None = 0.25
    scaling: ScalingConfig = Field(default_factory=ScalingConfig)


class StreakActionConfig(BaseModel):
    """Configuration for streak-triggered action.

    Attributes:
        type: Type of adjustment.
        value: Value for adjustment.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["increase", "decrease", "stop", "start", "multiply"] = "multiply"
    value: float = 2.0


class StreakBasedBonusConfig(BaseModel):
    """Configuration for streak-based bonus betting.

    Attributes:
        base_amount: Base bonus bet amount.
        trigger: Event type to trigger adjustment.
        streak_length: Consecutive events to trigger.
        action: Action when streak triggers.
        reset_on: Event to reset streak counter.
        max_multiplier: Cap on streak multiplier.
    """

    model_config = ConfigDict(extra="forbid")

    base_amount: Annotated[float, Field(gt=0)] = 1.0
    trigger: Literal[
        "main_loss",
        "main_win",
        "bonus_loss",
        "bonus_win",
        "any_loss",
        "any_win",
    ] = "bonus_loss"
    streak_length: Annotated[int, Field(ge=1)] = 5
    action: StreakActionConfig = Field(default_factory=StreakActionConfig)
    reset_on: Literal[
        "bonus_win",
        "bonus_loss",
        "main_win",
        "main_loss",
        "any_win",
        "any_loss",
        "never",
    ] = "bonus_win"
    max_multiplier: Annotated[float, Field(ge=1)] | None = 5.0


class EarlySessionConfig(BaseModel):
    """Configuration for early session bonus behavior.

    Attributes:
        hands: Number of hands considered early.
        amount: Bet amount during early session.
    """

    model_config = ConfigDict(extra="forbid")

    hands: Annotated[int, Field(ge=1)] = 20
    amount: Annotated[float, Field(ge=0)] = 1.0


class NearLimitConfig(BaseModel):
    """Configuration for near-limit bonus behavior.

    Attributes:
        threshold: Distance from limit to trigger.
        amount: Bet amount near limit.
    """

    model_config = ConfigDict(extra="forbid")

    threshold: Annotated[float, Field(gt=0)] = 50.0
    amount: Annotated[float, Field(ge=0)] = 5.0


class DefaultAmountConfig(BaseModel):
    """Configuration for default bonus amount.

    Attributes:
        amount: Default bet amount.
    """

    model_config = ConfigDict(extra="forbid")

    amount: Annotated[float, Field(ge=0)] = 1.0


class SessionConditionsConfig(BaseModel):
    """Configuration for session-conditional bonus behavior.

    Attributes:
        early_session: Early session configuration.
        near_win_limit: Near win limit configuration.
        near_loss_limit: Near loss limit configuration.
        default: Default configuration.
    """

    model_config = ConfigDict(extra="forbid")

    early_session: EarlySessionConfig = Field(default_factory=EarlySessionConfig)
    near_win_limit: NearLimitConfig = Field(
        default_factory=lambda: NearLimitConfig(threshold=50.0, amount=5.0)
    )
    near_loss_limit: NearLimitConfig = Field(
        default_factory=lambda: NearLimitConfig(threshold=50.0, amount=0.0)
    )
    default: DefaultAmountConfig = Field(default_factory=DefaultAmountConfig)


class SessionConditionalBonusConfig(BaseModel):
    """Configuration for session-conditional bonus betting.

    Attributes:
        base_amount: Base bonus bet amount.
        conditions: Session conditions configuration.
    """

    model_config = ConfigDict(extra="forbid")

    base_amount: Annotated[float, Field(gt=0)] = 1.0
    conditions: SessionConditionsConfig = Field(default_factory=SessionConditionsConfig)


class RideCorrelationConfig(BaseModel):
    """Configuration for ride correlation bonus adjustment.

    Attributes:
        enabled: Enable correlation with ride decisions.
        both_ride_multiplier: Multiplier when letting both bets ride.
        one_ride_multiplier: Multiplier when letting one bet ride.
        both_pull_multiplier: Multiplier when pulling both bets.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    both_ride_multiplier: Annotated[float, Field(gt=0)] = 2.0
    one_ride_multiplier: Annotated[float, Field(gt=0)] = 1.5
    both_pull_multiplier: Annotated[float, Field(gt=0)] = 0.5


class HandQualityConfig(BaseModel):
    """Configuration for hand quality bonus adjustment.

    Attributes:
        enabled: Enable hand quality adjustment.
        strong_hand_multiplier: Multiplier for strong hands.
        weak_hand_multiplier: Multiplier for weak hands.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    strong_hand_multiplier: Annotated[float, Field(gt=0)] = 1.5
    weak_hand_multiplier: Annotated[float, Field(gt=0)] = 0.5


class CombinedBonusConfig(BaseModel):
    """Configuration for combined bonus strategy.

    Attributes:
        base_amount: Base bonus bet amount.
        ride_correlation: Ride correlation configuration.
        hand_quality_adjustment: Hand quality adjustment configuration.
    """

    model_config = ConfigDict(extra="forbid")

    base_amount: Annotated[float, Field(gt=0)] = 1.0
    ride_correlation: RideCorrelationConfig = Field(
        default_factory=RideCorrelationConfig
    )
    hand_quality_adjustment: HandQualityConfig = Field(
        default_factory=HandQualityConfig
    )


class CustomBonusStrategyConfig(BaseModel):
    """Configuration for custom bonus betting logic.

    Attributes:
        expression: Python expression for bonus bet.
        min_bet: Minimum bet floor.
        max_bet: Maximum bet ceiling.
    """

    model_config = ConfigDict(extra="forbid")

    expression: str = "1.0 if session_profit > 0 else 0.0"
    min_bet: Annotated[float, Field(ge=0)] = 0.0
    max_bet: Annotated[float, Field(gt=0)] = 25.0

    @model_validator(mode="after")
    def validate_bet_limits(self) -> CustomBonusStrategyConfig:
        """Validate that min_bet does not exceed max_bet."""
        if self.min_bet > self.max_bet:
            raise ValueError("min_bet cannot exceed max_bet")
        return self


class BonusStrategyConfig(BaseModel):
    """Configuration for three-card bonus strategy.

    Attributes:
        enabled: Enable/disable bonus betting.
        paytable: Paytable selection.
        limits: Bonus bet limits.
        type: Strategy type selection.
        always: Config for always bonus betting.
        static: Config for static bonus betting.
        bankroll_conditional: Config for bankroll-conditional betting.
        streak_based: Config for streak-based betting.
        session_conditional: Config for session-conditional betting.
        combined: Config for combined strategy.
        custom: Config for custom bonus betting.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    paytable: Literal["paytable_a", "paytable_b", "paytable_c", "custom"] = "paytable_b"
    limits: BonusLimitsConfig = Field(default_factory=BonusLimitsConfig)
    type: Literal[
        "never",
        "always",
        "static",
        "bankroll_conditional",
        "streak_based",
        "session_conditional",
        "combined",
        "custom",
    ] = "never"

    always: AlwaysBonusConfig | None = None
    static: StaticBonusConfig | None = None
    bankroll_conditional: BankrollConditionalBonusConfig | None = None
    streak_based: StreakBasedBonusConfig | None = None
    session_conditional: SessionConditionalBonusConfig | None = None
    combined: CombinedBonusConfig | None = None
    custom: CustomBonusStrategyConfig | None = None

    @model_validator(mode="after")
    def validate_type_config_match(self) -> BonusStrategyConfig:
        """Validate that required config is provided for bonus strategies that need it."""
        type_to_config = {
            "always": self.always,
            "static": self.static,
            "bankroll_conditional": self.bankroll_conditional,
            "streak_based": self.streak_based,
            "session_conditional": self.session_conditional,
            "combined": self.combined,
            "custom": self.custom,
        }
        if self.type in type_to_config and type_to_config[self.type] is None:
            raise ValueError(
                f"'{self.type}' bonus strategy requires '{self.type}' config section"
            )
        return self


class CustomMainPaytableConfig(BaseModel):
    """Custom paytable for main game.

    Attributes:
        royal_flush: Payout for royal flush.
        straight_flush: Payout for straight flush.
        four_of_a_kind: Payout for four of a kind.
        full_house: Payout for full house.
        flush: Payout for flush.
        straight: Payout for straight.
        three_of_a_kind: Payout for three of a kind.
        two_pair: Payout for two pair.
        pair_tens_or_better: Payout for pair of tens or better.
    """

    model_config = ConfigDict(extra="forbid")

    royal_flush: Annotated[int, Field(ge=0)] = 1000
    straight_flush: Annotated[int, Field(ge=0)] = 200
    four_of_a_kind: Annotated[int, Field(ge=0)] = 50
    full_house: Annotated[int, Field(ge=0)] = 11
    flush: Annotated[int, Field(ge=0)] = 8
    straight: Annotated[int, Field(ge=0)] = 5
    three_of_a_kind: Annotated[int, Field(ge=0)] = 3
    two_pair: Annotated[int, Field(ge=0)] = 2
    pair_tens_or_better: Annotated[int, Field(ge=0)] = 1


class MainGamePaytableConfig(BaseModel):
    """Configuration for main game paytable.

    Attributes:
        type: Paytable type selection.
        custom: Custom paytable definition.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["standard", "liberal", "tight", "custom"] = "standard"
    custom: CustomMainPaytableConfig | None = None


class CustomBonusPaytableConfig(BaseModel):
    """Custom paytable for bonus bet.

    Attributes:
        mini_royal: Payout for mini royal.
        straight_flush: Payout for straight flush.
        three_of_a_kind: Payout for three of a kind.
        straight: Payout for straight.
        flush: Payout for flush.
        pair: Payout for pair.
    """

    model_config = ConfigDict(extra="forbid")

    mini_royal: Annotated[int, Field(ge=0)] = 100
    straight_flush: Annotated[int, Field(ge=0)] = 40
    three_of_a_kind: Annotated[int, Field(ge=0)] = 30
    straight: Annotated[int, Field(ge=0)] = 5
    flush: Annotated[int, Field(ge=0)] = 4
    pair: Annotated[int, Field(ge=0)] = 1


class ProgressiveJackpotConfig(BaseModel):
    """Configuration for progressive jackpot.

    Attributes:
        starting_jackpot: Starting jackpot amount.
        contribution_rate: Contribution per bonus bet.
        trigger: Hand that triggers jackpot.
        reset_amount: Amount after jackpot hit.
    """

    model_config = ConfigDict(extra="forbid")

    starting_jackpot: Annotated[float, Field(gt=0)] = 10000.0
    contribution_rate: Annotated[float, Field(gt=0, le=1.0)] = 0.15
    trigger: Literal["mini_royal"] = "mini_royal"
    reset_amount: Annotated[float, Field(gt=0)] = 10000.0


class BonusPaytableConfig(BaseModel):
    """Configuration for bonus paytable.

    Attributes:
        type: Paytable type selection.
        custom: Custom paytable definition.
        progressive: Progressive jackpot configuration.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["paytable_a", "paytable_b", "paytable_c", "custom"] = "paytable_b"
    custom: CustomBonusPaytableConfig | None = None
    progressive: ProgressiveJackpotConfig | None = None


class PaytablesConfig(BaseModel):
    """Configuration for game paytables.

    Attributes:
        main_game: Main game paytable configuration.
        bonus: Bonus paytable configuration.
    """

    model_config = ConfigDict(extra="forbid")

    main_game: MainGamePaytableConfig = Field(default_factory=MainGamePaytableConfig)
    bonus: BonusPaytableConfig = Field(default_factory=BonusPaytableConfig)


class CsvOutputConfig(BaseModel):
    """Configuration for CSV output.

    Attributes:
        enabled: Enable CSV export.
        include_hands: Include per-hand details.
        include_sessions: Include per-session summaries.
        include_aggregate: Include aggregate statistics.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    include_hands: bool = False
    include_sessions: bool = True
    include_aggregate: bool = True


class JsonOutputConfig(BaseModel):
    """Configuration for JSON output.

    Attributes:
        enabled: Enable JSON export.
        pretty: Pretty print JSON.
        include_config: Include configuration in output.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    pretty: bool = True
    include_config: bool = True


class HtmlOutputConfig(BaseModel):
    """Configuration for HTML report output.

    Attributes:
        enabled: Enable HTML export.
        include_charts: Include visualizations.
        chart_library: Chart library to use.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    include_charts: bool = True
    chart_library: Literal["plotly", "matplotlib"] = "plotly"


class OutputFormatsConfig(BaseModel):
    """Configuration for output formats.

    Attributes:
        csv: CSV output configuration.
        json_output: JSON output configuration (YAML key: "json").
        html: HTML output configuration.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    csv: CsvOutputConfig = Field(default_factory=CsvOutputConfig)
    json_output: JsonOutputConfig = Field(
        default_factory=JsonOutputConfig, alias="json"
    )
    html: HtmlOutputConfig = Field(default_factory=HtmlOutputConfig)


class ChartConfig(BaseModel):
    """Configuration for a single chart.

    Attributes:
        type: Chart type.
        title: Chart title.
        sample_sessions: Number of sample sessions (for trajectory charts).
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "session_outcomes_histogram",
        "bankroll_trajectory",
        "hand_frequency",
        "strategy_comparison",
        "bonus_impact",
    ]
    title: str
    sample_sessions: Annotated[int, Field(ge=1)] | None = None


class VisualizationsConfig(BaseModel):
    """Configuration for visualizations.

    Attributes:
        enabled: Enable visualization generation.
        charts: List of charts to generate.
        format: Output format for charts.
        dpi: Resolution for raster formats.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    charts: list[ChartConfig] = Field(default_factory=list)
    format: Literal["png", "svg", "html"] = "png"
    dpi: Annotated[int, Field(ge=72, le=600)] = 150


class ConsoleOutputConfig(BaseModel):
    """Configuration for console output.

    Attributes:
        progress_bar: Show progress bar.
        verbosity: Verbosity level (0-3).
        show_summary: Show summary statistics.
    """

    model_config = ConfigDict(extra="forbid")

    progress_bar: bool = True
    verbosity: Annotated[int, Field(ge=0, le=3)] = 1
    show_summary: bool = True


class OutputConfig(BaseModel):
    """Configuration for output and reporting.

    Attributes:
        directory: Output directory for results.
        prefix: Filename prefix.
        timestamp_format: Timestamp format for filenames.
        formats: Output format configurations.
        visualizations: Visualization configurations.
        console: Console output configurations.
    """

    model_config = ConfigDict(extra="forbid")

    directory: str = "./results"
    prefix: str = "simulation"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    formats: OutputFormatsConfig = Field(default_factory=OutputFormatsConfig)
    visualizations: VisualizationsConfig = Field(default_factory=VisualizationsConfig)
    console: ConsoleOutputConfig = Field(default_factory=ConsoleOutputConfig)


class FullConfig(BaseModel):
    """Root configuration model for Let It Ride simulation.

    This model represents the complete configuration file structure.
    All sections have sensible defaults, so a minimal configuration
    file can be used.

    Attributes:
        metadata: Optional metadata about the configuration.
        simulation: Simulation run parameters.
        deck: Deck handling configuration.
        dealer: Dealer card handling configuration.
        bankroll: Bankroll management configuration.
        strategy: Main game strategy configuration.
        bonus_strategy: Bonus betting strategy configuration.
        paytables: Paytable configuration.
        output: Output and reporting configuration.
    """

    model_config = ConfigDict(extra="forbid")

    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    deck: DeckConfig = Field(default_factory=DeckConfig)
    dealer: DealerConfig = Field(default_factory=DealerConfig)
    bankroll: BankrollConfig = Field(default_factory=BankrollConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    bonus_strategy: BonusStrategyConfig = Field(default_factory=BonusStrategyConfig)
    paytables: PaytablesConfig = Field(default_factory=PaytablesConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
