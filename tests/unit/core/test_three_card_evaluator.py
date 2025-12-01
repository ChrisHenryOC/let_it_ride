"""Unit tests for three-card hand evaluation (bonus bet)."""

from itertools import combinations

import pytest

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.three_card_evaluator import (
    ThreeCardHandRank,
    evaluate_three_card_hand,
)
from tests.fixtures.three_card_samples import (
    ALL_THREE_CARD_SAMPLES,
    FLUSH_SAMPLES,
    HIGH_CARD_SAMPLES,
    INVALID_STRAIGHT_SAMPLES,
    MINI_ROYAL_SAMPLES,
    PAIR_SAMPLES,
    STRAIGHT_FLUSH_SAMPLES,
    STRAIGHT_SAMPLES,
    THREE_OF_A_KIND_SAMPLES,
    make_three_card_hand,
)


class TestThreeCardHandRank:
    """Tests for ThreeCardHandRank enum ordering."""

    def test_mini_royal_is_highest(self) -> None:
        """Mini Royal should be the highest ranked hand."""
        assert ThreeCardHandRank.MINI_ROYAL.value == 7
        assert ThreeCardHandRank.MINI_ROYAL > ThreeCardHandRank.STRAIGHT_FLUSH
        assert ThreeCardHandRank.MINI_ROYAL > ThreeCardHandRank.HIGH_CARD

    def test_high_card_is_lowest(self) -> None:
        """High card should be the lowest ranked hand."""
        assert ThreeCardHandRank.HIGH_CARD.value == 1
        assert ThreeCardHandRank.HIGH_CARD < ThreeCardHandRank.PAIR

    def test_full_ordering(self) -> None:
        """All hand ranks should be properly ordered."""
        ordered_ranks = [
            ThreeCardHandRank.HIGH_CARD,
            ThreeCardHandRank.PAIR,
            ThreeCardHandRank.FLUSH,
            ThreeCardHandRank.STRAIGHT,
            ThreeCardHandRank.THREE_OF_A_KIND,
            ThreeCardHandRank.STRAIGHT_FLUSH,
            ThreeCardHandRank.MINI_ROYAL,
        ]
        for i in range(len(ordered_ranks) - 1):
            assert ordered_ranks[i] < ordered_ranks[i + 1]

    def test_comparison_operators(self) -> None:
        """All comparison operators should work correctly."""
        mini = ThreeCardHandRank.MINI_ROYAL
        high = ThreeCardHandRank.HIGH_CARD

        assert mini > high
        assert mini >= high
        assert high < mini
        assert high <= mini
        assert not mini < high
        assert not high > mini

        # Equal comparison
        assert mini >= mini
        assert mini <= mini


class TestEvaluateThreeCardHand:
    """Tests for evaluate_three_card_hand function."""

    def test_rejects_wrong_card_count(self) -> None:
        """Should raise ValueError if not exactly 3 cards."""
        with pytest.raises(ValueError, match="Expected 3 cards"):
            evaluate_three_card_hand([Card(Rank.ACE, Suit.HEARTS)])

        with pytest.raises(ValueError, match="Expected 3 cards"):
            evaluate_three_card_hand([])

        two_cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS),
        ]
        with pytest.raises(ValueError, match="Expected 3 cards"):
            evaluate_three_card_hand(two_cards)

        four_cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
        ]
        with pytest.raises(ValueError, match="Expected 3 cards"):
            evaluate_three_card_hand(four_cards)



class TestMiniRoyal:
    """Tests for Mini Royal detection."""

    @pytest.mark.parametrize("hand,expected_rank", MINI_ROYAL_SAMPLES)
    def test_mini_royal_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """Mini Royal (AKQ suited) should be correctly identified."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank

    def test_all_four_mini_royals(self) -> None:
        """All four suits should produce Mini Royals."""
        for suit in Suit:
            hand = [
                Card(Rank.ACE, suit),
                Card(Rank.KING, suit),
                Card(Rank.QUEEN, suit),
            ]
            result = evaluate_three_card_hand(hand)
            assert result == ThreeCardHandRank.MINI_ROYAL


class TestStraightFlush:
    """Tests for Straight Flush detection."""

    @pytest.mark.parametrize("hand,expected_rank", STRAIGHT_FLUSH_SAMPLES)
    def test_straight_flush_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """Straight flush should be correctly identified."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank

    def test_wheel_straight_flush(self) -> None:
        """A-2-3 suited should be straight flush, not Mini Royal."""
        hand = make_three_card_hand("Ah 2h 3h")
        result = evaluate_three_card_hand(hand)
        assert result == ThreeCardHandRank.STRAIGHT_FLUSH

    def test_akq_suited_is_mini_royal_not_straight_flush(self) -> None:
        """AKQ suited should be Mini Royal, not just Straight Flush."""
        hand = make_three_card_hand("Ah Kh Qh")
        result = evaluate_three_card_hand(hand)
        assert result == ThreeCardHandRank.MINI_ROYAL
        assert result != ThreeCardHandRank.STRAIGHT_FLUSH


