"""Unit tests for Card, Rank, and Suit classes."""

import pytest

from let_it_ride.core.card import Card, Rank, Suit


class TestRank:
    """Tests for the Rank enum."""

    def test_rank_values(self) -> None:
        """Verify all ranks have correct integer values."""
        assert Rank.TWO.value == 2
        assert Rank.THREE.value == 3
        assert Rank.FOUR.value == 4
        assert Rank.FIVE.value == 5
        assert Rank.SIX.value == 6
        assert Rank.SEVEN.value == 7
        assert Rank.EIGHT.value == 8
        assert Rank.NINE.value == 9
        assert Rank.TEN.value == 10
        assert Rank.JACK.value == 11
        assert Rank.QUEEN.value == 12
        assert Rank.KING.value == 13
        assert Rank.ACE.value == 14

    def test_rank_count(self) -> None:
        """Verify there are exactly 13 ranks."""
        assert len(Rank) == 13

    def test_rank_ordering_less_than(self) -> None:
        """Verify rank less-than comparison (ACE high by default)."""
        assert Rank.TWO < Rank.THREE
        assert Rank.TEN < Rank.JACK
        assert Rank.KING < Rank.ACE
        assert not Rank.ACE < Rank.KING

    def test_rank_ordering_greater_than(self) -> None:
        """Verify rank greater-than comparison (ACE high by default)."""
        assert Rank.ACE > Rank.KING
        assert Rank.JACK > Rank.TEN
        assert Rank.THREE > Rank.TWO
        assert not Rank.TWO > Rank.THREE

    def test_rank_ordering_less_than_or_equal(self) -> None:
        """Verify rank less-than-or-equal comparison."""
        assert Rank.TWO <= Rank.TWO
        assert Rank.TWO <= Rank.THREE
        assert not Rank.ACE <= Rank.KING

    def test_rank_ordering_greater_than_or_equal(self) -> None:
        """Verify rank greater-than-or-equal comparison."""
        assert Rank.ACE >= Rank.ACE
        assert Rank.ACE >= Rank.KING
        assert not Rank.TWO >= Rank.THREE

    def test_rank_str_representation(self) -> None:
        """Verify string representation of ranks."""
        assert str(Rank.TWO) == "2"
        assert str(Rank.NINE) == "9"
        assert str(Rank.TEN) == "T"
        assert str(Rank.JACK) == "J"
        assert str(Rank.QUEEN) == "Q"
        assert str(Rank.KING) == "K"
        assert str(Rank.ACE) == "A"

    def test_rank_comparison_with_non_rank_returns_not_implemented(self) -> None:
        """Verify comparison with non-Rank returns NotImplemented."""
        assert Rank.ACE.__lt__(5) == NotImplemented
        assert Rank.ACE.__le__(5) == NotImplemented
        assert Rank.ACE.__gt__(5) == NotImplemented
        assert Rank.ACE.__ge__(5) == NotImplemented

    def test_ace_low_value(self) -> None:
        """Verify ACE low_value returns 1, other ranks return standard value."""
        assert Rank.ACE.low_value() == 1
        assert Rank.TWO.low_value() == 2
        assert Rank.KING.low_value() == 13
        assert Rank.TEN.low_value() == 10

    def test_ace_compare_ace_low(self) -> None:
        """Verify compare_ace_low treats ACE as less than TWO."""
        # ACE (low=1) < TWO (low=2)
        assert Rank.ACE.compare_ace_low(Rank.TWO) < 0
        assert Rank.TWO.compare_ace_low(Rank.ACE) > 0

        # ACE (low=1) < KING (low=13)
        assert Rank.ACE.compare_ace_low(Rank.KING) < 0
        assert Rank.KING.compare_ace_low(Rank.ACE) > 0

        # Other ranks compare normally
        assert Rank.TWO.compare_ace_low(Rank.THREE) < 0
        assert Rank.KING.compare_ace_low(Rank.QUEEN) > 0

        # Equal ranks
        assert Rank.ACE.compare_ace_low(Rank.ACE) == 0
        assert Rank.FIVE.compare_ace_low(Rank.FIVE) == 0


class TestSuit:
    """Tests for the Suit enum."""

    def test_suit_values(self) -> None:
        """Verify all suits have correct single-character values."""
        assert Suit.CLUBS.value == "c"
        assert Suit.DIAMONDS.value == "d"
        assert Suit.HEARTS.value == "h"
        assert Suit.SPADES.value == "s"

    def test_suit_count(self) -> None:
        """Verify there are exactly 4 suits."""
        assert len(Suit) == 4

    def test_suit_no_ordering(self) -> None:
        """Verify suits have no inherent ordering (comparison raises TypeError)."""
        # Enums without custom comparison methods will raise TypeError
        with pytest.raises(TypeError):
            _ = Suit.CLUBS < Suit.DIAMONDS  # type: ignore[operator]


