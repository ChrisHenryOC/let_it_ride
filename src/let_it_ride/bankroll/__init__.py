"""Bankroll management.

This module contains bankroll tracking and betting systems:
- Bankroll tracker with high water mark and drawdown
- Flat betting system
- Progressive betting systems (Martingale, Paroli, etc.)
"""

from let_it_ride.bankroll.tracker import BankrollTracker

__all__ = ["BankrollTracker"]
