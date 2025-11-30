"""Unit tests for Deck class."""

import random
from collections import Counter

import pytest
from scipy import stats

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.deck import Deck, DeckEmptyError


class TestDeckInitialization:
    """Tests for Deck initialization."""

    def test_deck_has_52_cards(self) -> None:
        """Verify a new deck has 52 cards."""
        deck = Deck()
        assert deck.cards_remaining() == 52
        assert len(deck) == 52

    def test_deck_has_no_dealt_cards(self) -> None:
        """Verify a new deck has no dealt cards."""
        deck = Deck()
        assert deck.dealt_cards() == []

    def test_deck_contains_all_unique_cards(self) -> None:
        """Verify a new deck contains all 52 unique cards."""
        deck = Deck()
        all_cards = deck.deal(52)
        assert len(set(all_cards)) == 52

    def test_deck_contains_all_ranks_and_suits(self) -> None:
        """Verify deck contains all rank/suit combinations."""
        deck = Deck()
        all_cards = set(deck.deal(52))

        for suit in Suit:
            for rank in Rank:
                assert Card(rank, suit) in all_cards


class TestDeckShuffle:
    """Tests for Deck shuffle method."""

    def test_shuffle_changes_card_order(self, rng: random.Random) -> None:
        """Verify shuffle changes the order of cards."""
        deck1 = Deck()
        deck2 = Deck()

        deck2.shuffle(rng)

        # Deal all cards from both decks
        cards1 = deck1.deal(52)
        deck2.reset()  # Reset deck2 since we shuffled it
        deck2.shuffle(random.Random(42))
        cards2 = deck2.deal(52)

        # The shuffled order should be different
        assert cards1 != cards2

    def test_shuffle_preserves_all_cards(self, rng: random.Random) -> None:
        """Verify shuffle doesn't lose or duplicate cards."""
        deck = Deck()
        deck.shuffle(rng)

        all_cards = deck.deal(52)
        assert len(all_cards) == 52
        assert len(set(all_cards)) == 52

    def test_shuffle_with_same_seed_produces_same_order(self) -> None:
        """Verify shuffling with same seed is reproducible."""
        deck1 = Deck()
        deck2 = Deck()

        deck1.shuffle(random.Random(12345))
        deck2.shuffle(random.Random(12345))

        cards1 = deck1.deal(52)
        cards2 = deck2.deal(52)

        assert cards1 == cards2

    def test_shuffle_with_different_seeds_produces_different_order(self) -> None:
        """Verify shuffling with different seeds produces different orders."""
        deck1 = Deck()
        deck2 = Deck()

        deck1.shuffle(random.Random(12345))
        deck2.shuffle(random.Random(54321))

        cards1 = deck1.deal(52)
        cards2 = deck2.deal(52)

        assert cards1 != cards2

    def test_shuffle_only_shuffles_remaining_cards(self, rng: random.Random) -> None:
        """Verify shuffle only affects cards still in deck."""
        deck = Deck()
        deck.shuffle(rng)

        # Deal some cards
        dealt = deck.deal(10)
        remaining_before = deck.cards_remaining()

        # Shuffle again
        deck.shuffle(rng)

        # Should still have same number remaining
        assert deck.cards_remaining() == remaining_before

        # Dealt cards should not be back in deck
        remaining_cards = deck.deal(deck.cards_remaining())
        for card in dealt:
            assert card not in remaining_cards


class TestDeckDeal:
    """Tests for Deck deal method."""

    def test_deal_returns_correct_count(self, rng: random.Random) -> None:
        """Verify deal returns the requested number of cards."""
        deck = Deck()
        deck.shuffle(rng)

        cards = deck.deal(5)
        assert len(cards) == 5

    def test_deal_default_is_one(self, rng: random.Random) -> None:
        """Verify deal() with no argument returns one card."""
        deck = Deck()
        deck.shuffle(rng)

        cards = deck.deal()
        assert len(cards) == 1

    def test_deal_removes_cards_from_deck(self, rng: random.Random) -> None:
        """Verify dealt cards are removed from the deck."""
        deck = Deck()
        deck.shuffle(rng)

        initial_count = deck.cards_remaining()
        deck.deal(5)
        assert deck.cards_remaining() == initial_count - 5

    def test_deal_adds_to_dealt_cards(self, rng: random.Random) -> None:
        """Verify dealt cards are tracked."""
        deck = Deck()
        deck.shuffle(rng)

        dealt = deck.deal(5)
        assert deck.dealt_cards() == dealt

    def test_deal_accumulates_dealt_cards(self, rng: random.Random) -> None:
        """Verify multiple deals accumulate in dealt_cards."""
        deck = Deck()
        deck.shuffle(rng)

        first_deal = deck.deal(3)
        second_deal = deck.deal(2)

        assert deck.dealt_cards() == first_deal + second_deal

    def test_deal_raises_on_empty_deck(self, rng: random.Random) -> None:
        """Verify deal raises DeckEmptyError when deck is empty."""
        deck = Deck()
        deck.shuffle(rng)
        deck.deal(52)

        with pytest.raises(DeckEmptyError) as exc_info:
            deck.deal(1)

        assert "Cannot deal 1 cards, only 0 remaining" in str(exc_info.value)

    def test_deal_raises_on_insufficient_cards(self, rng: random.Random) -> None:
        """Verify deal raises DeckEmptyError when not enough cards."""
        deck = Deck()
        deck.shuffle(rng)
        deck.deal(50)

        with pytest.raises(DeckEmptyError) as exc_info:
            deck.deal(5)

        assert "Cannot deal 5 cards, only 2 remaining" in str(exc_info.value)

    def test_deal_raises_on_invalid_count(self, rng: random.Random) -> None:
        """Verify deal raises ValueError for count < 1."""
        deck = Deck()
        deck.shuffle(rng)

        with pytest.raises(ValueError) as exc_info:
            deck.deal(0)
        assert "Count must be at least 1" in str(exc_info.value)

        with pytest.raises(ValueError):
            deck.deal(-1)


