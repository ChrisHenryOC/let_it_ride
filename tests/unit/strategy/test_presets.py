"""Unit tests for preset strategy implementations.

This module tests the preset strategy factory functions:
- conservative_strategy: Only rides on made hands
- aggressive_strategy: Rides on any draw

These tests verify that the presets behave according to their documented
specifications and conform to the Strategy protocol.
"""

import pytest

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_analysis import analyze_four_cards, analyze_three_cards
from let_it_ride.strategy import (
    CustomStrategy,
    Decision,
    StrategyContext,
    aggressive_strategy,
    conservative_strategy,
)


# Helper functions for creating test cards
def make_card(notation: str) -> Card:
    """Create a Card from notation like 'Ah' (Ace of Hearts)."""
    rank_map = {
        "2": Rank.TWO, "3": Rank.THREE, "4": Rank.FOUR, "5": Rank.FIVE,
        "6": Rank.SIX, "7": Rank.SEVEN, "8": Rank.EIGHT, "9": Rank.NINE,
        "T": Rank.TEN, "J": Rank.JACK, "Q": Rank.QUEEN, "K": Rank.KING,
        "A": Rank.ACE,
    }
    suit_map = {"c": Suit.CLUBS, "d": Suit.DIAMONDS, "h": Suit.HEARTS, "s": Suit.SPADES}
    return Card(rank_map[notation[0]], suit_map[notation[1]])


def make_hand(notations: str) -> list[Card]:
    """Create a hand from space-separated notation like 'Ah Kh Qh'."""
    return [make_card(n) for n in notations.split()]


@pytest.fixture
def default_context() -> StrategyContext:
    """Create a default StrategyContext for testing."""
    return StrategyContext(
        session_profit=0.0,
        hands_played=0,
        streak=0,
        bankroll=1000.0,
        deck_composition=None,
    )


