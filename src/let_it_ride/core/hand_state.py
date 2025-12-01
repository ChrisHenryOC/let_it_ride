"""Hand state machine for Let It Ride.

This module implements the core state machine that tracks a single hand
through all decision points. It enforces proper game flow and tracks
bet/card state throughout the hand.

Game Flow:
1. DEAL: Player places 3 equal bets, receives 3 cards
2. BET1_DECISION: Player decides to pull or ride on Bet 1
3. FIRST_REVEAL: First community card is revealed
4. BET2_DECISION: Player decides to pull or ride on Bet 2
5. SECOND_REVEAL: Second community card is revealed
6. RESOLVED: Hand is evaluated and paid
"""

from dataclasses import dataclass, field
from enum import Enum

from let_it_ride.core.card import Card


class HandPhase(Enum):
    """Phases of a Let It Ride hand.

    Each hand progresses through these phases in order.
    State transitions are enforced by the HandState class.
    """

    DEAL = "deal"
    BET1_DECISION = "bet1_decision"
    FIRST_REVEAL = "first_reveal"
    BET2_DECISION = "bet2_decision"
    SECOND_REVEAL = "second_reveal"
    RESOLVED = "resolved"


class Decision(Enum):
    """Player decisions for bet 1 and bet 2.

    RIDE: Leave the bet in play
    PULL: Withdraw the bet
    """

    RIDE = "ride"
    PULL = "pull"


class InvalidPhaseError(Exception):
    """Raised when an operation is attempted in an invalid phase."""

    pass


@dataclass
class HandState:
    """Tracks the state of a single Let It Ride hand.

    This class enforces proper game flow by validating phase transitions
    and tracking bet/card state throughout the hand.

    Attributes:
        phase: Current phase of the hand.
        player_cards: The player's 3 dealt cards (immutable after creation).
        community_cards: Community cards revealed so far (0, 1, or 2).
        base_bet: The bet amount per circle.
        bet1_decision: Player's decision on bet 1 (None until decided).
        bet2_decision: Player's decision on bet 2 (None until decided).
        bet1_active: Whether bet 1 is still in play.
        bet2_active: Whether bet 2 is still in play.
        bet3_active: Whether bet 3 is still in play (always True).
    """

    player_cards: tuple[Card, Card, Card]
    base_bet: float
    phase: HandPhase = field(default=HandPhase.DEAL)
    community_cards: list[Card] = field(default_factory=list)
    bet1_decision: Decision | None = field(default=None)
    bet2_decision: Decision | None = field(default=None)
    bet1_active: bool = field(default=True)
    bet2_active: bool = field(default=True)
    bet3_active: bool = field(default=True)

    def __post_init__(self) -> None:
        """Validate initial state."""
        if len(self.player_cards) != 3:
            raise ValueError(
                f"Player must have exactly 3 cards, got {len(self.player_cards)}"
            )
        if self.base_bet <= 0:
            raise ValueError(f"Base bet must be positive, got {self.base_bet}")

    def apply_bet1_decision(self, decision: Decision) -> None:
        """Record the player's decision on bet 1.

        Args:
            decision: RIDE to keep bet 1 in play, PULL to withdraw it.

        Raises:
            InvalidPhaseError: If not in DEAL phase.
        """
        if self.phase != HandPhase.DEAL:
            raise InvalidPhaseError(
                f"Cannot apply bet 1 decision in phase {self.phase.value}, "
                f"expected {HandPhase.DEAL.value}"
            )
        self.bet1_decision = decision
        if decision == Decision.PULL:
            self.bet1_active = False
        self.phase = HandPhase.BET1_DECISION

    def reveal_first_community(self, card: Card) -> None:
        """Reveal the first community card.

        Args:
            card: The first community card to reveal.

        Raises:
            InvalidPhaseError: If not in BET1_DECISION phase.
        """
        if self.phase != HandPhase.BET1_DECISION:
            raise InvalidPhaseError(
                f"Cannot reveal first community card in phase {self.phase.value}, "
                f"expected {HandPhase.BET1_DECISION.value}"
            )
        self.community_cards.append(card)
        self.phase = HandPhase.FIRST_REVEAL

    def apply_bet2_decision(self, decision: Decision) -> None:
        """Record the player's decision on bet 2.

        Args:
            decision: RIDE to keep bet 2 in play, PULL to withdraw it.

        Raises:
            InvalidPhaseError: If not in FIRST_REVEAL phase.
        """
        if self.phase != HandPhase.FIRST_REVEAL:
            raise InvalidPhaseError(
                f"Cannot apply bet 2 decision in phase {self.phase.value}, "
                f"expected {HandPhase.FIRST_REVEAL.value}"
            )
        self.bet2_decision = decision
        if decision == Decision.PULL:
            self.bet2_active = False
        self.phase = HandPhase.BET2_DECISION

    def reveal_second_community(self, card: Card) -> None:
        """Reveal the second community card.

        Args:
            card: The second community card to reveal.

        Raises:
            InvalidPhaseError: If not in BET2_DECISION phase.
        """
        if self.phase != HandPhase.BET2_DECISION:
            raise InvalidPhaseError(
                f"Cannot reveal second community card in phase {self.phase.value}, "
                f"expected {HandPhase.BET2_DECISION.value}"
            )
        self.community_cards.append(card)
        self.phase = HandPhase.SECOND_REVEAL

    def resolve(self) -> None:
        """Mark the hand as resolved.

        This should be called after the hand has been evaluated and paid.

        Raises:
            InvalidPhaseError: If not in SECOND_REVEAL phase.
        """
        if self.phase != HandPhase.SECOND_REVEAL:
            raise InvalidPhaseError(
                f"Cannot resolve hand in phase {self.phase.value}, "
                f"expected {HandPhase.SECOND_REVEAL.value}"
            )
        self.phase = HandPhase.RESOLVED

    def get_visible_cards(self) -> list[Card]:
        """Get all cards currently visible to the player.

        Returns:
            List of cards visible at the current phase.
            In DEAL/BET1_DECISION: 3 player cards.
            In FIRST_REVEAL/BET2_DECISION: 3 player cards + 1 community.
            In SECOND_REVEAL/RESOLVED: All 5 cards.
        """
        visible = list(self.player_cards)
        visible.extend(self.community_cards)
        return visible

    def get_final_hand(self) -> tuple[Card, ...]:
        """Get the final 5-card hand for evaluation.

        Returns:
            Tuple of all 5 cards (3 player + 2 community).

        Raises:
            InvalidPhaseError: If called before SECOND_REVEAL phase.
        """
        if self.phase not in (HandPhase.SECOND_REVEAL, HandPhase.RESOLVED):
            raise InvalidPhaseError(
                f"Cannot get final hand in phase {self.phase.value}, "
                f"must be in {HandPhase.SECOND_REVEAL.value} or "
                f"{HandPhase.RESOLVED.value}"
            )
        return tuple(self.player_cards) + tuple(self.community_cards)

    def bets_at_risk(self) -> float:
        """Calculate the total amount of bets still in play.

        Returns:
            Sum of base_bet for each active bet (bet1, bet2, bet3).
        """
        active_count = sum([self.bet1_active, self.bet2_active, self.bet3_active])
        return self.base_bet * active_count
