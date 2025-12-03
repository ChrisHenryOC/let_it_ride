"""Session result data structures for Let It Ride.

This module provides data structures for recording and serializing
session results and individual hand records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from let_it_ride.strategy.base import Decision

if TYPE_CHECKING:
    from collections.abc import Iterable

    from let_it_ride.core.game_engine import GameHandResult
    from let_it_ride.core.hand_evaluator import FiveCardHandRank


@dataclass(frozen=True, slots=True)
class HandRecord:
    """Serializable record of a single Let It Ride hand.

    This dataclass stores all per-hand information in a format suitable
    for serialization to CSV, JSON, or other formats. Card and enum values
    are stored as strings for portability.

    Attributes:
        hand_id: Unique hand identifier within the session.
        session_id: Parent session identifier.
        shoe_id: Shoe identifier, or None if single-deck mode.
        cards_player: Player's 3 cards as space-separated string (e.g., "Ah Kd Qs").
        cards_community: 2 community cards as space-separated string.
        decision_bet1: Decision on bet 1 ("ride" or "pull").
        decision_bet2: Decision on bet 2 ("ride" or "pull").
        final_hand_rank: Evaluated 5-card hand rank name (e.g., "flush").
        base_bet: Bet amount per circle.
        bets_at_risk: Total amount wagered after decisions.
        main_payout: Profit from main game (0 for losing hands).
        bonus_bet: Bonus bet amount (0 if not playing bonus).
        bonus_hand_rank: 3-card bonus hand rank name, or None if no bonus bet.
        bonus_payout: Profit from bonus bet (0 for losing or no bet).
        bankroll_after: Bankroll balance after hand completed.
    """

    hand_id: int
    session_id: int
    shoe_id: int | None
    cards_player: str
    cards_community: str
    decision_bet1: str
    decision_bet2: str
    final_hand_rank: str
    base_bet: float
    bets_at_risk: float
    main_payout: float
    bonus_bet: float
    bonus_hand_rank: str | None
    bonus_payout: float
    bankroll_after: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary with all fields suitable for JSON/CSV export.
        """
        return {
            "hand_id": self.hand_id,
            "session_id": self.session_id,
            "shoe_id": self.shoe_id,
            "cards_player": self.cards_player,
            "cards_community": self.cards_community,
            "decision_bet1": self.decision_bet1,
            "decision_bet2": self.decision_bet2,
            "final_hand_rank": self.final_hand_rank,
            "base_bet": self.base_bet,
            "bets_at_risk": self.bets_at_risk,
            "main_payout": self.main_payout,
            "bonus_bet": self.bonus_bet,
            "bonus_hand_rank": self.bonus_hand_rank,
            "bonus_payout": self.bonus_payout,
            "bankroll_after": self.bankroll_after,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HandRecord:
        """Create HandRecord from dictionary.

        Args:
            data: Dictionary with hand record fields.

        Returns:
            HandRecord instance.

        Raises:
            KeyError: If required field is missing.
            TypeError: If field has wrong type.
        """
        return cls(
            hand_id=int(data["hand_id"]),
            session_id=int(data["session_id"]),
            shoe_id=int(data["shoe_id"]) if data.get("shoe_id") is not None else None,
            cards_player=str(data["cards_player"]),
            cards_community=str(data["cards_community"]),
            decision_bet1=str(data["decision_bet1"]),
            decision_bet2=str(data["decision_bet2"]),
            final_hand_rank=str(data["final_hand_rank"]),
            base_bet=float(data["base_bet"]),
            bets_at_risk=float(data["bets_at_risk"]),
            main_payout=float(data["main_payout"]),
            bonus_bet=float(data["bonus_bet"]),
            bonus_hand_rank=(
                str(data["bonus_hand_rank"])
                if data.get("bonus_hand_rank") is not None
                else None
            ),
            bonus_payout=float(data["bonus_payout"]),
            bankroll_after=float(data["bankroll_after"]),
        )

    @classmethod
    def from_game_result(
        cls,
        result: GameHandResult,
        session_id: int,
        bankroll_after: float,
        shoe_id: int | None = None,
    ) -> HandRecord:
        """Create HandRecord from GameHandResult.

        Converts the in-memory game result with Card objects and enums
        to a serializable HandRecord with string representations.

        Args:
            result: GameHandResult from the game engine.
            session_id: Parent session identifier.
            bankroll_after: Bankroll balance after the hand completed.
            shoe_id: Optional shoe identifier.

        Returns:
            HandRecord instance.
        """
        # Convert cards to space-separated strings
        cards_player = " ".join(str(card) for card in result.player_cards)
        cards_community = " ".join(str(card) for card in result.community_cards)

        # Convert decisions to lowercase strings
        decision_bet1 = result.decision_bet1.value
        decision_bet2 = result.decision_bet2.value

        # Convert hand ranks to lowercase strings
        final_hand_rank = result.final_hand_rank.name.lower()
        bonus_hand_rank = (
            result.bonus_hand_rank.name.lower()
            if result.bonus_hand_rank is not None
            else None
        )

        return cls(
            hand_id=result.hand_id,
            session_id=session_id,
            shoe_id=shoe_id,
            cards_player=cards_player,
            cards_community=cards_community,
            decision_bet1=decision_bet1,
            decision_bet2=decision_bet2,
            final_hand_rank=final_hand_rank,
            base_bet=result.base_bet,
            bets_at_risk=result.bets_at_risk,
            main_payout=result.main_payout,
            bonus_bet=result.bonus_bet,
            bonus_hand_rank=bonus_hand_rank,
            bonus_payout=result.bonus_payout,
            bankroll_after=bankroll_after,
        )


def count_hand_distribution(
    records: Iterable[HandRecord | GameHandResult],
) -> dict[str, int]:
    """Count the distribution of hand types.

    Counts how many times each 5-card hand rank appears in the
    given collection of hand records or game results.

    Args:
        records: Iterable of HandRecord or GameHandResult objects.

    Returns:
        Dictionary mapping hand rank names (lowercase) to counts.
        Only includes ranks that appear at least once.
    """
    distribution: dict[str, int] = {}

    for record in records:
        if isinstance(record, HandRecord):
            rank_name = record.final_hand_rank
        else:
            # GameHandResult
            rank_name = record.final_hand_rank.name.lower()

        distribution[rank_name] = distribution.get(rank_name, 0) + 1

    return distribution


def count_hand_distribution_from_ranks(
    ranks: Iterable[FiveCardHandRank],
) -> dict[str, int]:
    """Count the distribution of hand ranks.

    Alternative helper that counts from raw FiveCardHandRank values.

    Args:
        ranks: Iterable of FiveCardHandRank values.

    Returns:
        Dictionary mapping hand rank names (lowercase) to counts.
    """
    distribution: dict[str, int] = {}

    for rank in ranks:
        rank_name = rank.name.lower()
        distribution[rank_name] = distribution.get(rank_name, 0) + 1

    return distribution


def get_decision_from_string(decision_str: str) -> Decision:
    """Convert a decision string back to Decision enum.

    Args:
        decision_str: Decision string ("ride" or "pull").

    Returns:
        Decision enum value.

    Raises:
        ValueError: If decision string is invalid.
    """
    decision_lower = decision_str.lower()
    if decision_lower == "ride":
        return Decision.RIDE
    elif decision_lower == "pull":
        return Decision.PULL
    else:
        raise ValueError(f"Invalid decision string: {decision_str}")
