"""Unit tests for the hand state machine.

Tests cover:
- Valid state transitions through the full game flow
- Invalid state transitions (should raise InvalidPhaseError)
- Bet tracking (active/inactive based on decisions)
- Utility methods (get_visible_cards, get_final_hand, bets_at_risk)
"""

import pytest

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_state import (
    Decision,
    HandPhase,
    HandState,
    InvalidPhaseError,
)


# Test fixtures
@pytest.fixture
def player_cards() -> tuple[Card, Card, Card]:
    """Standard player cards for testing."""
    return (
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.QUEEN, Suit.SPADES),
    )


@pytest.fixture
def community_card1() -> Card:
    """First community card for testing."""
    return Card(Rank.JACK, Suit.SPADES)


@pytest.fixture
def community_card2() -> Card:
    """Second community card for testing."""
    return Card(Rank.TEN, Suit.SPADES)


@pytest.fixture
def hand_state(player_cards: tuple[Card, Card, Card]) -> HandState:
    """Create a fresh HandState in DEAL phase."""
    return HandState(player_cards=player_cards, base_bet=5.0)


class TestHandStateCreation:
    """Tests for HandState initialization."""

    def test_create_hand_state(self, player_cards: tuple[Card, Card, Card]) -> None:
        """Test creating a new HandState."""
        state = HandState(player_cards=player_cards, base_bet=10.0)

        assert state.phase == HandPhase.DEAL
        assert state.player_cards == player_cards
        assert state.base_bet == 10.0
        assert state.community_cards == []
        assert state.bet1_decision is None
        assert state.bet2_decision is None
        assert state.bet1_active is True
        assert state.bet2_active is True
        assert state.bet3_active is True

    def test_create_with_wrong_card_count(self) -> None:
        """Test that creating with wrong number of cards raises ValueError."""
        two_cards = (
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.KING, Suit.SPADES),
        )
        with pytest.raises(ValueError, match="exactly 3 cards"):
            # Type: ignore for test - intentionally passing wrong type
            HandState(player_cards=two_cards, base_bet=5.0)  # type: ignore[arg-type]

    def test_create_with_zero_bet(self, player_cards: tuple[Card, Card, Card]) -> None:
        """Test that creating with zero bet raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            HandState(player_cards=player_cards, base_bet=0.0)

    def test_create_with_negative_bet(
        self, player_cards: tuple[Card, Card, Card]
    ) -> None:
        """Test that creating with negative bet raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            HandState(player_cards=player_cards, base_bet=-5.0)


