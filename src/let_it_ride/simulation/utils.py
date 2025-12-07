"""Shared utility functions for simulation modules.

This module provides common helper functions used by both the simulation
controller and parallel executor to avoid code duplication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_a,
    bonus_paytable_b,
    bonus_paytable_c,
    standard_main_paytable,
)
from let_it_ride.simulation.session import SessionConfig

if TYPE_CHECKING:
    from let_it_ride.config.models import FullConfig


def get_main_paytable(config: FullConfig) -> MainGamePaytable:
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


def get_bonus_paytable(config: FullConfig) -> BonusPaytable | None:
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


def calculate_bonus_bet(config: FullConfig) -> float:
    """Calculate the bonus bet amount from configuration.

    Args:
        config: The full simulation configuration.

    Returns:
        The bonus bet amount (0.0 if disabled).
    """
    if not config.bonus_strategy.enabled:
        return 0.0

    if config.bonus_strategy.always is not None:
        return config.bonus_strategy.always.amount
    if config.bonus_strategy.static is not None:
        if config.bonus_strategy.static.amount is not None:
            return config.bonus_strategy.static.amount
        if config.bonus_strategy.static.ratio is not None:
            return config.bankroll.base_bet * config.bonus_strategy.static.ratio

    return 0.0


def create_session_config(config: FullConfig, bonus_bet: float) -> SessionConfig:
    """Create a SessionConfig from FullConfig.

    Args:
        config: The full simulation configuration.
        bonus_bet: The bonus bet amount.

    Returns:
        A SessionConfig instance.
    """
    bankroll_config = config.bankroll
    stop_conditions = bankroll_config.stop_conditions

    return SessionConfig(
        starting_bankroll=bankroll_config.starting_amount,
        base_bet=bankroll_config.base_bet,
        win_limit=stop_conditions.win_limit,
        loss_limit=stop_conditions.loss_limit,
        max_hands=config.simulation.hands_per_session,
        stop_on_insufficient_funds=stop_conditions.stop_on_insufficient_funds,
        bonus_bet=bonus_bet,
    )
