"""Unit tests for session result data structures."""

from dataclasses import FrozenInstanceError

import pytest

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.game_engine import GameHandResult
from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.three_card_evaluator import ThreeCardHandRank
from let_it_ride.simulation.results import (
    HandRecord,
    count_hand_distribution,
    count_hand_distribution_from_ranks,
    get_decision_from_string,
)
from let_it_ride.strategy.base import Decision

# --- Test Fixtures ---


def create_sample_hand_record(
    hand_id: int = 0,
    session_id: int = 1,
    shoe_id: int | None = None,
    cards_player: str = "Ah Kd Qs",
    cards_community: str = "Jc Th",
    decision_bet1: str = "ride",
    decision_bet2: str = "pull",
    final_hand_rank: str = "straight",
    base_bet: float = 25.0,
    bets_at_risk: float = 50.0,
    main_payout: float = 100.0,
    bonus_bet: float = 5.0,
    bonus_hand_rank: str | None = "high_card",
    bonus_payout: float = 0.0,
    bankroll_after: float = 1075.0,
) -> HandRecord:
    """Create a sample HandRecord for testing."""
    return HandRecord(
        hand_id=hand_id,
        session_id=session_id,
        shoe_id=shoe_id,
        cards_player=cards_player,
        cards_community=cards_community,
        decision_bet1=decision_bet1,
        decision_bet2=decision_bet2,
        final_hand_rank=final_hand_rank,
        base_bet=base_bet,
        bets_at_risk=bets_at_risk,
        main_payout=main_payout,
        bonus_bet=bonus_bet,
        bonus_hand_rank=bonus_hand_rank,
        bonus_payout=bonus_payout,
        bankroll_after=bankroll_after,
    )


def create_sample_game_hand_result(
    hand_id: int = 0,
    final_hand_rank: FiveCardHandRank = FiveCardHandRank.STRAIGHT,
    bonus_hand_rank: ThreeCardHandRank | None = ThreeCardHandRank.HIGH_CARD,
) -> GameHandResult:
    """Create a sample GameHandResult for testing."""
    player_cards = (
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.DIAMONDS),
        Card(Rank.QUEEN, Suit.SPADES),
    )
    community_cards = (
        Card(Rank.JACK, Suit.CLUBS),
        Card(Rank.TEN, Suit.HEARTS),
    )
    return GameHandResult(
        hand_id=hand_id,
        player_cards=player_cards,
        community_cards=community_cards,
        decision_bet1=Decision.RIDE,
        decision_bet2=Decision.PULL,
        final_hand_rank=final_hand_rank,
        base_bet=25.0,
        bets_at_risk=50.0,
        main_payout=100.0,
        bonus_bet=5.0,
        bonus_hand_rank=bonus_hand_rank,
        bonus_payout=0.0,
        net_result=45.0,
    )


# --- HandRecord Initialization Tests ---


class TestHandRecordInitialization:
    """Tests for HandRecord initialization."""

    def test_create_minimal_record(self) -> None:
        """Verify HandRecord can be created with all required fields."""
        record = create_sample_hand_record()
        assert record.hand_id == 0
        assert record.session_id == 1
        assert record.shoe_id is None
        assert record.cards_player == "Ah Kd Qs"
        assert record.cards_community == "Jc Th"
        assert record.decision_bet1 == "ride"
        assert record.decision_bet2 == "pull"
        assert record.final_hand_rank == "straight"
        assert record.base_bet == 25.0
        assert record.bets_at_risk == 50.0
        assert record.main_payout == 100.0
        assert record.bonus_bet == 5.0
        assert record.bonus_hand_rank == "high_card"
        assert record.bonus_payout == 0.0
        assert record.bankroll_after == 1075.0

    def test_create_record_with_shoe_id(self) -> None:
        """Verify HandRecord can be created with shoe_id."""
        record = create_sample_hand_record(shoe_id=42)
        assert record.shoe_id == 42

    def test_create_record_without_bonus(self) -> None:
        """Verify HandRecord can be created without bonus bet."""
        record = create_sample_hand_record(
            bonus_bet=0.0,
            bonus_hand_rank=None,
            bonus_payout=0.0,
        )
        assert record.bonus_bet == 0.0
        assert record.bonus_hand_rank is None
        assert record.bonus_payout == 0.0

    def test_record_is_frozen(self) -> None:
        """Verify HandRecord is immutable."""
        record = create_sample_hand_record()
        with pytest.raises(FrozenInstanceError):
            record.hand_id = 999  # type: ignore[misc]

    def test_record_is_hashable(self) -> None:
        """Verify HandRecord is hashable."""
        record = create_sample_hand_record()
        hash_value = hash(record)
        assert isinstance(hash_value, int)

    def test_record_equality(self) -> None:
        """Verify HandRecord equality comparison."""
        record1 = create_sample_hand_record()
        record2 = create_sample_hand_record()
        record3 = create_sample_hand_record(hand_id=999)

        assert record1 == record2
        assert record1 != record3


