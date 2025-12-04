"""Unit tests for dealer discard mechanics."""

import random

import pytest

from let_it_ride.config.models import DealerConfig
from let_it_ride.config.paytables import MainGamePaytable, standard_main_paytable
from let_it_ride.core.deck import Deck
from let_it_ride.core.game_engine import GameEngine
from let_it_ride.strategy.basic import BasicStrategy


@pytest.fixture
def basic_setup() -> tuple[Deck, BasicStrategy, MainGamePaytable]:
    """Provide basic components for GameEngine tests."""
    deck = Deck()
    strategy = BasicStrategy()
    paytable = standard_main_paytable()
    return deck, strategy, paytable


class TestDealerConfigModel:
    """Tests for DealerConfig validation."""

    def test_default_values(self) -> None:
        """Verify DealerConfig has correct defaults."""
        config = DealerConfig()
        assert config.discard_enabled is False
        assert config.discard_cards == 3

    def test_custom_values(self) -> None:
        """Verify DealerConfig accepts custom values."""
        config = DealerConfig(discard_enabled=True, discard_cards=5)
        assert config.discard_enabled is True
        assert config.discard_cards == 5

    def test_discard_cards_minimum(self) -> None:
        """Verify discard_cards must be at least 1."""
        with pytest.raises(ValueError):
            DealerConfig(discard_cards=0)

    def test_discard_cards_maximum(self) -> None:
        """Verify discard_cards must be at most 10."""
        with pytest.raises(ValueError):
            DealerConfig(discard_cards=11)

    def test_discard_cards_boundary_values(self) -> None:
        """Verify boundary values are accepted."""
        config_min = DealerConfig(discard_cards=1)
        assert config_min.discard_cards == 1

        config_max = DealerConfig(discard_cards=10)
        assert config_max.discard_cards == 10

    def test_discard_cards_invalid_types(self) -> None:
        """Verify discard_cards rejects invalid types."""
        with pytest.raises(ValueError):
            DealerConfig(discard_cards=3.5)  # type: ignore[arg-type]

        with pytest.raises(ValueError):
            DealerConfig(discard_cards="three")  # type: ignore[arg-type]


