"""Unit tests for hand analysis utilities."""

import pytest

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_analysis import (
    HandAnalysis,
    analyze_four_cards,
    analyze_three_cards,
)
from tests.fixtures.hand_analysis_samples import (
    FOUR_CARD_FLUSH_DRAW_SAMPLES,
    FOUR_CARD_HIGH_PAIR_SAMPLES,
    FOUR_CARD_INSIDE_STRAIGHT_SAMPLES,
    FOUR_CARD_LOW_PAIR_SAMPLES,
    FOUR_CARD_NO_DRAW_SAMPLES,
    FOUR_CARD_OPEN_STRAIGHT_SAMPLES,
    FOUR_CARD_ROYAL_DRAW_SAMPLES,
    FOUR_CARD_TRIPS_SAMPLES,
    FOUR_CARD_TWO_PAIR_SAMPLES,
    THREE_CARD_ALL_HIGH_SAMPLES,
    THREE_CARD_FLUSH_DRAW_SAMPLES,
    THREE_CARD_HIGH_PAIR_SAMPLES,
    THREE_CARD_LOW_PAIR_SAMPLES,
    THREE_CARD_NO_DRAW_SAMPLES,
    THREE_CARD_NO_HIGH_SAMPLES,
    THREE_CARD_ROYAL_DRAW_SAMPLES,
    THREE_CARD_STRAIGHT_DRAW_SAMPLES,
    THREE_CARD_STRAIGHT_FLUSH_DRAW_SAMPLES,
    THREE_CARD_TRIPS_SAMPLES,
    make_hand,
)


class TestHandAnalysisDataclass:
    """Tests for HandAnalysis dataclass."""

    def test_dataclass_is_frozen(self) -> None:
        """HandAnalysis should be immutable (frozen)."""
        analysis = HandAnalysis(
            high_cards=0,
            suited_cards=1,
            connected_cards=1,
            gaps=0,
            has_paying_hand=False,
            has_pair=False,
            has_high_pair=False,
            has_trips=False,
            pair_rank=None,
            is_flush_draw=False,
            is_straight_draw=False,
            is_open_straight_draw=False,
            is_inside_straight_draw=False,
            is_straight_flush_draw=False,
            is_royal_draw=False,
            suited_high_cards=0,
        )
        with pytest.raises(AttributeError):
            analysis.high_cards = 5  # type: ignore[misc]

    def test_dataclass_equality(self) -> None:
        """Equal HandAnalysis objects should be equal."""
        analysis1 = HandAnalysis(
            high_cards=3,
            suited_cards=3,
            connected_cards=3,
            gaps=0,
            has_paying_hand=True,
            has_pair=True,
            has_high_pair=True,
            has_trips=False,
            pair_rank=Rank.ACE,
            is_flush_draw=True,
            is_straight_draw=True,
            is_open_straight_draw=False,
            is_inside_straight_draw=False,
            is_straight_flush_draw=True,
            is_royal_draw=True,
            suited_high_cards=3,
        )
        analysis2 = HandAnalysis(
            high_cards=3,
            suited_cards=3,
            connected_cards=3,
            gaps=0,
            has_paying_hand=True,
            has_pair=True,
            has_high_pair=True,
            has_trips=False,
            pair_rank=Rank.ACE,
            is_flush_draw=True,
            is_straight_draw=True,
            is_open_straight_draw=False,
            is_inside_straight_draw=False,
            is_straight_flush_draw=True,
            is_royal_draw=True,
            suited_high_cards=3,
        )
        assert analysis1 == analysis2


class TestAnalyzeThreeCardsValidation:
    """Tests for analyze_three_cards input validation."""

    def test_rejects_wrong_card_count(self) -> None:
        """Should raise ValueError if not exactly 3 cards."""
        with pytest.raises(ValueError, match="Expected 3 cards"):
            analyze_three_cards([Card(Rank.ACE, Suit.HEARTS)])

        with pytest.raises(ValueError, match="Expected 3 cards"):
            analyze_three_cards([])

        with pytest.raises(ValueError, match="Expected 3 cards"):
            analyze_three_cards(make_hand("Ah Ks Qd Jc"))