# --- HandRecord Serialization Tests ---


class TestHandRecordToDict:
    """Tests for HandRecord.to_dict() method."""

    def test_to_dict_all_fields(self) -> None:
        """Verify to_dict includes all fields."""
        record = create_sample_hand_record()
        data = record.to_dict()

        assert data["hand_id"] == 0
        assert data["session_id"] == 1
        assert data["shoe_id"] is None
        assert data["cards_player"] == "Ah Kd Qs"
        assert data["cards_community"] == "Jc Th"
        assert data["decision_bet1"] == "ride"
        assert data["decision_bet2"] == "pull"
        assert data["final_hand_rank"] == "straight"
        assert data["base_bet"] == 25.0
        assert data["bets_at_risk"] == 50.0
        assert data["main_payout"] == 100.0
        assert data["bonus_bet"] == 5.0
        assert data["bonus_hand_rank"] == "high_card"
        assert data["bonus_payout"] == 0.0
        assert data["bankroll_after"] == 1075.0

    def test_to_dict_with_shoe_id(self) -> None:
        """Verify to_dict correctly serializes shoe_id."""
        record = create_sample_hand_record(shoe_id=42)
        data = record.to_dict()
        assert data["shoe_id"] == 42

    def test_to_dict_field_count(self) -> None:
        """Verify to_dict returns correct number of fields."""
        record = create_sample_hand_record()
        data = record.to_dict()
        assert len(data) == 15  # All fields


class TestHandRecordFromDict:
    """Tests for HandRecord.from_dict() method."""

    def test_from_dict_round_trip(self) -> None:
        """Verify from_dict creates equivalent record after to_dict."""
        original = create_sample_hand_record()
        data = original.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored == original

    def test_from_dict_with_shoe_id(self) -> None:
        """Verify from_dict correctly handles shoe_id."""
        original = create_sample_hand_record(shoe_id=42)
        data = original.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored.shoe_id == 42

    def test_from_dict_with_null_shoe_id(self) -> None:
        """Verify from_dict handles null shoe_id."""
        original = create_sample_hand_record(shoe_id=None)
        data = original.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored.shoe_id is None

    def test_from_dict_with_null_bonus_hand_rank(self) -> None:
        """Verify from_dict handles null bonus_hand_rank."""
        original = create_sample_hand_record(bonus_hand_rank=None)
        data = original.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored.bonus_hand_rank is None

    def test_from_dict_type_coercion(self) -> None:
        """Verify from_dict coerces types correctly."""
        data = {
            "hand_id": "0",  # String instead of int
            "session_id": "1",
            "shoe_id": None,
            "cards_player": "Ah Kd Qs",
            "cards_community": "Jc Th",
            "decision_bet1": "ride",
            "decision_bet2": "pull",
            "final_hand_rank": "straight",
            "base_bet": "25.0",  # String instead of float
            "bets_at_risk": "50.0",
            "main_payout": "100.0",
            "bonus_bet": "5.0",
            "bonus_hand_rank": "high_card",
            "bonus_payout": "0.0",
            "bankroll_after": "1075.0",
        }
        record = HandRecord.from_dict(data)
        assert record.hand_id == 0
        assert record.base_bet == 25.0
        assert isinstance(record.hand_id, int)
        assert isinstance(record.base_bet, float)

    def test_from_dict_missing_field_raises(self) -> None:
        """Verify from_dict raises KeyError for missing fields."""
        data = {"hand_id": 0}  # Missing most fields
        with pytest.raises(KeyError):
            HandRecord.from_dict(data)

    def test_from_dict_invalid_int_value_raises(self) -> None:
        """Verify from_dict raises ValueError for non-convertible int values."""
        data = create_sample_hand_record().to_dict()
        data["hand_id"] = "not_an_int"
        with pytest.raises(ValueError):
            HandRecord.from_dict(data)

    def test_from_dict_invalid_float_value_raises(self) -> None:
        """Verify from_dict raises ValueError for non-convertible float values."""
        data = create_sample_hand_record().to_dict()
        data["base_bet"] = "not_a_float"
        with pytest.raises(ValueError):
            HandRecord.from_dict(data)


