"""Simulation controller for running multiple sessions.

This module provides the main simulation controller for orchestrating
the execution of multiple Let It Ride sessions sequentially.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from let_it_ride.bankroll import (
    BettingSystem,
    DAlembertBetting,
    FibonacciBetting,
    FlatBetting,
    MartingaleBetting,
    ParoliBetting,
    ReverseMartingaleBetting,
)
from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_a,
    bonus_paytable_b,
    bonus_paytable_c,
    standard_main_paytable,
)
from let_it_ride.core.deck import Deck
from let_it_ride.core.game_engine import GameEngine
from let_it_ride.simulation.session import Session, SessionConfig, SessionResult
from let_it_ride.strategy import (
    AlwaysPullStrategy,
    AlwaysRideStrategy,
    BasicStrategy,
    CustomStrategy,
    Strategy,
    StrategyRule,
    aggressive_strategy,
    conservative_strategy,
)
from let_it_ride.strategy.base import Decision

if TYPE_CHECKING:
    from let_it_ride.config.models import (
        BankrollConfig,
        FullConfig,
        StrategyConfig,
    )

# Type alias for progress callback
ProgressCallback = Callable[[int, int], None]


def _action_to_decision(action: str) -> Decision:
    """Convert action string to Decision enum.

    Args:
        action: Action string ("ride" or "pull").

    Returns:
        Decision.RIDE or Decision.PULL.
    """
    return Decision.RIDE if action == "ride" else Decision.PULL


def _create_custom_strategy(config: StrategyConfig) -> Strategy:
    """Create a custom strategy from configuration.

    Args:
        config: The strategy configuration with custom rules.

    Returns:
        A CustomStrategy instance configured with the provided rules.

    Raises:
        ValueError: If custom config section is missing.
    """
    if config.custom is None:
        raise ValueError("'custom' strategy requires 'custom' config section")
    # Convert config rules to StrategyRule instances
    # Config uses "ride"/"pull" strings, StrategyRule needs Decision enum
    bet1_rules = [
        StrategyRule(condition=rule.condition, action=_action_to_decision(rule.action))
        for rule in config.custom.bet1_rules
    ]
    bet2_rules = [
        StrategyRule(condition=rule.condition, action=_action_to_decision(rule.action))
        for rule in config.custom.bet2_rules
    ]
    return CustomStrategy(bet1_rules=bet1_rules, bet2_rules=bet2_rules)


# Strategy factory registry mapping type names to factory functions.
# Each factory takes a StrategyConfig and returns a Strategy instance.
_STRATEGY_FACTORIES: dict[str, Callable[[StrategyConfig], Strategy]] = {
    "basic": lambda _: BasicStrategy(),
    "always_ride": lambda _: AlwaysRideStrategy(),
    "always_pull": lambda _: AlwaysPullStrategy(),
    "conservative": lambda _: conservative_strategy(),
    "aggressive": lambda _: aggressive_strategy(),
    "custom": _create_custom_strategy,
}


@dataclass(frozen=True, slots=True)
class SimulationResults:
    """Complete results from a simulation run.

    Attributes:
        config: The configuration used for this simulation.
        session_results: List of results from each session.
        start_time: When the simulation started.
        end_time: When the simulation completed.
        total_hands: Total number of hands played across all sessions.
    """

    config: FullConfig
    session_results: list[SessionResult]
    start_time: datetime
    end_time: datetime
    total_hands: int


def create_strategy(config: StrategyConfig) -> Strategy:
    """Create a strategy instance from configuration.

    Args:
        config: The strategy configuration.

    Returns:
        An instance of the appropriate Strategy implementation.

    Raises:
        ValueError: If the strategy type is unknown or if custom strategy
            is requested without the required configuration section.
    """
    factory = _STRATEGY_FACTORIES.get(config.type)
    if factory is None:
        raise ValueError(f"Unknown strategy type: {config.type}")
    return factory(config)


def _create_flat_betting(config: BankrollConfig) -> BettingSystem:
    """Create flat betting system."""
    return FlatBetting(base_bet=config.base_bet)


def _create_martingale_betting(config: BankrollConfig) -> BettingSystem:
    """Create martingale betting system."""
    if config.betting_system.martingale is None:
        raise ValueError("'martingale' betting requires 'martingale' config")
    mc = config.betting_system.martingale
    return MartingaleBetting(
        base_bet=config.base_bet,
        loss_multiplier=mc.loss_multiplier,
        max_bet=mc.max_bet,
        max_progressions=mc.max_progressions,
    )


def _create_reverse_martingale_betting(config: BankrollConfig) -> BettingSystem:
    """Create reverse martingale betting system."""
    if config.betting_system.reverse_martingale is None:
        raise ValueError(
            "'reverse_martingale' betting requires 'reverse_martingale' config"
        )
    rmc = config.betting_system.reverse_martingale
    return ReverseMartingaleBetting(
        base_bet=config.base_bet,
        win_multiplier=rmc.win_multiplier,
        max_bet=rmc.max_bet,
        profit_target_streak=rmc.profit_target_streak,
    )


def _create_paroli_betting(config: BankrollConfig) -> BettingSystem:
    """Create Paroli betting system."""
    if config.betting_system.paroli is None:
        raise ValueError("'paroli' betting requires 'paroli' config")
    pc = config.betting_system.paroli
    return ParoliBetting(
        base_bet=config.base_bet,
        win_multiplier=pc.win_multiplier,
        max_bet=pc.max_bet,
        wins_before_reset=pc.wins_before_reset,
    )


def _create_dalembert_betting(config: BankrollConfig) -> BettingSystem:
    """Create D'Alembert betting system."""
    if config.betting_system.dalembert is None:
        raise ValueError("'dalembert' betting requires 'dalembert' config")
    dc = config.betting_system.dalembert
    return DAlembertBetting(
        base_bet=config.base_bet,
        unit=dc.unit,
        min_bet=dc.min_bet,
        max_bet=dc.max_bet,
    )