class TestAnalyzeFourCardsValidation:
    """Tests for analyze_four_cards input validation."""

    def test_rejects_wrong_card_count(self) -> None:
        """Should raise ValueError if not exactly 4 cards."""
        with pytest.raises(ValueError, match="Expected 4 cards"):
            analyze_four_cards([Card(Rank.ACE, Suit.HEARTS)])

        with pytest.raises(ValueError, match="Expected 4 cards"):
            analyze_four_cards([])

        with pytest.raises(ValueError, match="Expected 4 cards"):
            analyze_four_cards(make_hand("Ah Ks Qd"))


class TestThreeCardTrips:
    """Tests for three of a kind detection in 3-card analysis."""

    @pytest.mark.parametrize("hand", THREE_CARD_TRIPS_SAMPLES)
    def test_trips_detected(self, hand: list[Card]) -> None:
        """Three of a kind should be detected."""
        analysis = analyze_three_cards(hand)
        assert analysis.has_trips is True
        assert analysis.has_paying_hand is True
        assert analysis.has_pair is False  # Trips is not a pair
        # In Let It Ride, only hand type matters - pair_rank not set for trips
        assert analysis.pair_rank is None

    def test_trip_aces(self) -> None:
        """Trip aces should be detected with correct high card count."""
        analysis = analyze_three_cards(make_hand("Ah As Ad"))
        assert analysis.has_trips is True
        assert analysis.high_cards == 3
        assert analysis.pair_rank is None  # Not set for trips


class TestThreeCardPairs:
    """Tests for pair detection in 3-card analysis."""

    @pytest.mark.parametrize("hand", THREE_CARD_HIGH_PAIR_SAMPLES)
    def test_high_pair_detected(self, hand: list[Card]) -> None:
        """High pair (10s or better) should be detected as paying."""
        analysis = analyze_three_cards(hand)
        assert analysis.has_pair is True
        assert analysis.has_high_pair is True
        assert analysis.has_paying_hand is True
        assert analysis.pair_rank is not None
        assert analysis.pair_rank.value >= 10

    @pytest.mark.parametrize("hand", THREE_CARD_LOW_PAIR_SAMPLES)
    def test_low_pair_detected(self, hand: list[Card]) -> None:
        """Low pair (below 10s) should not be a paying hand."""
        analysis = analyze_three_cards(hand)
        assert analysis.has_pair is True
        assert analysis.has_high_pair is False
        assert analysis.has_paying_hand is False
        assert analysis.pair_rank is not None
        assert analysis.pair_rank.value < 10

    def test_pair_of_tens_is_high(self) -> None:
        """Pair of 10s should be a high pair (minimum paying)."""
        analysis = analyze_three_cards(make_hand("Th Ts 2d"))
        assert analysis.has_high_pair is True
        assert analysis.pair_rank == Rank.TEN

    def test_pair_of_nines_is_low(self) -> None:
        """Pair of 9s should be a low pair (non-paying)."""
        analysis = analyze_three_cards(make_hand("9h 9s Ad"))
        assert analysis.has_high_pair is False
        assert analysis.pair_rank == Rank.NINE


class TestThreeCardFlushDraws:
    """Tests for flush draw detection in 3-card analysis."""

    @pytest.mark.parametrize("hand", THREE_CARD_FLUSH_DRAW_SAMPLES)
    def test_flush_draw_detected(self, hand: list[Card]) -> None:
        """3 suited cards should be a flush draw."""
        analysis = analyze_three_cards(hand)
        assert analysis.is_flush_draw is True
        assert analysis.suited_cards == 3

    def test_two_suited_not_flush_draw(self) -> None:
        """2 suited cards should not be a flush draw."""
        analysis = analyze_three_cards(make_hand("Ah Kh 9s"))
        assert analysis.is_flush_draw is False
        assert analysis.suited_cards == 2


class TestThreeCardRoyalDraws:
    """Tests for royal flush draw detection in 3-card analysis."""

    @pytest.mark.parametrize("hand", THREE_CARD_ROYAL_DRAW_SAMPLES)
    def test_royal_draw_detected(self, hand: list[Card]) -> None:
        """3 suited high cards with Ace should be a royal draw."""
        analysis = analyze_three_cards(hand)
        assert analysis.is_royal_draw is True
        assert analysis.is_flush_draw is True

    def test_suited_high_no_ace_not_royal_draw(self) -> None:
        """3 suited high cards without Ace should not be royal draw."""
        # KQJ suited - high cards but no Ace
        analysis = analyze_three_cards(make_hand("Kh Qh Jh"))
        assert analysis.is_royal_draw is False
        assert analysis.is_flush_draw is True
        assert analysis.suited_high_cards == 3

    def test_two_suited_royals_not_royal_draw(self) -> None:
        """Only 2 suited high cards should not be royal draw."""
        analysis = analyze_three_cards(make_hand("Ah Kh 2s"))
        assert analysis.is_royal_draw is False
        assert analysis.suited_high_cards == 2


