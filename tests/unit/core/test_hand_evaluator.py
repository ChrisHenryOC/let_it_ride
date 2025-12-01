"""Unit tests for five-card hand evaluation."""

import time

import pytest

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_evaluator import (
    FiveCardHandRank,
    HandResult,
    evaluate_five_card_hand,
)
from tests.fixtures.hand_samples import (
    ALL_HAND_SAMPLES,
    FLUSH_SAMPLES,
    FOUR_OF_A_KIND_SAMPLES,
    FULL_HOUSE_SAMPLES,
    HIGH_CARD_SAMPLES,
    PAIR_BELOW_TENS_SAMPLES,
    PAIR_TENS_OR_BETTER_SAMPLES,
    ROYAL_FLUSH_SAMPLES,
    STRAIGHT_FLUSH_SAMPLES,
    STRAIGHT_SAMPLES,
    THREE_OF_A_KIND_SAMPLES,
    TWO_PAIR_SAMPLES,
    make_hand,
)


class TestFiveCardHandRank:
    """Tests for FiveCardHandRank enum ordering."""

    def test_royal_flush_is_highest(self) -> None:
        """Royal flush should be the highest ranked hand."""
        assert FiveCardHandRank.ROYAL_FLUSH.value == 10
        assert FiveCardHandRank.ROYAL_FLUSH > FiveCardHandRank.STRAIGHT_FLUSH
        assert FiveCardHandRank.ROYAL_FLUSH > FiveCardHandRank.HIGH_CARD

    def test_high_card_is_lowest(self) -> None:
        """High card should be the lowest ranked hand."""
        assert FiveCardHandRank.HIGH_CARD.value == 0
        assert FiveCardHandRank.HIGH_CARD < FiveCardHandRank.PAIR_BELOW_TENS

    def test_pair_tens_or_better_beats_pair_below_tens(self) -> None:
        """Pair of 10+ should beat pair of 2-9."""
        assert FiveCardHandRank.PAIR_TENS_OR_BETTER > FiveCardHandRank.PAIR_BELOW_TENS

    def test_full_ordering(self) -> None:
        """All hand ranks should be properly ordered."""
        ordered_ranks = [
            FiveCardHandRank.HIGH_CARD,
            FiveCardHandRank.PAIR_BELOW_TENS,
            FiveCardHandRank.PAIR_TENS_OR_BETTER,
            FiveCardHandRank.TWO_PAIR,
            FiveCardHandRank.THREE_OF_A_KIND,
            FiveCardHandRank.STRAIGHT,
            FiveCardHandRank.FLUSH,
            FiveCardHandRank.FULL_HOUSE,
            FiveCardHandRank.FOUR_OF_A_KIND,
            FiveCardHandRank.STRAIGHT_FLUSH,
            FiveCardHandRank.ROYAL_FLUSH,
        ]
        for i in range(len(ordered_ranks) - 1):
            assert ordered_ranks[i] < ordered_ranks[i + 1]


