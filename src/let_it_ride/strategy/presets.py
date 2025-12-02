"""Preset strategy implementations for Let It Ride.

This module provides factory functions for commonly used strategy configurations:
- Conservative: Only ride on made hands (minimizes variance)
- Aggressive: Ride on any reasonable draw (maximizes action)

These presets are implemented using CustomStrategy with predefined rules.
"""

from let_it_ride.strategy.base import Decision
from let_it_ride.strategy.custom import CustomStrategy, StrategyRule


def conservative_strategy() -> CustomStrategy:
    """Create a conservative strategy that only rides on made hands.

    The conservative strategy is designed for risk-averse players who want
    to minimize variance. It only lets bets ride when holding a paying hand
    (pair of 10s or better, trips, two pair).

    Bet 1 (3-card) rules:
        - Ride on paying hands only

    Bet 2 (4-card) rules:
        - Ride on paying hands only

    Returns:
        A CustomStrategy configured for conservative play.

    Example:
        >>> strategy = conservative_strategy()
        >>> # Will only ride on made hands, never on draws
    """
    bet1_rules = [
        StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
        StrategyRule(condition="default", action=Decision.PULL),
    ]

    bet2_rules = [
        StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
        StrategyRule(condition="default", action=Decision.PULL),
    ]

    return CustomStrategy(bet1_rules=bet1_rules, bet2_rules=bet2_rules)


def aggressive_strategy() -> CustomStrategy:
    """Create an aggressive strategy that rides on any draw.

    The aggressive strategy is designed for players who want maximum action.
    It lets bets ride on any paying hand, flush draw, or straight draw.

    Bet 1 (3-card) rules:
        - Ride on paying hands
        - Ride on flush draws (3 suited cards)
        - Ride on straight draws (3 connected cards)
        - Default: pull

    Bet 2 (4-card) rules:
        - Ride on paying hands
        - Ride on flush draws (4 suited cards)
        - Ride on any straight draw
        - Default: pull

    Returns:
        A CustomStrategy configured for aggressive play.

    Example:
        >>> strategy = aggressive_strategy()
        >>> # Will ride on made hands and all reasonable draws
    """
    bet1_rules = [
        StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
        StrategyRule(condition="is_flush_draw", action=Decision.RIDE),
        StrategyRule(condition="is_straight_draw", action=Decision.RIDE),
        StrategyRule(condition="default", action=Decision.PULL),
    ]

    bet2_rules = [
        StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
        StrategyRule(condition="is_flush_draw", action=Decision.RIDE),
        StrategyRule(condition="is_straight_draw", action=Decision.RIDE),
        StrategyRule(condition="default", action=Decision.PULL),
    ]

    return CustomStrategy(bet1_rules=bet1_rules, bet2_rules=bet2_rules)