class TestDeckReset:
    """Tests for Deck reset method."""

    def test_reset_restores_all_cards(self, rng: random.Random) -> None:
        """Verify reset restores deck to 52 cards."""
        deck = Deck()
        deck.shuffle(rng)
        deck.deal(30)

        deck.reset()

        assert deck.cards_remaining() == 52

    def test_reset_clears_dealt_cards(self, rng: random.Random) -> None:
        """Verify reset clears the dealt cards list."""
        deck = Deck()
        deck.shuffle(rng)
        deck.deal(10)

        deck.reset()

        assert deck.dealt_cards() == []

    def test_reset_returns_deck_to_unshuffled_state(self, rng: random.Random) -> None:
        """Verify reset returns deck to standard order."""
        deck1 = Deck()
        deck2 = Deck()

        deck2.shuffle(rng)
        deck2.deal(20)
        deck2.reset()

        # Both decks should now have cards in standard order
        cards1 = deck1.deal(52)
        cards2 = deck2.deal(52)

        assert cards1 == cards2


class TestDeckDealtCards:
    """Tests for dealt_cards method."""

    def test_dealt_cards_returns_copy(self, rng: random.Random) -> None:
        """Verify dealt_cards returns a copy, not the internal list."""
        deck = Deck()
        deck.shuffle(rng)
        deck.deal(5)

        dealt = deck.dealt_cards()
        dealt.clear()

        # Internal list should not be affected
        assert len(deck.dealt_cards()) == 5


class TestDeckRepr:
    """Tests for Deck string representation."""

    def test_repr_new_deck(self) -> None:
        """Verify repr of new deck."""
        deck = Deck()
        assert repr(deck) == "Deck(remaining=52, dealt=0)"

    def test_repr_after_dealing(self, rng: random.Random) -> None:
        """Verify repr after dealing cards."""
        deck = Deck()
        deck.shuffle(rng)
        deck.deal(10)

        assert repr(deck) == "Deck(remaining=42, dealt=10)"


class TestShuffleDistribution:
    """Statistical tests for shuffle uniformity using chi-square test."""

    def test_shuffle_produces_uniform_distribution(self) -> None:
        """Verify Fisher-Yates shuffle produces uniform distribution.

        This test shuffles the deck many times and counts how often each
        card appears in each position. A chi-square test verifies the
        distribution is uniform (each card equally likely in each position).
        """
        num_shuffles = 10000
        deck_size = 52

        # Track position counts: position_counts[position][card] = count
        # For efficiency, we use a simpler approach: track first position only
        # If first position is uniform, Fisher-Yates guarantees all are
        first_position_counts: Counter[Card] = Counter()

        deck = Deck()

        for seed in range(num_shuffles):
            deck.reset()
            deck.shuffle(random.Random(seed))
            first_card = deck.deal(1)[0]
            first_position_counts[first_card] += 1

        # Perform chi-square test
        observed = list(first_position_counts.values())

        # All 52 cards should have appeared at least once
        assert len(observed) == deck_size

        chi2, p_value = stats.chisquare(observed)

        # With 51 degrees of freedom and alpha=0.01, the critical value is ~76.15
        # We use p-value > 0.01 to ensure uniform distribution
        assert (
            p_value > 0.01
        ), f"Shuffle distribution is not uniform (chi2={chi2:.2f}, p={p_value:.4f})"

    def test_shuffle_all_positions_uniform(self) -> None:
        """Verify all positions have uniform distribution.

        This test is more comprehensive but slower. It checks that each
        position in the deck receives each card with equal probability.
        """
        num_shuffles = 5000
        deck_size = 52

        # Use a smaller sample of positions to check (0, 25, 51)
        positions_to_check = [0, 25, 51]
        position_counts: dict[int, Counter[Card]] = {
            pos: Counter() for pos in positions_to_check
        }

        deck = Deck()

        for seed in range(num_shuffles):
            deck.reset()
            deck.shuffle(random.Random(seed))
            cards = deck.deal(52)

            for pos in positions_to_check:
                position_counts[pos][cards[pos]] += 1

        # Check each position's distribution
        for pos in positions_to_check:
            observed = list(position_counts[pos].values())
            assert len(observed) == deck_size, f"Position {pos} missing cards"

            chi2, p_value = stats.chisquare(observed)
            assert p_value > 0.01, (
                f"Position {pos} distribution not uniform "
                f"(chi2={chi2:.2f}, p={p_value:.4f})"
            )
