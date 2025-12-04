"""Unit tests for Table abstraction."""

import random

import pytest

from let_it_ride.config.models import DealerConfig, TableConfig
from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_b,
    standard_main_paytable,
)
from let_it_ride.core.deck import Deck
from let_it_ride.core.game_engine import GameEngine
from let_it_ride.core.table import Table
from let_it_ride.strategy.base import StrategyContext
from let_it_ride.strategy.basic import BasicStrategy


@pytest.fixture
def basic_setup() -> tuple[Deck, BasicStrategy, MainGamePaytable]:
    """Provide basic components for Table tests."""
    deck = Deck()
    strategy = BasicStrategy()
    paytable = standard_main_paytable()
    return deck, strategy, paytable


@pytest.fixture
def setup_with_bonus() -> tuple[Deck, BasicStrategy, MainGamePaytable, BonusPaytable]:
    """Provide components with bonus paytable for Table tests."""
    deck = Deck()
    strategy = BasicStrategy()
    main_paytable = standard_main_paytable()
    bonus_paytable = bonus_paytable_b()
    return deck, strategy, main_paytable, bonus_paytable


class TestTableConfigModel:
    """Tests for TableConfig validation."""

    def test_default_values(self) -> None:
        """Verify TableConfig has correct defaults."""
        config = TableConfig()
        assert config.num_seats == 1
        assert config.track_seat_positions is True

    def test_custom_values(self) -> None:
        """Verify TableConfig accepts custom values."""
        config = TableConfig(num_seats=6, track_seat_positions=False)
        assert config.num_seats == 6
        assert config.track_seat_positions is False

    def test_num_seats_minimum(self) -> None:
        """Verify num_seats must be at least 1."""
        with pytest.raises(ValueError):
            TableConfig(num_seats=0)

    def test_num_seats_maximum(self) -> None:
        """Verify num_seats must be at most 6."""
        with pytest.raises(ValueError):
            TableConfig(num_seats=7)

    def test_num_seats_boundary_values(self) -> None:
        """Verify boundary values are accepted."""
        config_min = TableConfig(num_seats=1)
        assert config_min.num_seats == 1

        config_max = TableConfig(num_seats=6)
        assert config_max.num_seats == 6


