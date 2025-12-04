"""Core game engine components.

This module contains the fundamental game mechanics including:
- Card and Deck representations
- Multi-deck Shoe implementation
- Hand evaluation (5-card and 3-card)
- Hand analysis for strategy decisions
- Hand processing (shared decision and payout logic)
- Game state management
- Game engine orchestration

Note: GameEngine, GameHandResult, Table, and related classes are not exported
here because they import from config.paytables, which in turn imports from
core.hand_evaluator. Exporting them here would create a circular import.
Import them directly: from let_it_ride.core.game_engine import GameEngine
"""

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.deck import Deck, DeckEmptyError
from let_it_ride.core.hand_analysis import (
    HandAnalysis,
    analyze_four_cards,
    analyze_three_cards,
)
from let_it_ride.core.hand_evaluator import (
    FiveCardHandRank,
    HandResult,
    evaluate_five_card_hand,
)
from let_it_ride.core.hand_state import (
    Decision,
    HandPhase,
    HandState,
    InvalidPhaseError,
)
from let_it_ride.core.three_card_evaluator import (
    ThreeCardHandRank,
    evaluate_three_card_hand,
)

__all__ = [
    "Card",
    "Rank",
    "Suit",
    "Deck",
    "DeckEmptyError",
    "FiveCardHandRank",
    "HandResult",
    "evaluate_five_card_hand",
    "ThreeCardHandRank",
    "evaluate_three_card_hand",
    "HandAnalysis",
    "analyze_three_cards",
    "analyze_four_cards",
    "Decision",
    "HandPhase",
    "HandState",
    "InvalidPhaseError",
]