class TestHandResult:
    """Tests for HandResult dataclass."""

    def test_hand_result_comparison_by_rank(self) -> None:
        """HandResults should compare first by rank."""
        flush = HandResult(
            rank=FiveCardHandRank.FLUSH,
            primary_cards=(Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK, Rank.NINE),
            kickers=(),
        )
        straight = HandResult(
            rank=FiveCardHandRank.STRAIGHT,
            primary_cards=(Rank.ACE,),
            kickers=(),
        )
        assert flush > straight
        assert straight < flush

    def test_hand_result_comparison_by_primary_cards(self) -> None:
        """Equal rank hands should compare by primary cards."""
        high_pair = HandResult(
            rank=FiveCardHandRank.PAIR_TENS_OR_BETTER,
            primary_cards=(Rank.ACE,),
            kickers=(Rank.KING, Rank.QUEEN, Rank.JACK),
        )
        low_pair = HandResult(
            rank=FiveCardHandRank.PAIR_TENS_OR_BETTER,
            primary_cards=(Rank.TEN,),
            kickers=(Rank.KING, Rank.QUEEN, Rank.JACK),
        )
        assert high_pair > low_pair
        assert low_pair < high_pair

    def test_hand_result_comparison_by_kickers(self) -> None:
        """Equal rank and primary should compare by kickers."""
        better_kicker = HandResult(
            rank=FiveCardHandRank.PAIR_TENS_OR_BETTER,
            primary_cards=(Rank.ACE,),
            kickers=(Rank.KING, Rank.QUEEN, Rank.JACK),
        )
        worse_kicker = HandResult(
            rank=FiveCardHandRank.PAIR_TENS_OR_BETTER,
            primary_cards=(Rank.ACE,),
            kickers=(Rank.KING, Rank.QUEEN, Rank.TEN),
        )
        assert better_kicker > worse_kicker

    def test_hand_result_equality(self) -> None:
        """Identical HandResults should be equal."""
        result1 = HandResult(
            rank=FiveCardHandRank.FLUSH,
            primary_cards=(Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK, Rank.NINE),
            kickers=(),
        )
        result2 = HandResult(
            rank=FiveCardHandRank.FLUSH,
            primary_cards=(Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK, Rank.NINE),
            kickers=(),
        )
        assert result1 == result2
        assert result1 <= result2
        assert result1 >= result2

    def test_hand_result_is_frozen(self) -> None:
        """HandResult should be immutable."""
        result = HandResult(
            rank=FiveCardHandRank.HIGH_CARD,
            primary_cards=(Rank.ACE,),
            kickers=(Rank.KING,),
        )
        with pytest.raises(AttributeError):
            result.rank = FiveCardHandRank.FLUSH  # type: ignore[misc]


class TestEvaluateFiveCardHand:
    """Tests for evaluate_five_card_hand function."""

    def test_rejects_wrong_card_count(self) -> None:
        """Should raise ValueError if not exactly 5 cards."""
        with pytest.raises(ValueError, match="Expected 5 cards"):
            evaluate_five_card_hand([Card(Rank.ACE, Suit.HEARTS)])

        with pytest.raises(ValueError, match="Expected 5 cards"):
            evaluate_five_card_hand([])

        four_cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
        ]
        with pytest.raises(ValueError, match="Expected 5 cards"):
            evaluate_five_card_hand(four_cards)

    def test_rejects_duplicate_cards(self) -> None:
        """Should raise ValueError if duplicate cards are provided."""
        duplicate_cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.ACE, Suit.HEARTS),  # duplicate
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
        ]
        with pytest.raises(ValueError, match="Duplicate cards"):
            evaluate_five_card_hand(duplicate_cards)


class TestRoyalFlush:
    """Tests for Royal Flush detection."""

    @pytest.mark.parametrize("hand,expected_rank,expected_primary", ROYAL_FLUSH_SAMPLES)
    def test_royal_flush_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Royal flush should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary
        assert result.kickers == ()

    def test_all_four_royal_flushes(self) -> None:
        """All four suits should produce royal flushes."""
        for suit in Suit:
            hand = [
                Card(Rank.ACE, suit),
                Card(Rank.KING, suit),
                Card(Rank.QUEEN, suit),
                Card(Rank.JACK, suit),
                Card(Rank.TEN, suit),
            ]
            result = evaluate_five_card_hand(hand)
            assert result.rank == FiveCardHandRank.ROYAL_FLUSH


class TestStraightFlush:
    """Tests for Straight Flush detection."""

    @pytest.mark.parametrize(
        "hand,expected_rank,expected_primary", STRAIGHT_FLUSH_SAMPLES
    )
    def test_straight_flush_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Straight flush should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_steel_wheel_is_straight_flush(self) -> None:
        """A-2-3-4-5 suited (steel wheel) should be straight flush with 5 high."""
        hand = make_hand("Ah 2h 3h 4h 5h")
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.STRAIGHT_FLUSH
        assert result.primary_cards == (Rank.FIVE,)  # Five is high in wheel