# --- HandRecord.from_game_result Tests ---


class TestHandRecordFromGameResult:
    """Tests for HandRecord.from_game_result() method."""

    def test_from_game_result_basic(self) -> None:
        """Verify from_game_result creates correct HandRecord."""
        game_result = create_sample_game_hand_result()
        record = HandRecord.from_game_result(
            result=game_result,
            session_id=1,
            bankroll_after=1075.0,
        )

        assert record.hand_id == 0
        assert record.session_id == 1
        assert record.shoe_id is None
        assert record.cards_player == "Ah Kd Qs"
        assert record.cards_community == "Jc Th"
        assert record.decision_bet1 == "ride"
        assert record.decision_bet2 == "pull"
        assert record.final_hand_rank == "straight"
        assert record.base_bet == 25.0
        assert record.bets_at_risk == 50.0
        assert record.main_payout == 100.0
        assert record.bonus_bet == 5.0
        assert record.bonus_hand_rank == "high_card"
        assert record.bonus_payout == 0.0
        assert record.bankroll_after == 1075.0

    def test_from_game_result_with_shoe_id(self) -> None:
        """Verify from_game_result handles shoe_id."""
        game_result = create_sample_game_hand_result()
        record = HandRecord.from_game_result(
            result=game_result,
            session_id=1,
            bankroll_after=1075.0,
            shoe_id=42,
        )
        assert record.shoe_id == 42

    def test_from_game_result_no_bonus(self) -> None:
        """Verify from_game_result handles no bonus bet."""
        game_result = create_sample_game_hand_result(bonus_hand_rank=None)
        record = HandRecord.from_game_result(
            result=game_result,
            session_id=1,
            bankroll_after=1075.0,
        )
        assert record.bonus_hand_rank is None

    def test_from_game_result_card_format(self) -> None:
        """Verify from_game_result formats cards correctly."""
        game_result = create_sample_game_hand_result()
        record = HandRecord.from_game_result(
            result=game_result,
            session_id=1,
            bankroll_after=1000.0,
        )
        # Cards should be space-separated, format: RankSuit
        parts = record.cards_player.split()
        assert len(parts) == 3
        # Each card should be 2-3 characters (rank + suit)
        for part in parts:
            assert len(part) in (2, 3)  # "Ah" or "10h"

    def test_from_game_result_decision_format(self) -> None:
        """Verify from_game_result formats decisions correctly."""
        game_result = create_sample_game_hand_result()
        record = HandRecord.from_game_result(
            result=game_result,
            session_id=1,
            bankroll_after=1000.0,
        )
        # Decisions should be lowercase
        assert record.decision_bet1 in ("ride", "pull")
        assert record.decision_bet2 in ("ride", "pull")

    def test_from_game_result_hand_rank_format(self) -> None:
        """Verify from_game_result formats hand ranks correctly."""
        game_result = create_sample_game_hand_result(
            final_hand_rank=FiveCardHandRank.ROYAL_FLUSH
        )
        record = HandRecord.from_game_result(
            result=game_result,
            session_id=1,
            bankroll_after=1000.0,
        )
        # Hand rank should be lowercase enum name
        assert record.final_hand_rank == "royal_flush"

    def test_from_game_result_all_hand_ranks(self) -> None:
        """Verify from_game_result handles all hand rank types."""
        for rank in FiveCardHandRank:
            game_result = create_sample_game_hand_result(final_hand_rank=rank)
            record = HandRecord.from_game_result(
                result=game_result,
                session_id=1,
                bankroll_after=1000.0,
            )
            assert record.final_hand_rank == rank.name.lower()

    def test_from_game_result_all_decision_combinations(self) -> None:
        """Verify from_game_result handles all decision combinations."""
        decision_combinations = [
            (Decision.RIDE, Decision.RIDE),
            (Decision.RIDE, Decision.PULL),
            (Decision.PULL, Decision.RIDE),
            (Decision.PULL, Decision.PULL),
        ]
        for decision1, decision2 in decision_combinations:
            # Create GameHandResult with specific decisions
            player_cards = (
                Card(Rank.ACE, Suit.HEARTS),
                Card(Rank.KING, Suit.DIAMONDS),
                Card(Rank.QUEEN, Suit.SPADES),
            )
            community_cards = (
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.TEN, Suit.HEARTS),
            )
            game_result = GameHandResult(
                hand_id=0,
                player_cards=player_cards,
                community_cards=community_cards,
                decision_bet1=decision1,
                decision_bet2=decision2,
                final_hand_rank=FiveCardHandRank.STRAIGHT,
                base_bet=25.0,
                bets_at_risk=50.0,
                main_payout=100.0,
                bonus_bet=0.0,
                bonus_hand_rank=None,
                bonus_payout=0.0,
                net_result=50.0,
            )
            record = HandRecord.from_game_result(
                result=game_result,
                session_id=1,
                bankroll_after=1000.0,
            )
            assert record.decision_bet1 == decision1.value
            assert record.decision_bet2 == decision2.value