class TestPlayerSeatDataclass:
    """Tests for PlayerSeat dataclass."""

    def test_player_seat_is_frozen(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify PlayerSeat is immutable."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        result = table.play_round(round_id=1, base_bet=5.0)
        seat = result.seat_results[0]

        with pytest.raises(AttributeError):
            seat.net_result = 100.0  # type: ignore[misc]


class TestTableRoundResultDataclass:
    """Tests for TableRoundResult dataclass."""

    def test_table_round_result_is_frozen(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify TableRoundResult is immutable."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        result = table.play_round(round_id=1, base_bet=5.0)

        with pytest.raises(AttributeError):
            result.round_id = 999  # type: ignore[misc]


class TestTableSingleSeat:
    """Tests for Table with single seat (backwards compatibility)."""

    def test_single_seat_returns_one_result(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify single-seat table returns exactly one seat result."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        result = table.play_round(round_id=1, base_bet=5.0)

        assert len(result.seat_results) == 1
        assert result.seat_results[0].seat_number == 1

    def test_single_seat_matches_game_engine_with_same_seed(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
    ) -> None:
        """Verify single-seat Table produces same results as GameEngine with same seed."""
        deck1, strategy, paytable = basic_setup
        deck2 = Deck()

        # Create Table and GameEngine with same seed
        table = Table(deck1, strategy, paytable, None, random.Random(12345))
        engine = GameEngine(deck2, strategy, paytable, None, random.Random(12345))

        # Play same round/hand
        table_result = table.play_round(round_id=1, base_bet=5.0)
        engine_result = engine.play_hand(hand_id=1, base_bet=5.0)

        seat = table_result.seat_results[0]

        # Compare all relevant fields
        assert seat.player_cards == engine_result.player_cards
        assert table_result.community_cards == engine_result.community_cards
        assert seat.decision_bet1 == engine_result.decision_bet1
        assert seat.decision_bet2 == engine_result.decision_bet2
        assert seat.final_hand_rank == engine_result.final_hand_rank
        assert seat.base_bet == engine_result.base_bet
        assert seat.bets_at_risk == engine_result.bets_at_risk
        assert seat.main_payout == engine_result.main_payout
        assert seat.net_result == engine_result.net_result

    def test_single_seat_matches_game_engine_with_bonus(
        self,
        setup_with_bonus: tuple[Deck, BasicStrategy, MainGamePaytable, BonusPaytable],
    ) -> None:
        """Verify single-seat Table with bonus matches GameEngine."""
        deck1, strategy, main_paytable, bonus_paytable = setup_with_bonus
        deck2 = Deck()

        table = Table(
            deck1, strategy, main_paytable, bonus_paytable, random.Random(12345)
        )
        engine = GameEngine(
            deck2, strategy, main_paytable, bonus_paytable, random.Random(12345)
        )

        table_result = table.play_round(round_id=1, base_bet=5.0, bonus_bet=1.0)
        engine_result = engine.play_hand(hand_id=1, base_bet=5.0, bonus_bet=1.0)

        seat = table_result.seat_results[0]

        assert seat.bonus_bet == engine_result.bonus_bet
        assert seat.bonus_hand_rank == engine_result.bonus_hand_rank
        assert seat.bonus_payout == engine_result.bonus_payout
        assert seat.net_result == engine_result.net_result


class TestTableMultiSeat:
    """Tests for Table with multiple seats."""

    def test_multi_seat_returns_correct_count(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify multi-seat table returns correct number of seat results."""
        deck, strategy, paytable = basic_setup

        for num_seats in [2, 3, 4, 5, 6]:
            table_config = TableConfig(num_seats=num_seats)
            table = Table(
                deck, strategy, paytable, None, rng, table_config=table_config
            )

            result = table.play_round(round_id=1, base_bet=5.0)

            assert len(result.seat_results) == num_seats
            for i, seat in enumerate(result.seat_results):
                assert seat.seat_number == i + 1

    def test_multi_seat_shared_community_cards(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify all seats share the same community cards."""
        deck, strategy, paytable = basic_setup
        table_config = TableConfig(num_seats=6)
        table = Table(deck, strategy, paytable, None, rng, table_config=table_config)

        result = table.play_round(round_id=1, base_bet=5.0)

        # All seats should share the same community cards
        community = result.community_cards
        assert len(community) == 2

        # The community cards appear in all final hands
        for seat in result.seat_results:
            final_cards = list(seat.player_cards) + list(community)
            assert len(final_cards) == 5

    def test_multi_seat_unique_player_cards(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify each seat gets unique player cards."""
        deck, strategy, paytable = basic_setup
        table_config = TableConfig(num_seats=6)
        table = Table(deck, strategy, paytable, None, rng, table_config=table_config)

        result = table.play_round(round_id=1, base_bet=5.0)

        # Collect all player cards from all seats
        all_player_cards = []
        for seat in result.seat_results:
            all_player_cards.extend(seat.player_cards)

        # All cards should be unique
        assert len(all_player_cards) == 18  # 6 seats * 3 cards
        assert len(set(all_player_cards)) == 18

    def test_all_cards_unique_in_round(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify all cards dealt in a round are unique (no duplicates)."""
        deck, strategy, paytable = basic_setup
        table_config = TableConfig(num_seats=6)
        dealer_config = DealerConfig(discard_enabled=True, discard_cards=3)
        table = Table(
            deck,
            strategy,
            paytable,
            None,
            rng,
            table_config=table_config,
            dealer_config=dealer_config,
        )

        result = table.play_round(round_id=1, base_bet=5.0)

        # Collect all cards
        all_cards = []
        if result.dealer_discards:
            all_cards.extend(result.dealer_discards)
        all_cards.extend(result.community_cards)
        for seat in result.seat_results:
            all_cards.extend(seat.player_cards)

        # Expected: 3 discard + 2 community + 18 player (6*3) = 23 cards
        assert len(all_cards) == 23
        assert len(set(all_cards)) == 23


class TestTableDealerDiscard:
    """Tests for Table with dealer discard mechanics."""

    def test_no_discard_by_default(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify no cards are discarded when dealer_config is not provided."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        result = table.play_round(round_id=1, base_bet=5.0)

        assert result.dealer_discards is None
        assert table.last_discarded_cards() == ()

    def test_discard_enabled(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify cards are discarded when enabled."""
        deck, strategy, paytable = basic_setup
        dealer_config = DealerConfig(discard_enabled=True, discard_cards=3)
        table = Table(deck, strategy, paytable, None, rng, dealer_config=dealer_config)

        result = table.play_round(round_id=1, base_bet=5.0)

        assert result.dealer_discards is not None
        assert len(result.dealer_discards) == 3
        assert table.last_discarded_cards() == result.dealer_discards

    def test_discard_cards_not_dealt_to_players(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify discarded cards are not dealt to players."""
        deck, strategy, paytable = basic_setup
        table_config = TableConfig(num_seats=6)
        dealer_config = DealerConfig(discard_enabled=True, discard_cards=3)
        table = Table(
            deck,
            strategy,
            paytable,
            None,
            rng,
            table_config=table_config,
            dealer_config=dealer_config,
        )

        result = table.play_round(round_id=1, base_bet=5.0)

        # Collect all player and community cards
        player_and_community = list(result.community_cards)
        for seat in result.seat_results:
            player_and_community.extend(seat.player_cards)

        # No discarded card should appear in player/community cards
        assert result.dealer_discards is not None
        for card in result.dealer_discards:
            assert card not in player_and_community


class TestTableValidation:
    """Tests for Table input validation."""

    def test_base_bet_must_be_positive(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify base_bet validation."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        with pytest.raises(ValueError, match="base_bet must be positive"):
            table.play_round(round_id=1, base_bet=0)

        with pytest.raises(ValueError, match="base_bet must be positive"):
            table.play_round(round_id=1, base_bet=-5.0)

    def test_bonus_bet_cannot_be_negative(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify bonus_bet validation."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        with pytest.raises(ValueError, match="bonus_bet cannot be negative"):
            table.play_round(round_id=1, base_bet=5.0, bonus_bet=-1.0)

    def test_bonus_bet_requires_paytable(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify bonus_bet requires bonus paytable."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)  # No bonus paytable

        with pytest.raises(ValueError, match="bonus_bet > 0 requires a bonus_paytable"):
            table.play_round(round_id=1, base_bet=5.0, bonus_bet=1.0)


class TestTableReproducibility:
    """Tests for Table reproducibility."""

    def test_reproducible_with_same_seed(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
    ) -> None:
        """Verify Table produces identical results with same RNG seed."""
        deck1, strategy, paytable = basic_setup
        deck2 = Deck()

        table_config = TableConfig(num_seats=6)
        dealer_config = DealerConfig(discard_enabled=True, discard_cards=3)

        table1 = Table(
            deck1,
            strategy,
            paytable,
            None,
            random.Random(12345),
            table_config=table_config,
            dealer_config=dealer_config,
        )
        table2 = Table(
            deck2,
            strategy,
            paytable,
            None,
            random.Random(12345),
            table_config=table_config,
            dealer_config=dealer_config,
        )

        result1 = table1.play_round(round_id=1, base_bet=5.0)
        result2 = table2.play_round(round_id=1, base_bet=5.0)

        # Compare all results
        assert result1.community_cards == result2.community_cards
        assert result1.dealer_discards == result2.dealer_discards
        assert len(result1.seat_results) == len(result2.seat_results)

        for seat1, seat2 in zip(
            result1.seat_results, result2.seat_results, strict=True
        ):
            assert seat1.player_cards == seat2.player_cards
            assert seat1.decision_bet1 == seat2.decision_bet1
            assert seat1.decision_bet2 == seat2.decision_bet2
            assert seat1.final_hand_rank == seat2.final_hand_rank
            assert seat1.net_result == seat2.net_result


class TestTableDeckUsage:
    """Tests for correct deck usage in Table."""

    def test_deck_remaining_cards_single_seat(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify correct deck usage for single seat.

        Single seat: 3 player + 2 community = 5 cards
        52 - 5 = 47 remaining
        """
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        table.play_round(round_id=1, base_bet=5.0)

        assert deck.cards_remaining() == 47

    def test_deck_remaining_cards_six_seats(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify correct deck usage for six seats.

        Six seats: 18 player (6*3) + 2 community = 20 cards
        52 - 20 = 32 remaining
        """
        deck, strategy, paytable = basic_setup
        table_config = TableConfig(num_seats=6)
        table = Table(deck, strategy, paytable, None, rng, table_config=table_config)

        table.play_round(round_id=1, base_bet=5.0)

        assert deck.cards_remaining() == 32

    def test_deck_remaining_cards_six_seats_with_discard(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify correct deck usage for six seats with dealer discard.

        Six seats with 3 discards: 3 discard + 18 player + 2 community = 23 cards
        52 - 23 = 29 remaining
        """
        deck, strategy, paytable = basic_setup
        table_config = TableConfig(num_seats=6)
        dealer_config = DealerConfig(discard_enabled=True, discard_cards=3)
        table = Table(
            deck,
            strategy,
            paytable,
            None,
            rng,
            table_config=table_config,
            dealer_config=dealer_config,
        )

        table.play_round(round_id=1, base_bet=5.0)

        assert deck.cards_remaining() == 29


class TestTableStrategyContext:
    """Tests for strategy context handling in Table."""

    def test_default_context_used_when_none_provided(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify default context is created when none provided."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        # Should not raise - default context should be created
        result = table.play_round(round_id=1, base_bet=5.0)
        assert result is not None

    def test_custom_context_used(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify custom context is used when provided."""
        deck, strategy, paytable = basic_setup
        table = Table(deck, strategy, paytable, None, rng)

        context = StrategyContext(
            session_profit=100.0,
            hands_played=50,
            streak=3,
            bankroll=600.0,
        )

        # Should not raise - context should be accepted
        result = table.play_round(round_id=1, base_bet=5.0, context=context)
        assert result is not None