class TestDealerDiscardDisabled:
    """Tests for GameEngine with dealer discard disabled (backwards compatibility)."""

    def test_no_discard_by_default(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify no cards are discarded when dealer_config is not provided."""
        deck, strategy, paytable = basic_setup
        engine = GameEngine(deck, strategy, paytable, None, rng)

        engine.play_hand(hand_id=1, base_bet=5.0)

        assert engine.last_discarded_cards() == ()

    def test_no_discard_when_disabled(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify no cards are discarded when discard_enabled=False."""
        deck, strategy, paytable = basic_setup
        config = DealerConfig(discard_enabled=False, discard_cards=3)
        engine = GameEngine(deck, strategy, paytable, None, rng, config)

        engine.play_hand(hand_id=1, base_bet=5.0)

        assert engine.last_discarded_cards() == ()

    def test_deck_has_expected_remaining_cards_without_discard(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify deck has 47 cards remaining when discard is disabled.

        Standard game deals: 3 player + 2 community = 5 cards
        52 - 5 = 47 remaining
        """
        deck, strategy, paytable = basic_setup
        engine = GameEngine(deck, strategy, paytable, None, rng)

        engine.play_hand(hand_id=1, base_bet=5.0)

        assert deck.cards_remaining() == 47


class TestDealerDiscardEnabled:
    """Tests for GameEngine with dealer discard enabled."""

    def test_discard_correct_number_of_cards(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify correct number of cards are discarded."""
        deck, strategy, paytable = basic_setup
        config = DealerConfig(discard_enabled=True, discard_cards=3)
        engine = GameEngine(deck, strategy, paytable, None, rng, config)

        engine.play_hand(hand_id=1, base_bet=5.0)

        assert len(engine.last_discarded_cards()) == 3

    def test_discard_different_card_counts(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify different discard card counts work correctly."""
        deck, strategy, paytable = basic_setup

        for discard_count in [1, 2, 5, 10]:
            config = DealerConfig(discard_enabled=True, discard_cards=discard_count)
            engine = GameEngine(deck, strategy, paytable, None, rng, config)

            engine.play_hand(hand_id=1, base_bet=5.0)

            assert len(engine.last_discarded_cards()) == discard_count

    def test_deck_remaining_cards_with_discard(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify deck has correct remaining cards after discard.

        Discard: 3 cards
        Player + community: 5 cards
        52 - 3 - 5 = 44 remaining
        """
        deck, strategy, paytable = basic_setup
        config = DealerConfig(discard_enabled=True, discard_cards=3)
        engine = GameEngine(deck, strategy, paytable, None, rng, config)

        engine.play_hand(hand_id=1, base_bet=5.0)

        assert deck.cards_remaining() == 44

    def test_discarded_cards_tracked_for_validation(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify discarded cards are available for statistical validation."""
        deck, strategy, paytable = basic_setup
        config = DealerConfig(discard_enabled=True, discard_cards=3)
        engine = GameEngine(deck, strategy, paytable, None, rng, config)

        engine.play_hand(hand_id=1, base_bet=5.0)
        discarded = engine.last_discarded_cards()

        # All discarded cards should be valid Card objects
        assert len(discarded) == 3
        assert all(hasattr(card, "rank") and hasattr(card, "suit") for card in discarded)

    def test_discarded_cards_returns_immutable_tuple(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify last_discarded_cards returns an immutable tuple."""
        deck, strategy, paytable = basic_setup
        config = DealerConfig(discard_enabled=True, discard_cards=3)
        engine = GameEngine(deck, strategy, paytable, None, rng, config)

        engine.play_hand(hand_id=1, base_bet=5.0)
        discarded = engine.last_discarded_cards()

        # Should return a tuple (immutable)
        assert isinstance(discarded, tuple)
        assert len(discarded) == 3

        # Multiple calls should return equal tuples
        assert engine.last_discarded_cards() == discarded


class TestDealerDiscardIntegration:
    """Integration tests for dealer discard mechanics."""

    def test_discarded_cards_removed_from_play(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify discarded cards are not in player or community cards."""
        deck, strategy, paytable = basic_setup
        config = DealerConfig(discard_enabled=True, discard_cards=3)
        engine = GameEngine(deck, strategy, paytable, None, rng, config)

        result = engine.play_hand(hand_id=1, base_bet=5.0)
        discarded = engine.last_discarded_cards()

        # Get all cards dealt to player and community
        player_and_community = list(result.player_cards) + list(result.community_cards)

        # No discarded card should appear in player/community cards
        for card in discarded:
            assert card not in player_and_community

    def test_all_dealt_cards_are_unique(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify all cards (discarded + player + community) are unique."""
        deck, strategy, paytable = basic_setup
        config = DealerConfig(discard_enabled=True, discard_cards=3)
        engine = GameEngine(deck, strategy, paytable, None, rng, config)

        result = engine.play_hand(hand_id=1, base_bet=5.0)
        discarded = engine.last_discarded_cards()

        # Combine all cards dealt
        all_cards = list(discarded) + list(result.player_cards) + list(result.community_cards)

        # All cards should be unique
        assert len(all_cards) == len(set(all_cards))

    def test_discard_resets_each_hand(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
        rng: random.Random,
    ) -> None:
        """Verify discarded cards are reset for each new hand."""
        deck, strategy, paytable = basic_setup
        config = DealerConfig(discard_enabled=True, discard_cards=3)
        engine = GameEngine(deck, strategy, paytable, None, rng, config)

        # Play first hand
        engine.play_hand(hand_id=1, base_bet=5.0)
        first_discarded = engine.last_discarded_cards()

        # Play second hand
        engine.play_hand(hand_id=2, base_bet=5.0)
        second_discarded = engine.last_discarded_cards()

        # Should have fresh discards each hand
        assert len(first_discarded) == 3
        assert len(second_discarded) == 3
        # Cards may or may not be different (depends on RNG), but list should be fresh
        assert first_discarded is not second_discarded

    def test_reproducible_with_same_seed(
        self,
        basic_setup: tuple[Deck, BasicStrategy, MainGamePaytable],
    ) -> None:
        """Verify dealer discard is reproducible with same RNG seed."""
        deck1, strategy, paytable = basic_setup
        deck2 = Deck()
        config = DealerConfig(discard_enabled=True, discard_cards=3)

        # Create two engines with same seed
        engine1 = GameEngine(
            deck1, strategy, paytable, None, random.Random(12345), config
        )
        engine2 = GameEngine(
            deck2, strategy, paytable, None, random.Random(12345), config
        )

        result1 = engine1.play_hand(hand_id=1, base_bet=5.0)
        result2 = engine2.play_hand(hand_id=1, base_bet=5.0)

        # Discarded cards should be identical
        assert engine1.last_discarded_cards() == engine2.last_discarded_cards()
        # Player cards should also be identical
        assert result1.player_cards == result2.player_cards