def _create_fibonacci_betting(config: BankrollConfig) -> BettingSystem:
    """Create Fibonacci betting system."""
    if config.betting_system.fibonacci is None:
        raise ValueError("'fibonacci' betting requires 'fibonacci' config")
    fc = config.betting_system.fibonacci
    return FibonacciBetting(
        base_unit=fc.unit,
        max_bet=fc.max_bet,
        max_position=fc.max_position,
        win_regression=fc.win_regression,
    )


# Betting system factory registry mapping type names to factory functions.
# Each factory takes a BankrollConfig and returns a BettingSystem instance.
# None values indicate types that are not yet implemented.
_BETTING_SYSTEM_FACTORIES: dict[
    str, Callable[[BankrollConfig], BettingSystem] | None
] = {
    "flat": _create_flat_betting,
    "martingale": _create_martingale_betting,
    "reverse_martingale": _create_reverse_martingale_betting,
    "paroli": _create_paroli_betting,
    "dalembert": _create_dalembert_betting,
    "fibonacci": _create_fibonacci_betting,
    "proportional": None,  # Not yet implemented
    "custom": None,  # Not yet implemented
}


def create_betting_system(config: BankrollConfig) -> BettingSystem:
    """Create a betting system instance from configuration.

    Args:
        config: The bankroll configuration containing betting system settings.

    Returns:
        An instance of the appropriate BettingSystem implementation.

    Raises:
        ValueError: If the betting system type is unknown.
        NotImplementedError: If the betting system type is not yet implemented.
    """
    system_type = config.betting_system.type
    if system_type not in _BETTING_SYSTEM_FACTORIES:
        raise ValueError(f"Unknown betting system type: {system_type}")

    factory = _BETTING_SYSTEM_FACTORIES[system_type]
    if factory is None:
        raise NotImplementedError(
            f"Betting system type '{system_type}' is not yet implemented"
        )
    return factory(config)


def _get_main_paytable(config: FullConfig) -> MainGamePaytable:
    """Get the main game paytable from configuration.

    Args:
        config: The full simulation configuration.

    Returns:
        The appropriate MainGamePaytable instance.

    Raises:
        NotImplementedError: If the paytable type is not yet supported.
    """
    paytable_type = config.paytables.main_game.type
    if paytable_type == "standard":
        return standard_main_paytable()
    # liberal, tight, and custom paytables not yet implemented
    raise NotImplementedError(
        f"Main paytable type '{paytable_type}' is not yet implemented. "
        "Only 'standard' is currently supported."
    )


def _get_bonus_paytable(config: FullConfig) -> BonusPaytable | None:
    """Get the bonus paytable from configuration.

    Args:
        config: The full simulation configuration.

    Returns:
        The appropriate BonusPaytable instance, or None if bonus is disabled.

    Raises:
        ValueError: If the bonus paytable type is unknown.
    """
    if not config.bonus_strategy.enabled:
        return None

    paytable_type = config.paytables.bonus.type
    if paytable_type == "paytable_a":
        return bonus_paytable_a()
    if paytable_type == "paytable_b":
        return bonus_paytable_b()
    if paytable_type == "paytable_c":
        return bonus_paytable_c()
    raise ValueError(
        f"Unknown bonus paytable type: '{paytable_type}'. "
        "Supported types: 'paytable_a', 'paytable_b', 'paytable_c'."
    )


