"""Card, Rank, and Suit definitions for Let It Ride.

This module provides the fundamental card representation used throughout
the game engine. Cards are immutable (frozen dataclass) to prevent
accidental modification during gameplay.
"""

from dataclasses import dataclass
from enum import Enum


class Rank(Enum):
    """Card ranks from TWO (2) through ACE (14).

    Integer values enable natural ordering for hand comparison.
    ACE can be high (14) or low (1) depending on context - use the
    compare_ace_low() method when ACE should be treated as low.
    """

    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Rank):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Rank):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Rank):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Rank):
            return NotImplemented
        return self.value >= other.value

    def __str__(self) -> str:
        """Return single character representation of rank."""
        if self.value <= 9:
            return str(self.value)
        return {10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}[self.value]

    def low_value(self) -> int:
        """Return the rank value treating ACE as 1 (low).

        For all other ranks, returns the standard value.
        """
        if self == Rank.ACE:
            return 1
        return int(self.value)

    def compare_ace_low(self, other: "Rank") -> int:
        """Compare ranks treating ACE as low (value 1).

        Returns:
            Negative if self < other, 0 if equal, positive if self > other.
        """
        return self.low_value() - other.low_value()


class Suit(Enum):
    """Card suits with single-character values for string representation.

    Note: Suits have no inherent ordering in Let It Ride.
    """

    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"


@dataclass(frozen=True)
class Card:
    """Immutable card representation with rank and suit.

    Cards are frozen (immutable) to prevent accidental modification
    during gameplay. Comparison is by rank only; suits have no ordering.
    """

    rank: Rank
    suit: Suit

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank < other.rank

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank <= other.rank

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank > other.rank

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank >= other.rank

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def __str__(self) -> str:
        """Return two-character representation (e.g., 'Ah' for Ace of Hearts)."""
        return f"{self.rank}{self.suit.value}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return f"Card({self.rank.name}, {self.suit.name})"