# --- count_hand_distribution Tests ---


class TestCountHandDistribution:
    """Tests for count_hand_distribution helper function."""

    def test_empty_input(self) -> None:
        """Verify empty input returns empty distribution."""
        result = count_hand_distribution([])
        assert result == {}

    def test_single_hand_record(self) -> None:
        """Verify single HandRecord is counted correctly."""
        record = create_sample_hand_record(final_hand_rank="flush")
        result = count_hand_distribution([record])
        assert result == {"flush": 1}

    def test_single_game_result(self) -> None:
        """Verify single GameHandResult is counted correctly."""
        game_result = create_sample_game_hand_result(
            final_hand_rank=FiveCardHandRank.FLUSH
        )
        result = count_hand_distribution([game_result])
        assert result == {"flush": 1}

    def test_multiple_same_hand(self) -> None:
        """Verify multiple same hands are counted correctly."""
        records = [
            create_sample_hand_record(hand_id=i, final_hand_rank="pair_tens_or_better")
            for i in range(5)
        ]
        result = count_hand_distribution(records)
        assert result == {"pair_tens_or_better": 5}

    def test_multiple_different_hands(self) -> None:
        """Verify multiple different hands are counted correctly."""
        records = [
            create_sample_hand_record(hand_id=0, final_hand_rank="high_card"),
            create_sample_hand_record(hand_id=1, final_hand_rank="pair_tens_or_better"),
            create_sample_hand_record(hand_id=2, final_hand_rank="flush"),
            create_sample_hand_record(hand_id=3, final_hand_rank="pair_tens_or_better"),
            create_sample_hand_record(hand_id=4, final_hand_rank="high_card"),
            create_sample_hand_record(hand_id=5, final_hand_rank="high_card"),
        ]
        result = count_hand_distribution(records)
        assert result == {
            "high_card": 3,
            "pair_tens_or_better": 2,
            "flush": 1,
        }

    def test_mixed_record_types(self) -> None:
        """Verify distribution handles mixed HandRecord and GameHandResult."""
        records: list[HandRecord | GameHandResult] = [
            create_sample_hand_record(hand_id=0, final_hand_rank="flush"),
            create_sample_game_hand_result(
                hand_id=1, final_hand_rank=FiveCardHandRank.FLUSH
            ),
            create_sample_hand_record(hand_id=2, final_hand_rank="straight"),
        ]
        result = count_hand_distribution(records)
        assert result == {"flush": 2, "straight": 1}

    def test_all_hand_ranks_counted(self) -> None:
        """Verify all hand rank types can be counted."""
        records = [
            create_sample_hand_record(hand_id=i, final_hand_rank=rank.name.lower())
            for i, rank in enumerate(FiveCardHandRank)
        ]
        result = count_hand_distribution(records)
        assert len(result) == len(FiveCardHandRank)
        for rank in FiveCardHandRank:
            assert result[rank.name.lower()] == 1

    def test_distribution_counts_unknown_rank_strings(self) -> None:
        """Verify distribution counts arbitrary rank strings without validation.

        This documents that count_hand_distribution does not validate rank names,
        which is intentional for flexibility but means invalid data could propagate.
        """
        record = create_sample_hand_record(final_hand_rank="invalid_rank")
        result = count_hand_distribution([record])
        assert result == {"invalid_rank": 1}