class SimulationController:
    """Orchestrates the execution of multiple simulation sessions.

    The controller manages the lifecycle of sessions, handles RNG seeding
    for reproducibility, and aggregates results.
    """

    __slots__ = ("_config", "_progress_callback", "_base_seed")

    def __init__(
        self,
        config: FullConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize the simulation controller.

        Args:
            config: Full simulation configuration.
            progress_callback: Optional callback for progress reporting.
                Called with (completed_sessions, total_sessions) after
                each session completes.
        """
        self._config = config
        self._progress_callback = progress_callback
        self._base_seed = config.simulation.random_seed

    def run(self) -> SimulationResults:
        """Execute the simulation.

        Runs the configured number of sessions sequentially, collecting
        results and reporting progress.

        Returns:
            SimulationResults containing all session results and metadata.
        """
        start_time = datetime.now()
        num_sessions = self._config.simulation.num_sessions
        session_results: list[SessionResult] = []

        # Create immutable components once and reuse across sessions
        # (Strategy, paytables, and betting system configs are identical per-session)
        strategy = create_strategy(self._config.strategy)
        main_paytable = _get_main_paytable(self._config)
        bonus_paytable = _get_bonus_paytable(self._config)

        def betting_system_factory() -> BettingSystem:
            return create_betting_system(self._config.bankroll)

        # Create master RNG for deriving session seeds
        if self._base_seed is not None:
            master_rng = random.Random(self._base_seed)
        else:
            master_rng = random.Random()

        for session_id in range(num_sessions):
            # Derive a session-specific seed for reproducibility
            session_seed = master_rng.randint(0, 2**31 - 1)
            session_rng = random.Random(session_seed)

            session = self._create_session(
                session_rng,
                strategy,
                main_paytable,
                bonus_paytable,
                betting_system_factory,
            )
            result = self._run_session(session)
            session_results.append(result)

            if self._progress_callback is not None:
                self._progress_callback(session_id + 1, num_sessions)

        end_time = datetime.now()

        total_hands = sum(r.hands_played for r in session_results)

        return SimulationResults(
            config=self._config,
            session_results=session_results,
            start_time=start_time,
            end_time=end_time,
            total_hands=total_hands,
        )

    def _create_session(
        self,
        rng: random.Random,
        strategy: Strategy,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable | None,
        betting_system_factory: Callable[[], BettingSystem],
    ) -> Session:
        """Create a new session with fresh state.

        Args:
            rng: Random number generator for this session.
            strategy: Strategy instance (reused across sessions).
            main_paytable: Main game paytable (reused across sessions).
            bonus_paytable: Bonus paytable or None (reused across sessions).
            betting_system_factory: Factory to create fresh betting system per session.

        Returns:
            A new Session instance ready to run.
        """
        # Build SessionConfig from FullConfig
        bankroll_config = self._config.bankroll
        stop_conditions = bankroll_config.stop_conditions

        # Determine bonus bet amount (0 if bonus disabled)
        bonus_bet = 0.0
        if self._config.bonus_strategy.enabled:
            # For now, use a fixed bonus bet if enabled
            # TODO: Support dynamic bonus betting from strategy
            if self._config.bonus_strategy.always is not None:
                bonus_bet = self._config.bonus_strategy.always.amount
            elif self._config.bonus_strategy.static is not None:
                if self._config.bonus_strategy.static.amount is not None:
                    bonus_bet = self._config.bonus_strategy.static.amount
                elif self._config.bonus_strategy.static.ratio is not None:
                    bonus_bet = (
                        bankroll_config.base_bet
                        * self._config.bonus_strategy.static.ratio
                    )

        session_config = SessionConfig(
            starting_bankroll=bankroll_config.starting_amount,
            base_bet=bankroll_config.base_bet,
            win_limit=stop_conditions.win_limit,
            loss_limit=stop_conditions.loss_limit,
            max_hands=self._config.simulation.hands_per_session,
            stop_on_insufficient_funds=stop_conditions.stop_on_insufficient_funds,
            bonus_bet=bonus_bet,
        )

        # Create game components - Deck must be fresh per session
        deck = Deck()

        engine = GameEngine(
            deck=deck,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            rng=rng,
            dealer_config=self._config.dealer,
        )

        # Betting system needs fresh state per session
        betting_system = betting_system_factory()

        return Session(session_config, engine, betting_system)

    def _run_session(self, session: Session) -> SessionResult:
        """Run a single session to completion.

        Args:
            session: The session to run.

        Returns:
            The session result.
        """
        return session.run_to_completion()