class TestThreeCardStraightFlushDraws:
    """Tests for straight flush draw detection in 3-card analysis."""

    @pytest.mark.parametrize("hand", THREE_CARD_STRAIGHT_FLUSH_DRAW_SAMPLES)
    def test_straight_flush_draw_detected(self, hand: list[Card]) -> None:
        """3 consecutive suited cards should be straight flush draw."""
        analysis = analyze_three_cards(hand)
        assert analysis.is_straight_flush_draw is True
        assert analysis.is_flush_draw is True

    def test_flush_draw_non_connected_not_sf_draw(self) -> None:
        """3 suited cards with large gap should not be SF draw."""
        # Ah 9h 2h has too large a gap (span > 4) for a straight flush draw
        analysis = analyze_three_cards(make_hand("Ah 9h 2h"))
        assert analysis.is_flush_draw is True
        assert analysis.is_straight_flush_draw is False

    def test_wheel_flush_draw_is_sf_draw(self) -> None:
        """A-5-2 suited is a SF draw (wheel potential)."""
        # A-5-2 fits within the A-2-3-4-5 wheel window
        analysis = analyze_three_cards(make_hand("Ah 5h 2h"))
        assert analysis.is_flush_draw is True
        assert analysis.is_straight_flush_draw is True


class TestThreeCardStraightDraws:
    """Tests for straight draw detection in 3-card analysis."""

    @pytest.mark.parametrize("hand", THREE_CARD_STRAIGHT_DRAW_SAMPLES)
    def test_straight_draw_detected(self, hand: list[Card]) -> None:
        """3 consecutive cards should be straight draw."""
        analysis = analyze_three_cards(hand)
        assert analysis.is_straight_draw is True
        assert analysis.connected_cards >= 3

    def test_wheel_straight_draw(self) -> None:
        """A-2-3 should be detected as straight draw."""
        analysis = analyze_three_cards(make_hand("Ah 2s 3d"))
        assert analysis.is_straight_draw is True

    def test_broadway_straight_draw(self) -> None:
        """Q-K-A should be detected as straight draw."""
        analysis = analyze_three_cards(make_hand("Qh Ks Ad"))
        assert analysis.is_straight_draw is True


class TestThreeCardNoDraws:
    """Tests for hands with no draws in 3-card analysis."""

    @pytest.mark.parametrize("hand", THREE_CARD_NO_DRAW_SAMPLES)
    def test_no_draws(self, hand: list[Card]) -> None:
        """Disconnected hands should have no draws."""
        analysis = analyze_three_cards(hand)
        assert analysis.is_flush_draw is False
        assert analysis.suited_cards < 3


class TestThreeCardHighCardCounting:
    """Tests for high card counting in 3-card analysis."""

    @pytest.mark.parametrize("hand", THREE_CARD_ALL_HIGH_SAMPLES)
    def test_all_high_cards(self, hand: list[Card]) -> None:
        """All high cards should count correctly."""
        analysis = analyze_three_cards(hand)
        assert analysis.high_cards == 3

    @pytest.mark.parametrize("hand", THREE_CARD_NO_HIGH_SAMPLES)
    def test_no_high_cards(self, hand: list[Card]) -> None:
        """Hands with no high cards should count as 0."""
        analysis = analyze_three_cards(hand)
        assert analysis.high_cards == 0

    @pytest.mark.parametrize(
        "hand,expected",
        [
            (make_hand("2h 5s Td"), 1),  # One high card (10)
            (make_hand("3h Ks Ad"), 2),  # Two high cards (K, A)
        ],
    )
    def test_mixed_high_cards(self, hand: list[Card], expected: int) -> None:
        """Mixed hands should count high cards correctly."""
        analysis = analyze_three_cards(hand)
        assert analysis.high_cards == expected


class TestFourCardTrips:
    """Tests for three of a kind detection in 4-card analysis."""

    @pytest.mark.parametrize("hand", FOUR_CARD_TRIPS_SAMPLES)
    def test_trips_detected(self, hand: list[Card]) -> None:
        """Three of a kind should be detected."""
        analysis = analyze_four_cards(hand)
        assert analysis.has_trips is True
        assert analysis.has_paying_hand is True
        assert analysis.has_pair is False  # Trips is not a pair
        # In Let It Ride, only hand type matters - pair_rank not set for trips
        assert analysis.pair_rank is None