class TestFourOfAKind:
    """Tests for Four of a Kind detection."""

    @pytest.mark.parametrize(
        "hand,expected_rank,expected_primary", FOUR_OF_A_KIND_SAMPLES
    )
    def test_four_of_a_kind_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Four of a kind should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_four_of_a_kind_kicker(self) -> None:
        """Four of a kind should have one kicker."""
        hand = make_hand("Ah As Ad Ac Kh")
        result = evaluate_five_card_hand(hand)
        assert result.kickers == (Rank.KING,)


class TestFullHouse:
    """Tests for Full House detection."""

    @pytest.mark.parametrize("hand,expected_rank,expected_primary", FULL_HOUSE_SAMPLES)
    def test_full_house_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Full house should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary
        assert result.kickers == ()  # No kickers in full house

    def test_full_house_trips_over_pair(self) -> None:
        """Full house should list trips rank before pair rank."""
        hand = make_hand("2h 2s 2d Ah As")
        result = evaluate_five_card_hand(hand)
        # Twos are trips, Aces are pair
        assert result.primary_cards == (Rank.TWO, Rank.ACE)


class TestFlush:
    """Tests for Flush detection."""

    @pytest.mark.parametrize("hand,expected_rank,expected_primary", FLUSH_SAMPLES)
    def test_flush_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Flush should be correctly identified with cards sorted high to low."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_flush_not_straight(self) -> None:
        """Non-sequential suited cards should be flush, not straight flush."""
        hand = make_hand("Ah Kh Qh Jh 9h")  # Missing 10
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.FLUSH


class TestStraight:
    """Tests for Straight detection."""

    @pytest.mark.parametrize("hand,expected_rank,expected_primary", STRAIGHT_SAMPLES)
    def test_straight_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Straight should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_wheel_is_straight(self) -> None:
        """A-2-3-4-5 (wheel) should be straight with 5 high."""
        hand = make_hand("Ah 2s 3d 4c 5h")
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.STRAIGHT
        assert result.primary_cards == (Rank.FIVE,)

    def test_broadway_is_straight(self) -> None:
        """A-K-Q-J-10 offsuit should be straight with Ace high."""
        hand = make_hand("Ah Ks Qd Jc Th")
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.STRAIGHT
        assert result.primary_cards == (Rank.ACE,)

    def test_broken_wheel_is_not_straight(self) -> None:
        """A-2-3-4-6 is NOT a straight (broken wheel)."""
        hand = make_hand("Ah 2s 3d 4c 6h")
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.HIGH_CARD

    def test_wraparound_is_not_straight(self) -> None:
        """K-A-2-3-4 is NOT a straight (Ace can't be both high and low)."""
        hand = make_hand("Kh As 2d 3c 4h")
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.HIGH_CARD

    def test_one_gap_is_not_straight(self) -> None:
        """5-6-7-9-10 is NOT a straight (gap in the middle)."""
        hand = make_hand("5h 6s 7d 9c Th")
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.HIGH_CARD


class TestThreeOfAKind:
    """Tests for Three of a Kind detection."""

    @pytest.mark.parametrize(
        "hand,expected_rank,expected_primary", THREE_OF_A_KIND_SAMPLES
    )
    def test_three_of_a_kind_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Three of a kind should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_three_of_a_kind_kickers(self) -> None:
        """Three of a kind should have two kickers sorted high to low."""
        hand = make_hand("Ah As Ad Kh Qh")
        result = evaluate_five_card_hand(hand)
        assert result.kickers == (Rank.KING, Rank.QUEEN)


class TestTwoPair:
    """Tests for Two Pair detection."""

    @pytest.mark.parametrize("hand,expected_rank,expected_primary", TWO_PAIR_SAMPLES)
    def test_two_pair_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Two pair should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_two_pair_ordering(self) -> None:
        """Two pair should list higher pair first."""
        hand = make_hand("2h 2s Ah As Kh")
        result = evaluate_five_card_hand(hand)
        # Aces are higher than twos
        assert result.primary_cards == (Rank.ACE, Rank.TWO)
        assert result.kickers == (Rank.KING,)