class TestValidStateTransitions:
    """Tests for valid state transitions through the full game flow."""

    def test_apply_bet1_decision_ride(self, hand_state: HandState) -> None:
        """Test applying RIDE decision for bet 1."""
        hand_state.apply_bet1_decision(Decision.RIDE)

        assert hand_state.phase == HandPhase.BET1_DECISION
        assert hand_state.bet1_decision == Decision.RIDE
        assert hand_state.bet1_active is True

    def test_apply_bet1_decision_pull(self, hand_state: HandState) -> None:
        """Test applying PULL decision for bet 1."""
        hand_state.apply_bet1_decision(Decision.PULL)

        assert hand_state.phase == HandPhase.BET1_DECISION
        assert hand_state.bet1_decision == Decision.PULL
        assert hand_state.bet1_active is False

    def test_reveal_first_community(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test revealing the first community card."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)

        assert hand_state.phase == HandPhase.FIRST_REVEAL
        assert len(hand_state.community_cards) == 1
        assert hand_state.community_cards[0] == community_card1

    def test_apply_bet2_decision_ride(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test applying RIDE decision for bet 2."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)

        assert hand_state.phase == HandPhase.BET2_DECISION
        assert hand_state.bet2_decision == Decision.RIDE
        assert hand_state.bet2_active is True

    def test_apply_bet2_decision_pull(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test applying PULL decision for bet 2."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.PULL)

        assert hand_state.phase == HandPhase.BET2_DECISION
        assert hand_state.bet2_decision == Decision.PULL
        assert hand_state.bet2_active is False

    def test_reveal_second_community(
        self,
        hand_state: HandState,
        community_card1: Card,
        community_card2: Card,
    ) -> None:
        """Test revealing the second community card."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)
        hand_state.reveal_second_community(community_card2)

        assert hand_state.phase == HandPhase.SECOND_REVEAL
        assert len(hand_state.community_cards) == 2
        assert hand_state.community_cards[1] == community_card2

    def test_resolve(
        self,
        hand_state: HandState,
        community_card1: Card,
        community_card2: Card,
    ) -> None:
        """Test resolving the hand."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)
        hand_state.reveal_second_community(community_card2)
        hand_state.resolve()

        assert hand_state.phase == HandPhase.RESOLVED

    def test_full_game_flow_all_ride(
        self,
        hand_state: HandState,
        community_card1: Card,
        community_card2: Card,
    ) -> None:
        """Test complete game flow with all RIDE decisions."""
        # DEAL -> BET1_DECISION
        hand_state.apply_bet1_decision(Decision.RIDE)
        assert hand_state.phase == HandPhase.BET1_DECISION

        # BET1_DECISION -> FIRST_REVEAL
        hand_state.reveal_first_community(community_card1)
        assert hand_state.phase == HandPhase.FIRST_REVEAL

        # FIRST_REVEAL -> BET2_DECISION
        hand_state.apply_bet2_decision(Decision.RIDE)
        assert hand_state.phase == HandPhase.BET2_DECISION

        # BET2_DECISION -> SECOND_REVEAL
        hand_state.reveal_second_community(community_card2)
        assert hand_state.phase == HandPhase.SECOND_REVEAL

        # SECOND_REVEAL -> RESOLVED
        hand_state.resolve()
        assert hand_state.phase == HandPhase.RESOLVED

        # Verify all bets active
        assert hand_state.bet1_active is True
        assert hand_state.bet2_active is True
        assert hand_state.bet3_active is True

    def test_full_game_flow_all_pull(
        self,
        hand_state: HandState,
        community_card1: Card,
        community_card2: Card,
    ) -> None:
        """Test complete game flow with all PULL decisions."""
        hand_state.apply_bet1_decision(Decision.PULL)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.PULL)
        hand_state.reveal_second_community(community_card2)
        hand_state.resolve()

        assert hand_state.phase == HandPhase.RESOLVED
        assert hand_state.bet1_active is False
        assert hand_state.bet2_active is False
        assert hand_state.bet3_active is True  # Always true


class TestInvalidStateTransitions:
    """Tests for invalid state transitions that should raise InvalidPhaseError."""

    def test_apply_bet1_in_wrong_phase(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test that applying bet1 decision in wrong phase raises error."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)

        # Now in FIRST_REVEAL, should not be able to apply bet1 decision
        with pytest.raises(InvalidPhaseError, match="bet 1"):
            hand_state.apply_bet1_decision(Decision.RIDE)

    def test_reveal_first_community_in_deal_phase(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test that revealing first community in DEAL phase raises error."""
        # Still in DEAL phase
        with pytest.raises(InvalidPhaseError, match="first community"):
            hand_state.reveal_first_community(community_card1)

    def test_reveal_first_community_in_first_reveal_phase(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test that revealing first community twice raises error."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)

        # Already revealed, should not be able to reveal again
        with pytest.raises(InvalidPhaseError, match="first community"):
            hand_state.reveal_first_community(Card(Rank.TWO, Suit.HEARTS))

    def test_apply_bet2_in_deal_phase(self, hand_state: HandState) -> None:
        """Test that applying bet2 decision in DEAL phase raises error."""
        with pytest.raises(InvalidPhaseError, match="bet 2"):
            hand_state.apply_bet2_decision(Decision.RIDE)

    def test_apply_bet2_in_bet1_decision_phase(self, hand_state: HandState) -> None:
        """Test that applying bet2 decision in BET1_DECISION phase raises error."""
        hand_state.apply_bet1_decision(Decision.RIDE)

        with pytest.raises(InvalidPhaseError, match="bet 2"):
            hand_state.apply_bet2_decision(Decision.RIDE)

    def test_reveal_second_community_in_first_reveal_phase(
        self, hand_state: HandState, community_card1: Card, community_card2: Card
    ) -> None:
        """Test that revealing second community in FIRST_REVEAL phase raises error."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)

        # In FIRST_REVEAL, should not be able to reveal second community yet
        with pytest.raises(InvalidPhaseError, match="second community"):
            hand_state.reveal_second_community(community_card2)

    def test_resolve_in_deal_phase(self, hand_state: HandState) -> None:
        """Test that resolving in DEAL phase raises error."""
        with pytest.raises(InvalidPhaseError, match="resolve"):
            hand_state.resolve()

    def test_resolve_in_bet2_decision_phase(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test that resolving in BET2_DECISION phase raises error."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)

        with pytest.raises(InvalidPhaseError, match="resolve"):
            hand_state.resolve()

    def test_operations_after_resolved(
        self,
        hand_state: HandState,
        community_card1: Card,
        community_card2: Card,
    ) -> None:
        """Test that no operations are allowed after RESOLVED phase."""
        # Go through full game flow
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)
        hand_state.reveal_second_community(community_card2)
        hand_state.resolve()

        # All operations should fail
        with pytest.raises(InvalidPhaseError):
            hand_state.apply_bet1_decision(Decision.RIDE)

        with pytest.raises(InvalidPhaseError):
            hand_state.reveal_first_community(Card(Rank.TWO, Suit.HEARTS))

        with pytest.raises(InvalidPhaseError):
            hand_state.apply_bet2_decision(Decision.RIDE)

        with pytest.raises(InvalidPhaseError):
            hand_state.reveal_second_community(Card(Rank.TWO, Suit.HEARTS))

        with pytest.raises(InvalidPhaseError):
            hand_state.resolve()


class TestBetsAtRisk:
    """Tests for the bets_at_risk calculation."""

    def test_bets_at_risk_initial(self, hand_state: HandState) -> None:
        """Test initial bets at risk (all 3 bets active)."""
        assert hand_state.bets_at_risk() == 15.0  # 5.0 * 3

    def test_bets_at_risk_after_pull_bet1(self, hand_state: HandState) -> None:
        """Test bets at risk after pulling bet 1."""
        hand_state.apply_bet1_decision(Decision.PULL)

        assert hand_state.bets_at_risk() == 10.0  # 5.0 * 2

    def test_bets_at_risk_after_pull_both(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test bets at risk after pulling both bets."""
        hand_state.apply_bet1_decision(Decision.PULL)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.PULL)

        assert hand_state.bets_at_risk() == 5.0  # 5.0 * 1 (only bet3)

    def test_bets_at_risk_after_ride_both(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test bets at risk after riding both bets."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)

        assert hand_state.bets_at_risk() == 15.0  # 5.0 * 3

    def test_bets_at_risk_mixed_decisions(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test bets at risk with mixed decisions."""
        hand_state.apply_bet1_decision(Decision.PULL)  # Pull bet 1
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)  # Ride bet 2

        assert hand_state.bets_at_risk() == 10.0  # 5.0 * 2 (bet2 + bet3)


class TestGetVisibleCards:
    """Tests for the get_visible_cards method."""

    def test_visible_cards_in_deal_phase(
        self, hand_state: HandState, player_cards: tuple[Card, Card, Card]
    ) -> None:
        """Test visible cards in DEAL phase (only player cards)."""
        visible = hand_state.get_visible_cards()

        assert len(visible) == 3
        assert visible == list(player_cards)

    def test_visible_cards_in_bet1_decision_phase(
        self, hand_state: HandState, player_cards: tuple[Card, Card, Card]
    ) -> None:
        """Test visible cards in BET1_DECISION phase (only player cards)."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        visible = hand_state.get_visible_cards()

        assert len(visible) == 3
        assert visible == list(player_cards)

    def test_visible_cards_in_first_reveal_phase(
        self,
        hand_state: HandState,
        player_cards: tuple[Card, Card, Card],
        community_card1: Card,
    ) -> None:
        """Test visible cards in FIRST_REVEAL phase (4 cards)."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        visible = hand_state.get_visible_cards()

        assert len(visible) == 4
        assert visible[:3] == list(player_cards)
        assert visible[3] == community_card1

    def test_visible_cards_in_second_reveal_phase(
        self,
        hand_state: HandState,
        player_cards: tuple[Card, Card, Card],
        community_card1: Card,
        community_card2: Card,
    ) -> None:
        """Test visible cards in SECOND_REVEAL phase (5 cards)."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)
        hand_state.reveal_second_community(community_card2)
        visible = hand_state.get_visible_cards()

        assert len(visible) == 5
        assert visible[:3] == list(player_cards)
        assert visible[3] == community_card1
        assert visible[4] == community_card2


class TestGetFinalHand:
    """Tests for the get_final_hand method."""

    def test_get_final_hand_in_second_reveal(
        self,
        hand_state: HandState,
        player_cards: tuple[Card, Card, Card],
        community_card1: Card,
        community_card2: Card,
    ) -> None:
        """Test getting final hand in SECOND_REVEAL phase."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)
        hand_state.reveal_second_community(community_card2)

        final_hand = hand_state.get_final_hand()

        assert len(final_hand) == 5
        assert final_hand[:3] == player_cards
        assert final_hand[3] == community_card1
        assert final_hand[4] == community_card2

    def test_get_final_hand_in_resolved(
        self,
        hand_state: HandState,
        community_card1: Card,
        community_card2: Card,
    ) -> None:
        """Test getting final hand in RESOLVED phase."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)
        hand_state.reveal_second_community(community_card2)
        hand_state.resolve()

        final_hand = hand_state.get_final_hand()
        assert len(final_hand) == 5

    def test_get_final_hand_in_deal_phase_raises(self, hand_state: HandState) -> None:
        """Test that getting final hand in DEAL phase raises error."""
        with pytest.raises(InvalidPhaseError, match="final hand"):
            hand_state.get_final_hand()

    def test_get_final_hand_in_first_reveal_phase_raises(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test that getting final hand in FIRST_REVEAL phase raises error."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)

        with pytest.raises(InvalidPhaseError, match="final hand"):
            hand_state.get_final_hand()

    def test_get_final_hand_in_bet2_decision_phase_raises(
        self, hand_state: HandState, community_card1: Card
    ) -> None:
        """Test that getting final hand in BET2_DECISION phase raises error."""
        hand_state.apply_bet1_decision(Decision.RIDE)
        hand_state.reveal_first_community(community_card1)
        hand_state.apply_bet2_decision(Decision.RIDE)

        with pytest.raises(InvalidPhaseError, match="final hand"):
            hand_state.get_final_hand()


class TestDecisionEnum:
    """Tests for the Decision enum."""

    def test_decision_values(self) -> None:
        """Test Decision enum values."""
        assert Decision.RIDE.value == "ride"
        assert Decision.PULL.value == "pull"

    def test_decision_members(self) -> None:
        """Test Decision enum has exactly 2 members."""
        assert len(Decision) == 2


class TestHandPhaseEnum:
    """Tests for the HandPhase enum."""

    def test_phase_values(self) -> None:
        """Test HandPhase enum values."""
        assert HandPhase.DEAL.value == "deal"
        assert HandPhase.BET1_DECISION.value == "bet1_decision"
        assert HandPhase.FIRST_REVEAL.value == "first_reveal"
        assert HandPhase.BET2_DECISION.value == "bet2_decision"
        assert HandPhase.SECOND_REVEAL.value == "second_reveal"
        assert HandPhase.RESOLVED.value == "resolved"

    def test_phase_members(self) -> None:
        """Test HandPhase enum has exactly 6 members."""
        assert len(HandPhase) == 6