class TestFourCardPairs:
    """Tests for pair detection in 4-card analysis."""

    @pytest.mark.parametrize("hand", FOUR_CARD_HIGH_PAIR_SAMPLES)
    def test_high_pair_detected(self, hand: list[Card]) -> None:
        """High pair should be detected as paying."""
        analysis = analyze_four_cards(hand)
        assert analysis.has_pair is True
        assert analysis.has_high_pair is True
        assert analysis.has_paying_hand is True

    @pytest.mark.parametrize("hand", FOUR_CARD_LOW_PAIR_SAMPLES)
    def test_low_pair_detected(self, hand: list[Card]) -> None:
        """Low pair should be detected as non-paying."""
        analysis = analyze_four_cards(hand)
        assert analysis.has_pair is True
        assert analysis.has_high_pair is False
        assert analysis.has_paying_hand is False


class TestFourCardTwoPair:
    """Tests for two pair detection in 4-card analysis."""

    @pytest.mark.parametrize("hand", FOUR_CARD_TWO_PAIR_SAMPLES)
    def test_two_pair_detected(self, hand: list[Card]) -> None:
        """Two pair should be detected as paying hand."""
        analysis = analyze_four_cards(hand)
        # Two pair is NOT has_pair (has_pair is for single pair only)
        assert analysis.has_pair is False
        assert analysis.has_paying_hand is True
        # In Let It Ride, only hand type matters - pair_rank not set for two pair
        assert analysis.pair_rank is None


class TestFourCardFlushDraws:
    """Tests for flush draw detection in 4-card analysis."""

    @pytest.mark.parametrize("hand", FOUR_CARD_FLUSH_DRAW_SAMPLES)
    def test_flush_draw_detected(self, hand: list[Card]) -> None:
        """4 suited cards should be a flush draw."""
        analysis = analyze_four_cards(hand)
        assert analysis.is_flush_draw is True
        assert analysis.suited_cards >= 4

    def test_three_suited_not_flush_draw_in_four_cards(self) -> None:
        """3 suited cards in 4-card hand should not be flush draw."""
        analysis = analyze_four_cards(make_hand("Ah Kh Qh 2s"))
        assert analysis.is_flush_draw is False
        assert analysis.suited_cards == 3


class TestFourCardRoyalDraws:
    """Tests for royal flush draw detection in 4-card analysis."""

    @pytest.mark.parametrize("hand", FOUR_CARD_ROYAL_DRAW_SAMPLES)
    def test_royal_draw_detected(self, hand: list[Card]) -> None:
        """4 suited high cards with Ace should be a royal draw."""
        analysis = analyze_four_cards(hand)
        assert analysis.is_royal_draw is True
        assert analysis.is_flush_draw is True
        assert analysis.suited_high_cards >= 4


class TestFourCardOpenEndedStraightDraws:
    """Tests for open-ended straight draw detection in 4-card analysis."""

    @pytest.mark.parametrize("hand", FOUR_CARD_OPEN_STRAIGHT_SAMPLES)
    def test_open_ended_detected(self, hand: list[Card]) -> None:
        """4 consecutive cards should be open-ended straight draw."""
        analysis = analyze_four_cards(hand)
        assert analysis.is_straight_draw is True
        assert analysis.is_open_straight_draw is True
        assert analysis.is_inside_straight_draw is False
        assert analysis.connected_cards >= 4


class TestFourCardInsideStraightDraws:
    """Tests for inside (gutshot) straight draw detection in 4-card analysis."""

    @pytest.mark.parametrize("hand", FOUR_CARD_INSIDE_STRAIGHT_SAMPLES)
    def test_inside_draw_detected(self, hand: list[Card]) -> None:
        """4 cards with gap should be inside straight draw."""
        analysis = analyze_four_cards(hand)
        assert analysis.is_straight_draw is True
        assert analysis.is_inside_straight_draw is True
        assert analysis.is_open_straight_draw is False


class TestFourCardStraightFlushDraws:
    """Tests for straight flush draw detection in 4-card analysis."""

    def test_four_suited_consecutive_is_sf_draw(self) -> None:
        """4 consecutive suited cards should be straight flush draw."""
        analysis = analyze_four_cards(make_hand("8h 9h Th Jh"))
        assert analysis.is_straight_flush_draw is True
        assert analysis.is_flush_draw is True