class TestThreeOfAKind:
    """Tests for Three of a Kind detection."""

    @pytest.mark.parametrize("hand,expected_rank", THREE_OF_A_KIND_SAMPLES)
    def test_three_of_a_kind_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """Three of a kind should be correctly identified."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank

    def test_all_thirteen_three_of_a_kinds(self) -> None:
        """All 13 ranks should produce three of a kind."""
        suits = [Suit.HEARTS, Suit.SPADES, Suit.DIAMONDS]
        for rank in Rank:
            hand = [Card(rank, suit) for suit in suits]
            result = evaluate_three_card_hand(hand)
            assert result == ThreeCardHandRank.THREE_OF_A_KIND


class TestStraight:
    """Tests for Straight detection."""

    @pytest.mark.parametrize("hand,expected_rank", STRAIGHT_SAMPLES)
    def test_straight_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """Straight should be correctly identified."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank

    def test_wheel_is_straight(self) -> None:
        """A-2-3 offsuit should be a straight."""
        hand = make_three_card_hand("Ah 2s 3d")
        result = evaluate_three_card_hand(hand)
        assert result == ThreeCardHandRank.STRAIGHT

    def test_broadway_is_straight(self) -> None:
        """A-K-Q offsuit should be a straight."""
        hand = make_three_card_hand("Ah Ks Qd")
        result = evaluate_three_card_hand(hand)
        assert result == ThreeCardHandRank.STRAIGHT


class TestInvalidStraights:
    """Tests for hands that should NOT be straights."""

    @pytest.mark.parametrize("hand,expected_rank", INVALID_STRAIGHT_SAMPLES)
    def test_invalid_straight_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """Invalid straights should be correctly identified as high card."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank

    def test_wraparound_is_not_straight(self) -> None:
        """K-A-2 is NOT a straight (no wraparound)."""
        hand = make_three_card_hand("Kh As 2d")
        result = evaluate_three_card_hand(hand)
        assert result == ThreeCardHandRank.HIGH_CARD

    def test_qa2_is_not_straight(self) -> None:
        """Q-A-2 is NOT a straight."""
        hand = make_three_card_hand("Qh As 2d")
        result = evaluate_three_card_hand(hand)
        assert result == ThreeCardHandRank.HIGH_CARD

    def test_gap_in_middle_is_not_straight(self) -> None:
        """Cards with gap (A-3-5) should NOT be a straight."""
        hand = make_three_card_hand("Ah 3s 5d")
        result = evaluate_three_card_hand(hand)
        assert result == ThreeCardHandRank.HIGH_CARD


class TestFlush:
    """Tests for Flush detection."""

    @pytest.mark.parametrize("hand,expected_rank", FLUSH_SAMPLES)
    def test_flush_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """Flush should be correctly identified."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank

    def test_flush_not_straight(self) -> None:
        """Non-consecutive suited cards should be flush only."""
        hand = make_three_card_hand("Ah Kh 9h")  # Gap means not straight
        result = evaluate_three_card_hand(hand)
        assert result == ThreeCardHandRank.FLUSH


class TestPair:
    """Tests for Pair detection."""

    @pytest.mark.parametrize("hand,expected_rank", PAIR_SAMPLES)
    def test_pair_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """Pair should be correctly identified."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank


class TestHighCard:
    """Tests for High Card detection."""

    @pytest.mark.parametrize("hand,expected_rank", HIGH_CARD_SAMPLES)
    def test_high_card_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """High card should be correctly identified."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank


class TestAllSamples:
    """Verify all samples are correctly identified."""

    @pytest.mark.parametrize("hand,expected_rank", ALL_THREE_CARD_SAMPLES)
    def test_all_samples(
        self,
        hand: list[Card],
        expected_rank: ThreeCardHandRank,
    ) -> None:
        """All sample hands should be correctly evaluated."""
        result = evaluate_three_card_hand(hand)
        assert result == expected_rank


class TestProbabilityValidation:
    """Validate hand distribution against known probabilities.

    Total 3-card combinations from 52 cards: C(52,3) = 22,100

    Reference probabilities:
    | Hand | Combinations | Probability |
    |------|--------------|-------------|
    | Mini Royal | 4 | 0.0181% |
    | Straight Flush | 44 | 0.199% |
    | Three of a Kind | 52 | 0.235% |
    | Straight | 720 | 3.26% |
    | Flush | 1,096 | 4.96% |
    | Pair | 3,744 | 16.94% |
    | High Card | 16,440 | 74.39% |
    """

    @pytest.mark.slow
    def test_hand_distribution_matches_probabilities(self) -> None:
        """Enumerate all 22,100 combinations and verify distribution."""
        # Create all 52 cards
        all_cards = [Card(rank, suit) for suit in Suit for rank in Rank]

        counts: dict[ThreeCardHandRank, int] = {rank: 0 for rank in ThreeCardHandRank}

        for combo in combinations(all_cards, 3):
            hand_rank = evaluate_three_card_hand(combo)
            counts[hand_rank] += 1

        total = sum(counts.values())
        assert total == 22100, f"Expected 22,100 combinations, got {total}"

        # Verify exact counts match reference probabilities
        assert counts[ThreeCardHandRank.MINI_ROYAL] == 4
        assert counts[ThreeCardHandRank.STRAIGHT_FLUSH] == 44
        assert counts[ThreeCardHandRank.THREE_OF_A_KIND] == 52
        assert counts[ThreeCardHandRank.STRAIGHT] == 720
        assert counts[ThreeCardHandRank.FLUSH] == 1096
        assert counts[ThreeCardHandRank.PAIR] == 3744
        assert counts[ThreeCardHandRank.HIGH_CARD] == 16440

    def test_total_combinations_is_22100(self) -> None:
        """Verify total 3-card combinations from 52 cards is 22,100."""
        # C(52,3) = 52! / (3! * 49!) = 52 * 51 * 50 / 6 = 22100
        expected = 52 * 51 * 50 // 6
        assert expected == 22100