class TestCountHandDistributionFromRanks:
    """Tests for count_hand_distribution_from_ranks helper function."""

    def test_empty_input(self) -> None:
        """Verify empty input returns empty distribution."""
        result = count_hand_distribution_from_ranks([])
        assert result == {}

    def test_single_rank(self) -> None:
        """Verify single rank is counted correctly."""
        result = count_hand_distribution_from_ranks([FiveCardHandRank.FLUSH])
        assert result == {"flush": 1}

    def test_multiple_same_rank(self) -> None:
        """Verify multiple same ranks are counted correctly."""
        ranks = [FiveCardHandRank.PAIR_TENS_OR_BETTER] * 5
        result = count_hand_distribution_from_ranks(ranks)
        assert result == {"pair_tens_or_better": 5}

    def test_multiple_different_ranks(self) -> None:
        """Verify multiple different ranks are counted correctly."""
        ranks = [
            FiveCardHandRank.HIGH_CARD,
            FiveCardHandRank.PAIR_TENS_OR_BETTER,
            FiveCardHandRank.FLUSH,
            FiveCardHandRank.PAIR_TENS_OR_BETTER,
            FiveCardHandRank.HIGH_CARD,
            FiveCardHandRank.HIGH_CARD,
        ]
        result = count_hand_distribution_from_ranks(ranks)
        assert result == {
            "high_card": 3,
            "pair_tens_or_better": 2,
            "flush": 1,
        }


# --- get_decision_from_string Tests ---


class TestGetDecisionFromString:
    """Tests for get_decision_from_string helper function."""

    def test_ride_lowercase(self) -> None:
        """Verify 'ride' returns RIDE decision."""
        result = get_decision_from_string("ride")
        assert result == Decision.RIDE

    def test_pull_lowercase(self) -> None:
        """Verify 'pull' returns PULL decision."""
        result = get_decision_from_string("pull")
        assert result == Decision.PULL

    def test_ride_uppercase(self) -> None:
        """Verify 'RIDE' returns RIDE decision (case insensitive)."""
        result = get_decision_from_string("RIDE")
        assert result == Decision.RIDE

    def test_pull_uppercase(self) -> None:
        """Verify 'PULL' returns PULL decision (case insensitive)."""
        result = get_decision_from_string("PULL")
        assert result == Decision.PULL

    def test_ride_mixed_case(self) -> None:
        """Verify 'Ride' returns RIDE decision."""
        result = get_decision_from_string("Ride")
        assert result == Decision.RIDE

    def test_invalid_decision_raises(self) -> None:
        """Verify invalid decision string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_decision_from_string("invalid")
        assert "Invalid decision string" in str(exc_info.value)

    def test_empty_string_raises(self) -> None:
        """Verify empty string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_decision_from_string("")
        assert "Invalid decision string" in str(exc_info.value)

    def test_whitespace_raises(self) -> None:
        """Verify leading/trailing whitespace causes ValueError."""
        with pytest.raises(ValueError):
            get_decision_from_string(" ride ")

    def test_whitespace_only_raises(self) -> None:
        """Verify whitespace-only string raises ValueError."""
        with pytest.raises(ValueError):
            get_decision_from_string("   ")


# --- Serialization Round-Trip Tests ---