class TestCard:
    """Tests for the Card dataclass."""

    def test_card_creation(self) -> None:
        """Verify card can be created with rank and suit."""
        card = Card(Rank.ACE, Suit.SPADES)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES

    def test_card_immutability(self) -> None:
        """Verify card is immutable (frozen dataclass)."""
        card = Card(Rank.ACE, Suit.SPADES)
        with pytest.raises(AttributeError):
            card.rank = Rank.KING  # type: ignore[misc]
        with pytest.raises(AttributeError):
            card.suit = Suit.HEARTS  # type: ignore[misc]

    def test_card_equality(self) -> None:
        """Verify card equality comparison."""
        card1 = Card(Rank.ACE, Suit.SPADES)
        card2 = Card(Rank.ACE, Suit.SPADES)
        card3 = Card(Rank.ACE, Suit.HEARTS)
        card4 = Card(Rank.KING, Suit.SPADES)

        assert card1 == card2
        assert card1 != card3
        assert card1 != card4

    def test_card_equality_with_non_card(self) -> None:
        """Verify card inequality with non-Card objects."""
        card = Card(Rank.ACE, Suit.SPADES)
        assert card != "As"
        assert card != 14
        assert card != (Rank.ACE, Suit.SPADES)

    def test_card_ordering_by_rank(self) -> None:
        """Verify cards are ordered by rank (ACE high by default)."""
        ace_spades = Card(Rank.ACE, Suit.SPADES)
        king_spades = Card(Rank.KING, Suit.SPADES)
        two_spades = Card(Rank.TWO, Suit.SPADES)

        assert two_spades < king_spades < ace_spades
        assert ace_spades > king_spades > two_spades

    def test_card_same_rank_different_suit_comparison(self) -> None:
        """Verify cards with same rank but different suits compare by rank only.

        Since suits have no ordering, cards with equal ranks but different
        suits are neither less than nor greater than each other. They are
        also not equal (since equality requires both rank AND suit to match).
        """
        ace_clubs = Card(Rank.ACE, Suit.CLUBS)
        ace_spades = Card(Rank.ACE, Suit.SPADES)

        # Neither is less than the other (same rank)
        assert not ace_clubs < ace_spades
        assert not ace_spades < ace_clubs

        # Neither is greater than the other (same rank)
        assert not ace_clubs > ace_spades
        assert not ace_spades > ace_clubs

        # They are not equal (different suits)
        assert ace_clubs != ace_spades

    def test_card_ordering_less_than_or_equal(self) -> None:
        """Verify card less-than-or-equal comparison."""
        card1 = Card(Rank.ACE, Suit.SPADES)
        card2 = Card(Rank.ACE, Suit.SPADES)
        card3 = Card(Rank.KING, Suit.SPADES)

        assert card1 <= card2
        assert card3 <= card1
        assert not card1 <= card3

    def test_card_ordering_greater_than_or_equal(self) -> None:
        """Verify card greater-than-or-equal comparison."""
        card1 = Card(Rank.ACE, Suit.SPADES)
        card2 = Card(Rank.ACE, Suit.SPADES)
        card3 = Card(Rank.KING, Suit.SPADES)

        assert card1 >= card2
        assert card1 >= card3
        assert not card3 >= card1

    def test_card_comparison_with_non_card_returns_not_implemented(self) -> None:
        """Verify comparison with non-Card returns NotImplemented."""
        card = Card(Rank.ACE, Suit.SPADES)
        assert card.__lt__("As") == NotImplemented
        assert card.__le__("As") == NotImplemented
        assert card.__gt__("As") == NotImplemented
        assert card.__ge__("As") == NotImplemented
        assert card.__eq__("As") == NotImplemented

    def test_card_str_representation(self) -> None:
        """Verify string representation of cards."""
        assert str(Card(Rank.ACE, Suit.HEARTS)) == "Ah"
        assert str(Card(Rank.KING, Suit.SPADES)) == "Ks"
        assert str(Card(Rank.TEN, Suit.DIAMONDS)) == "Td"
        assert str(Card(Rank.TWO, Suit.CLUBS)) == "2c"

    def test_card_repr(self) -> None:
        """Verify repr representation of cards."""
        card = Card(Rank.ACE, Suit.HEARTS)
        assert repr(card) == "Card(ACE, HEARTS)"

    def test_card_hashable(self) -> None:
        """Verify cards can be used in sets and as dict keys."""
        card1 = Card(Rank.ACE, Suit.SPADES)
        card2 = Card(Rank.ACE, Suit.SPADES)
        card3 = Card(Rank.KING, Suit.SPADES)

        # Test in set
        card_set = {card1, card2, card3}
        assert len(card_set) == 2

        # Test as dict key
        card_dict = {card1: "ace", card3: "king"}
        assert card_dict[card2] == "ace"

    def test_all_52_cards_unique(self) -> None:
        """Verify all 52 rank/suit combinations produce unique cards."""
        all_cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        assert len(all_cards) == 52
        assert len(set(all_cards)) == 52