class TestConservativeStrategy:
    """Tests for conservative_strategy preset."""

    @pytest.fixture
    def strategy(self) -> CustomStrategy:
        """Create a conservative strategy for testing."""
        return conservative_strategy()

    def test_returns_custom_strategy(self) -> None:
        """Test that conservative_strategy returns a CustomStrategy instance."""
        strategy = conservative_strategy()
        assert isinstance(strategy, CustomStrategy)

    # === Bet 1 Tests ===

    def test_bet1_paying_hand_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that paying hands result in RIDE for Bet 1."""
        # Pair of Kings
        cards = make_hand("Kh Ks 5d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_bet1_trips_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that trips result in RIDE for Bet 1."""
        cards = make_hand("Kh Ks Kd")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_bet1_low_pair_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that low pairs result in PULL for Bet 1."""
        # Pair of 5s (not a paying hand)
        cards = make_hand("5h 5s Ad")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_bet1_royal_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that royal draws result in PULL (conservative ignores draws)."""
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_bet1_flush_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that flush draws result in PULL (conservative ignores draws)."""
        cards = make_hand("2h 5h 9h")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_bet1_straight_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that straight draws result in PULL (conservative ignores draws)."""
        cards = make_hand("5h 6h 7h")
        analysis = analyze_three_cards(cards)
        # This is actually a straight flush draw, but conservative ignores it
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_bet1_no_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that garbage hands result in PULL."""
        cards = make_hand("2h 5s 9d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    # === Bet 2 Tests ===

    def test_bet2_paying_hand_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that paying hands result in RIDE for Bet 2."""
        # Pair of Kings
        cards = make_hand("Kh Ks 5d 2c")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_two_pair_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that two pair results in RIDE for Bet 2."""
        cards = make_hand("Kh Ks 5d 5c")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_trips_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that trips result in RIDE for Bet 2."""
        cards = make_hand("Kh Ks Kd 5c")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_flush_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that flush draws result in PULL (conservative ignores draws)."""
        cards = make_hand("2h 5h 9h Kh")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.PULL

    def test_bet2_open_straight_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that open-ended straights result in PULL (conservative ignores draws)."""
        cards = make_hand("8h 9s Td Jc")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.PULL

    def test_bet2_no_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that garbage hands result in PULL."""
        cards = make_hand("2h 5s 9d Kc")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.PULL


class TestAggressiveStrategy:
    """Tests for aggressive_strategy preset."""

    @pytest.fixture
    def strategy(self) -> CustomStrategy:
        """Create an aggressive strategy for testing."""
        return aggressive_strategy()

    def test_returns_custom_strategy(self) -> None:
        """Test that aggressive_strategy returns a CustomStrategy instance."""
        strategy = aggressive_strategy()
        assert isinstance(strategy, CustomStrategy)

    # === Bet 1 Tests ===

    def test_bet1_paying_hand_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that paying hands result in RIDE for Bet 1."""
        cards = make_hand("Kh Ks 5d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_bet1_flush_draw_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that flush draws result in RIDE for Bet 1."""
        cards = make_hand("2h 5h 9h")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_bet1_straight_draw_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that straight draws result in RIDE for Bet 1."""
        # 5-6-7 suited is both a flush draw and straight draw
        cards = make_hand("5h 6h 7h")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_bet1_straight_draw_unsuited_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that unsuited straight draws result in RIDE for Bet 1."""
        cards = make_hand("5h 6s 7d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_bet1_royal_draw_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that royal draws result in RIDE for Bet 1."""
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        # Royal draw is also a flush draw, should ride
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_bet1_low_pair_no_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that low pairs without draws result in PULL for Bet 1."""
        # Pair of 5s with no draws
        cards = make_hand("5h 5s 2d")
        analysis = analyze_three_cards(cards)
        # Has pair but not a paying hand, and no flush/straight draw
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_bet1_no_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that garbage hands result in PULL for Bet 1."""
        cards = make_hand("2h 5s 9d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    # === Bet 2 Tests ===

    def test_bet2_paying_hand_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that paying hands result in RIDE for Bet 2."""
        cards = make_hand("Kh Ks 5d 2c")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_flush_draw_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that flush draws result in RIDE for Bet 2."""
        cards = make_hand("2h 5h 9h Kh")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_open_straight_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that open-ended straights result in RIDE for Bet 2."""
        cards = make_hand("8h 9s Td Jc")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_inside_straight_ride(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that inside straights result in RIDE for Bet 2."""
        cards = make_hand("5h 6s 8d 9c")
        analysis = analyze_four_cards(cards)
        # Inside straight is still a straight draw
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_no_draw_pull(
        self, strategy: CustomStrategy, default_context: StrategyContext
    ) -> None:
        """Test that garbage hands result in PULL for Bet 2."""
        cards = make_hand("2h 5s 9d Kc")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.PULL


class TestPresetComparison:
    """Tests comparing conservative vs aggressive strategy behavior."""

    @pytest.fixture
    def conservative(self) -> CustomStrategy:
        """Create conservative strategy."""
        return conservative_strategy()

    @pytest.fixture
    def aggressive(self) -> CustomStrategy:
        """Create aggressive strategy."""
        return aggressive_strategy()

    def test_both_ride_on_paying_hands(
        self,
        conservative: CustomStrategy,
        aggressive: CustomStrategy,
        default_context: StrategyContext,
    ) -> None:
        """Test that both strategies ride on paying hands."""
        cards = make_hand("Kh Ks 5d")
        analysis = analyze_three_cards(cards)
        assert conservative.decide_bet1(analysis, default_context) == Decision.RIDE
        assert aggressive.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_differ_on_draws(
        self,
        conservative: CustomStrategy,
        aggressive: CustomStrategy,
        default_context: StrategyContext,
    ) -> None:
        """Test that strategies differ on draws."""
        # Flush draw without paying hand
        cards = make_hand("2h 5h 9h")
        analysis = analyze_three_cards(cards)
        assert conservative.decide_bet1(analysis, default_context) == Decision.PULL
        assert aggressive.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_both_pull_on_garbage(
        self,
        conservative: CustomStrategy,
        aggressive: CustomStrategy,
        default_context: StrategyContext,
    ) -> None:
        """Test that both strategies pull on garbage hands."""
        cards = make_hand("2h 5s 9d")
        analysis = analyze_three_cards(cards)
        assert conservative.decide_bet1(analysis, default_context) == Decision.PULL
        assert aggressive.decide_bet1(analysis, default_context) == Decision.PULL


class TestStrategyProtocol:
    """Tests that preset strategies conform to the Strategy protocol."""

    def test_conservative_has_decide_bet1(self) -> None:
        """Test that conservative strategy has decide_bet1 method."""
        strategy = conservative_strategy()
        assert hasattr(strategy, "decide_bet1")
        assert callable(strategy.decide_bet1)

    def test_conservative_has_decide_bet2(self) -> None:
        """Test that conservative strategy has decide_bet2 method."""
        strategy = conservative_strategy()
        assert hasattr(strategy, "decide_bet2")
        assert callable(strategy.decide_bet2)

    def test_aggressive_has_decide_bet1(self) -> None:
        """Test that aggressive strategy has decide_bet1 method."""
        strategy = aggressive_strategy()
        assert hasattr(strategy, "decide_bet1")
        assert callable(strategy.decide_bet1)

    def test_aggressive_has_decide_bet2(self) -> None:
        """Test that aggressive strategy has decide_bet2 method."""
        strategy = aggressive_strategy()
        assert hasattr(strategy, "decide_bet2")
        assert callable(strategy.decide_bet2)
