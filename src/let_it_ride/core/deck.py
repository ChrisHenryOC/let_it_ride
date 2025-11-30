"""Deck management for Let It Ride.

This module provides the Deck class for managing a standard 52-card deck
with Fisher-Yates shuffling and card tracking for statistical validation.
"""

import random

from let_it_ride.core.card import Card, Rank, Suit


class DeckEmptyError(Exception):
    """Raised when attempting to deal from an empty or insufficient deck."""


class Deck:
    """A standard 52-card deck with shuffle, deal, and reset operations.

    The deck uses Fisher-Yates shuffling algorithm for uniform distribution
    and tracks dealt cards for statistical validation.
    """

    def __init__(self) -> None:
        """Initialize a new deck with all 52 cards."""
        self._cards: list[Card] = self._create_full_deck()
        self._dealt: list[Card] = []

    @staticmethod
    def _create_full_deck() -> list[Card]:
        """Create a standard 52-card deck."""
        return [Card(rank, suit) for suit in Suit for rank in Rank]

    def shuffle(self, rng: random.Random) -> None:
        """Shuffle the remaining cards using Fisher-Yates algorithm.

        Args:
            rng: Random number generator for reproducible shuffling.

        Note:
            Only shuffles cards that haven't been dealt. Dealt cards
            remain in the dealt pile until reset() is called.
        """
        # Fisher-Yates shuffle (in-place, O(n))
        cards = self._cards
        n = len(cards)
        for i in range(n - 1, 0, -1):
            j = rng.randint(0, i)
            cards[i], cards[j] = cards[j], cards[i]

    def deal(self, count: int = 1) -> list[Card]:
        """Deal cards from the top of the deck.

        Args:
            count: Number of cards to deal (default: 1).

        Returns:
            List of dealt cards.

        Raises:
            DeckEmptyError: If there are not enough cards remaining.
            ValueError: If count is less than 1.
        """
        if count < 1:
            raise ValueError("Count must be at least 1")
        if count > len(self._cards):
            raise DeckEmptyError(
                f"Cannot deal {count} cards, only {len(self._cards)} remaining"
            )

        dealt = self._cards[-count:]
        self._cards = self._cards[:-count]
        self._dealt.extend(dealt)
        return dealt

    def cards_remaining(self) -> int:
        """Return the number of cards remaining in the deck."""
        return len(self._cards)

    def dealt_cards(self) -> list[Card]:
        """Return a copy of the list of dealt cards.

        Returns a copy to prevent external modification.
        """
        return self._dealt.copy()

    def reset(self) -> None:
        """Return all dealt cards to the deck.

        This restores the deck to a full 52-card state.
        Cards are not shuffled; call shuffle() after reset() if needed.
        """
        self._cards = self._create_full_deck()
        self._dealt = []

    def __len__(self) -> int:
        """Return the number of cards remaining in the deck."""
        return len(self._cards)

    def __repr__(self) -> str:
        """Return a string representation of the deck state."""
        return f"Deck(remaining={len(self._cards)}, dealt={len(self._dealt)})"