class TestSerializationRoundTrip:
    """Tests for complete serialization round-trips."""

    def test_hand_record_round_trip(self) -> None:
        """Verify HandRecord survives JSON-like round-trip."""
        original = create_sample_hand_record()

        # Simulate JSON round-trip
        data = original.to_dict()
        # In real JSON, all values become strings or primitives
        import json

        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        restored = HandRecord.from_dict(parsed)

        assert restored == original

    def test_game_result_to_hand_record_preserves_data(self) -> None:
        """Verify GameHandResult to HandRecord preserves essential data."""
        game_result = create_sample_game_hand_result()

        record = HandRecord.from_game_result(
            result=game_result,
            session_id=1,
            bankroll_after=1000.0,
        )

        # Verify core data is preserved
        assert record.hand_id == game_result.hand_id
        assert record.decision_bet1 == game_result.decision_bet1.value
        assert record.decision_bet2 == game_result.decision_bet2.value
        assert record.final_hand_rank == game_result.final_hand_rank.name.lower()
        assert record.base_bet == game_result.base_bet
        assert record.bets_at_risk == game_result.bets_at_risk
        assert record.main_payout == game_result.main_payout
        assert record.bonus_bet == game_result.bonus_bet
        assert record.bonus_payout == game_result.bonus_payout

    def test_round_trip_with_various_hand_ranks(self) -> None:
        """Verify round-trip works for all hand ranks."""
        for rank in FiveCardHandRank:
            game_result = create_sample_game_hand_result(final_hand_rank=rank)
            record = HandRecord.from_game_result(
                result=game_result,
                session_id=1,
                bankroll_after=1000.0,
            )
            data = record.to_dict()
            restored = HandRecord.from_dict(data)

            assert restored == record
            assert restored.final_hand_rank == rank.name.lower()

    def test_round_trip_with_various_bonus_ranks(self) -> None:
        """Verify round-trip works for all bonus hand ranks."""
        for rank in ThreeCardHandRank:
            game_result = create_sample_game_hand_result(bonus_hand_rank=rank)
            record = HandRecord.from_game_result(
                result=game_result,
                session_id=1,
                bankroll_after=1000.0,
            )
            data = record.to_dict()
            restored = HandRecord.from_dict(data)

            assert restored == record
            assert restored.bonus_hand_rank == rank.name.lower()


# --- Edge Cases ---


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_values(self) -> None:
        """Verify HandRecord handles zero values correctly."""
        record = create_sample_hand_record(
            base_bet=0.0,
            bets_at_risk=0.0,
            main_payout=0.0,
            bonus_bet=0.0,
            bonus_payout=0.0,
            bankroll_after=0.0,
        )
        data = record.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored == record

    def test_negative_values(self) -> None:
        """Verify HandRecord handles negative values (for net losses)."""
        record = create_sample_hand_record(
            main_payout=-75.0,  # Loss
            bankroll_after=925.0,
        )
        data = record.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored == record
        assert restored.main_payout == -75.0

    def test_very_large_values(self) -> None:
        """Verify HandRecord handles very large values."""
        record = create_sample_hand_record(
            hand_id=999999999,
            session_id=999999999,
            base_bet=1000000.0,
            bankroll_after=10000000.0,
        )
        data = record.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored == record

    def test_floating_point_precision(self) -> None:
        """Verify HandRecord maintains floating point precision."""
        record = create_sample_hand_record(
            base_bet=0.01,
            bets_at_risk=0.03,
            main_payout=0.06,
            bankroll_after=100.07,
        )
        data = record.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored.base_bet == pytest.approx(0.01)
        assert restored.bets_at_risk == pytest.approx(0.03)
        assert restored.main_payout == pytest.approx(0.06)
        assert restored.bankroll_after == pytest.approx(100.07)

    def test_empty_card_strings(self) -> None:
        """Verify HandRecord handles unusual card strings."""
        # This shouldn't happen in practice, but test edge case
        record = create_sample_hand_record(
            cards_player="",
            cards_community="",
        )
        data = record.to_dict()
        restored = HandRecord.from_dict(data)
        assert restored == record

    def test_distribution_with_generator(self) -> None:
        """Verify count_hand_distribution works with generators."""

        def record_generator():
            for i in range(5):
                yield create_sample_hand_record(hand_id=i, final_hand_rank="flush")

        result = count_hand_distribution(record_generator())
        assert result == {"flush": 5}