class TestFourCardWheelDraws:
    """Tests for wheel (A-2-3-4-5) straight draws in 4-card analysis."""

    def test_a234_is_inside_draw(self) -> None:
        """A-2-3-4 should be inside draw (needs 5 only)."""
        analysis = analyze_four_cards(make_hand("Ah 2s 3d 4c"))
        assert analysis.is_straight_draw is True
        # A-2-3-4 needs only 5, so it's inside (gutshot)
        assert analysis.is_inside_straight_draw is True

    def test_2345_is_open_ended(self) -> None:
        """2-3-4-5 should be open-ended (needs A or 6)."""
        analysis = analyze_four_cards(make_hand("2h 3s 4d 5c"))
        assert analysis.is_straight_draw is True
        assert analysis.is_open_straight_draw is True


class TestFourCardBroadwayDraws:
    """Tests for broadway straight draws in 4-card analysis."""

    def test_tjqk_is_open_ended(self) -> None:
        """T-J-Q-K should be open-ended (needs 9 or A)."""
        analysis = analyze_four_cards(make_hand("Th Js Qd Kc"))
        assert analysis.is_straight_draw is True
        assert analysis.is_open_straight_draw is True

    def test_jqka_is_inside(self) -> None:
        """J-Q-K-A should be inside draw (needs T only)."""
        analysis = analyze_four_cards(make_hand("Jh Qs Kd Ac"))
        assert analysis.is_straight_draw is True
        # Can only complete with T, so it's inside
        assert analysis.is_inside_straight_draw is True


class TestFourCardNoDraws:
    """Tests for hands with no draws in 4-card analysis."""

    @pytest.mark.parametrize("hand", FOUR_CARD_NO_DRAW_SAMPLES)
    def test_no_draws(self, hand: list[Card]) -> None:
        """Disconnected hands should have no draws."""
        analysis = analyze_four_cards(hand)
        assert analysis.is_flush_draw is False
        assert analysis.suited_cards < 4


class TestSuitedHighCardCounting:
    """Tests for suited high card counting."""

    def test_all_suited_high_cards(self) -> None:
        """All suited high cards should be counted correctly."""
        analysis = analyze_three_cards(make_hand("Ah Kh Qh"))
        assert analysis.suited_high_cards == 3
        assert analysis.high_cards == 3

    def test_mixed_suited_high_cards(self) -> None:
        """Only suited high cards should be counted."""
        analysis = analyze_three_cards(make_hand("Ah Kh 2h"))
        assert analysis.suited_high_cards == 2
        assert analysis.high_cards == 2

    def test_no_suited_high_cards(self) -> None:
        """Low suited cards should count as 0 suited high cards."""
        analysis = analyze_three_cards(make_hand("2h 5h 8h"))
        assert analysis.suited_high_cards == 0
        assert analysis.high_cards == 0
        assert analysis.is_flush_draw is True


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_all_same_rank_three_cards(self) -> None:
        """Three cards of same rank should be trips."""
        analysis = analyze_three_cards(make_hand("Ah As Ad"))
        assert analysis.has_trips is True
        assert analysis.has_pair is False

    def test_all_same_rank_four_cards(self) -> None:
        """Four cards with trips should show trips."""
        analysis = analyze_four_cards(make_hand("Ah As Ad Kc"))
        assert analysis.has_trips is True

    def test_gap_analysis_three_cards(self) -> None:
        """Gap analysis should work for 3 cards."""
        # 3 consecutive cards within a 5-card window
        # gaps = 5 - connected_cards = 5 - 3 = 2 (spaces needed to complete straight)
        analysis = analyze_three_cards(make_hand("5h 6s 7d"))
        assert analysis.connected_cards == 3
        assert analysis.gaps == 2  # 2 cards needed to complete the straight

    def test_gap_analysis_four_cards(self) -> None:
        """Gap analysis should work for 4 cards."""
        # One gap
        analysis = analyze_four_cards(make_hand("5h 6s 8d 9c"))
        assert analysis.gaps == 1

    def test_disconnected_cards_high_gaps(self) -> None:
        """Very disconnected cards should have high gaps."""
        analysis = analyze_three_cards(make_hand("2h 7s Qd"))
        # No straight potential
        assert analysis.is_straight_draw is False