class TestPairTensOrBetter:
    """Tests for Pair of 10s or Better detection."""

    @pytest.mark.parametrize(
        "hand,expected_rank,expected_primary", PAIR_TENS_OR_BETTER_SAMPLES
    )
    def test_pair_tens_or_better_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Pair of 10+ should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_pair_of_tens_boundary(self) -> None:
        """Pair of tens is the minimum paying hand."""
        hand = make_hand("Th Ts Ah Kh Qh")
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.PAIR_TENS_OR_BETTER

    def test_pair_kickers(self) -> None:
        """Pair should have three kickers sorted high to low."""
        hand = make_hand("Ah As Kh Qh Jh")
        result = evaluate_five_card_hand(hand)
        assert result.kickers == (Rank.KING, Rank.QUEEN, Rank.JACK)


class TestPairBelowTens:
    """Tests for Pair Below Tens detection (non-paying)."""

    @pytest.mark.parametrize(
        "hand,expected_rank,expected_primary", PAIR_BELOW_TENS_SAMPLES
    )
    def test_pair_below_tens_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """Pair below 10s should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_pair_of_nines_boundary(self) -> None:
        """Pair of nines is just below the paying threshold."""
        hand = make_hand("9h 9s Ah Kh Qh")
        result = evaluate_five_card_hand(hand)
        assert result.rank == FiveCardHandRank.PAIR_BELOW_TENS


class TestHighCard:
    """Tests for High Card detection."""

    @pytest.mark.parametrize("hand,expected_rank,expected_primary", HIGH_CARD_SAMPLES)
    def test_high_card_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """High card should be correctly identified."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary

    def test_high_card_kickers(self) -> None:
        """High card should have four kickers (all but highest)."""
        hand = make_hand("Ah Ks Qd Jc 9h")
        result = evaluate_five_card_hand(hand)
        assert result.kickers == (Rank.KING, Rank.QUEEN, Rank.JACK, Rank.NINE)


class TestAllHandSamples:
    """Verify all samples are correctly identified."""

    @pytest.mark.parametrize("hand,expected_rank,expected_primary", ALL_HAND_SAMPLES)
    def test_all_samples(
        self,
        hand: list[Card],
        expected_rank: FiveCardHandRank,
        expected_primary: tuple[Rank, ...],
    ) -> None:
        """All sample hands should be correctly evaluated."""
        result = evaluate_five_card_hand(hand)
        assert result.rank == expected_rank
        assert result.primary_cards == expected_primary


class TestPerformance:
    """Performance tests for hand evaluation."""

    @pytest.mark.slow
    def test_evaluate_100000_hands_under_one_second(self) -> None:
        """Evaluating 100,000 hands should take less than 1 second.

        Target is <1s on modern hardware; uses 2s threshold for CI variability.
        Use `pytest -m "not slow"` to skip this test in constrained environments.
        """
        # Create a variety of test hands
        test_hands = [
            make_hand("Ah Kh Qh Jh Th"),  # Royal
            make_hand("9h 8h 7h 6h 5h"),  # Straight flush
            make_hand("Ah As Ad Ac Kh"),  # Four of a kind
            make_hand("Ah As Ad Kh Ks"),  # Full house
            make_hand("Ah Kh Qh Jh 9h"),  # Flush
            make_hand("Ah Ks Qd Jc Th"),  # Straight
            make_hand("Ah As Ad Kh Qh"),  # Three of a kind
            make_hand("Ah As Kh Ks Qh"),  # Two pair
            make_hand("Ah As Kh Qh Jh"),  # Pair tens or better
            make_hand("9h 9s Ah Kh Qh"),  # Pair below tens
            make_hand("Ah Ks Qd Jc 9h"),  # High card
        ]

        iterations = 100_000
        hands_per_iter = len(test_hands)

        start_time = time.perf_counter()
        for _ in range(iterations // hands_per_iter + 1):
            for hand in test_hands:
                evaluate_five_card_hand(hand)
        elapsed = time.perf_counter() - start_time

        # We evaluated at least 100,000 hands
        total_evaluated = (iterations // hands_per_iter + 1) * hands_per_iter
        assert total_evaluated >= 100_000

        # Target is <1s; using 2s threshold for CI variability
        assert (
            elapsed < 2.0
        ), f"Target <1s, got {elapsed:.3f}s for {total_evaluated} hands"
