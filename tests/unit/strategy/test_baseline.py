"""Unit tests for baseline strategy implementations.

This module tests AlwaysRideStrategy and AlwaysPullStrategy,
which serve as variance bounds for strategy comparison.
"""

import pytest

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_analysis import analyze_four_cards, analyze_three_cards
from let_it_ride.strategy import (
    AlwaysPullStrategy,
    AlwaysRideStrategy,
    Decision,
    StrategyContext,
)


def make_card(notation: str) -> Card:
    """Create a Card from notation like 'Ah' (Ace of Hearts).

    Args:
        notation: Two-character string, first char is rank, second is suit.
            Ranks: 2-9, T, J, Q, K, A
            Suits: c (clubs), d (diamonds), h (hearts), s (spades)
    """
    rank_map = {
        "2": Rank.TWO,
        "3": Rank.THREE,
        "4": Rank.FOUR,
        "5": Rank.FIVE,
        "6": Rank.SIX,
        "7": Rank.SEVEN,
        "8": Rank.EIGHT,
        "9": Rank.NINE,
        "T": Rank.TEN,
        "J": Rank.JACK,
        "Q": Rank.QUEEN,
        "K": Rank.KING,
        "A": Rank.ACE,
    }
    suit_map = {
        "c": Suit.CLUBS,
        "d": Suit.DIAMONDS,
        "h": Suit.HEARTS,
        "s": Suit.SPADES,
    }
    return Card(rank_map[notation[0]], suit_map[notation[1]])


def make_hand(notations: str) -> list[Card]:
    """Create a hand from space-separated notation like 'Ah Kh Qh'."""
    return [make_card(n) for n in notations.split()]


@pytest.fixture
def always_ride_strategy() -> AlwaysRideStrategy:
    """Create an AlwaysRideStrategy instance for testing."""
    return AlwaysRideStrategy()


@pytest.fixture
def always_pull_strategy() -> AlwaysPullStrategy:
    """Create an AlwaysPullStrategy instance for testing."""
    return AlwaysPullStrategy()


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


# Sample hands for testing - a variety of hand types
THREE_CARD_HANDS = [
    "Ah Kh Qh",  # Strong royal draw
    "2c 7d Ks",  # Weak garbage hand
    "Ts Ts 5c",  # Paying pair of tens
    "3h 4h 5h",  # Suited consecutive
    "9c 9d 9s",  # Trips
]

FOUR_CARD_HANDS = [
    "Ah Kh Qh Jh",  # Strong flush draw
    "2c 7d Ks 4s",  # Weak garbage hand
    "Ts Ts 5c 2d",  # Pair of tens
    "3h 4h 5h 6h",  # Made flush draw
    "Ac Ad As 2h",  # Trips
]


class TestAlwaysRideStrategyBet1:
    """Test AlwaysRideStrategy.decide_bet1 always returns RIDE."""

    @pytest.mark.parametrize("hand_notation", THREE_CARD_HANDS)
    def test_always_returns_ride(
        self,
        always_ride_strategy: AlwaysRideStrategy,
        default_context: StrategyContext,
        hand_notation: str,
    ) -> None:
        """Test that decide_bet1 always returns RIDE regardless of hand."""
        cards = make_hand(hand_notation)
        analysis = analyze_three_cards(cards)
        result = always_ride_strategy.decide_bet1(analysis, default_context)
        assert result == Decision.RIDE, f"Expected RIDE for {hand_notation}"


class TestAlwaysRideStrategyBet2:
    """Test AlwaysRideStrategy.decide_bet2 always returns RIDE."""

    @pytest.mark.parametrize("hand_notation", FOUR_CARD_HANDS)
    def test_always_returns_ride(
        self,
        always_ride_strategy: AlwaysRideStrategy,
        default_context: StrategyContext,
        hand_notation: str,
    ) -> None:
        """Test that decide_bet2 always returns RIDE regardless of hand."""
        cards = make_hand(hand_notation)
        analysis = analyze_four_cards(cards)
        result = always_ride_strategy.decide_bet2(analysis, default_context)
        assert result == Decision.RIDE, f"Expected RIDE for {hand_notation}"


class TestAlwaysPullStrategyBet1:
    """Test AlwaysPullStrategy.decide_bet1 always returns PULL."""

    @pytest.mark.parametrize("hand_notation", THREE_CARD_HANDS)
    def test_always_returns_pull(
        self,
        always_pull_strategy: AlwaysPullStrategy,
        default_context: StrategyContext,
        hand_notation: str,
    ) -> None:
        """Test that decide_bet1 always returns PULL regardless of hand."""
        cards = make_hand(hand_notation)
        analysis = analyze_three_cards(cards)
        result = always_pull_strategy.decide_bet1(analysis, default_context)
        assert result == Decision.PULL, f"Expected PULL for {hand_notation}"


class TestAlwaysPullStrategyBet2:
    """Test AlwaysPullStrategy.decide_bet2 always returns PULL."""

    @pytest.mark.parametrize("hand_notation", FOUR_CARD_HANDS)
    def test_always_returns_pull(
        self,
        always_pull_strategy: AlwaysPullStrategy,
        default_context: StrategyContext,
        hand_notation: str,
    ) -> None:
        """Test that decide_bet2 always returns PULL regardless of hand."""
        cards = make_hand(hand_notation)
        analysis = analyze_four_cards(cards)
        result = always_pull_strategy.decide_bet2(analysis, default_context)
        assert result == Decision.PULL, f"Expected PULL for {hand_notation}"


class TestContextIndependence:
    """Test that baseline strategies ignore context values."""

    @pytest.mark.parametrize(
        "session_profit,hands_played,streak,bankroll",
        [
            (0.0, 0, 0, 1000.0),  # Default state
            (500.0, 100, 5, 1500.0),  # Winning session
            (-500.0, 100, -5, 500.0),  # Losing session
            (0.0, 1000, 0, 10000.0),  # Many hands, large bankroll
        ],
    )
    def test_always_ride_ignores_context(
        self,
        always_ride_strategy: AlwaysRideStrategy,
        session_profit: float,
        hands_played: int,
        streak: int,
        bankroll: float,
    ) -> None:
        """Test that AlwaysRideStrategy returns RIDE regardless of context."""
        context = StrategyContext(
            session_profit=session_profit,
            hands_played=hands_played,
            streak=streak,
            bankroll=bankroll,
            deck_composition=None,
        )
        cards = make_hand("2c 7d Ks")  # Weak hand
        analysis = analyze_three_cards(cards)

        result = always_ride_strategy.decide_bet1(analysis, context)
        assert result == Decision.RIDE

    @pytest.mark.parametrize(
        "session_profit,hands_played,streak,bankroll",
        [
            (0.0, 0, 0, 1000.0),  # Default state
            (500.0, 100, 5, 1500.0),  # Winning session
            (-500.0, 100, -5, 500.0),  # Losing session
            (0.0, 1000, 0, 10000.0),  # Many hands, large bankroll
        ],
    )
    def test_always_pull_ignores_context(
        self,
        always_pull_strategy: AlwaysPullStrategy,
        session_profit: float,
        hands_played: int,
        streak: int,
        bankroll: float,
    ) -> None:
        """Test that AlwaysPullStrategy returns PULL regardless of context."""
        context = StrategyContext(
            session_profit=session_profit,
            hands_played=hands_played,
            streak=streak,
            bankroll=bankroll,
            deck_composition=None,
        )
        cards = make_hand("Ah Kh Qh")  # Strong hand
        analysis = analyze_three_cards(cards)

        result = always_pull_strategy.decide_bet1(analysis, context)
        assert result == Decision.PULL


class TestStrategyProtocolConformance:
    """Test that baseline strategies conform to the Strategy protocol."""

    def test_always_ride_has_decide_bet1(
        self, always_ride_strategy: AlwaysRideStrategy
    ) -> None:
        """Test that AlwaysRideStrategy has decide_bet1 method."""
        assert hasattr(always_ride_strategy, "decide_bet1")
        assert callable(always_ride_strategy.decide_bet1)

    def test_always_ride_has_decide_bet2(
        self, always_ride_strategy: AlwaysRideStrategy
    ) -> None:
        """Test that AlwaysRideStrategy has decide_bet2 method."""
        assert hasattr(always_ride_strategy, "decide_bet2")
        assert callable(always_ride_strategy.decide_bet2)

    def test_always_pull_has_decide_bet1(
        self, always_pull_strategy: AlwaysPullStrategy
    ) -> None:
        """Test that AlwaysPullStrategy has decide_bet1 method."""
        assert hasattr(always_pull_strategy, "decide_bet1")
        assert callable(always_pull_strategy.decide_bet1)

    def test_always_pull_has_decide_bet2(
        self, always_pull_strategy: AlwaysPullStrategy
    ) -> None:
        """Test that AlwaysPullStrategy has decide_bet2 method."""
        assert hasattr(always_pull_strategy, "decide_bet2")
        assert callable(always_pull_strategy.decide_bet2)


class TestStrategyProtocolTyping:
    """Test that baseline strategies can be used where Strategy protocol is expected."""

    def test_always_ride_as_strategy(
        self,
        always_ride_strategy: AlwaysRideStrategy,
        default_context: StrategyContext,
    ) -> None:
        """Test that AlwaysRideStrategy can be used as a Strategy."""
        from let_it_ride.strategy import Strategy

        def use_strategy(strategy: Strategy) -> Decision:
            cards = make_hand("Ah Kh Qh")
            analysis = analyze_three_cards(cards)
            return strategy.decide_bet1(analysis, default_context)

        result = use_strategy(always_ride_strategy)
        assert result == Decision.RIDE

    def test_always_pull_as_strategy(
        self,
        always_pull_strategy: AlwaysPullStrategy,
        default_context: StrategyContext,
    ) -> None:
        """Test that AlwaysPullStrategy can be used as a Strategy."""
        from let_it_ride.strategy import Strategy

        def use_strategy(strategy: Strategy) -> Decision:
            cards = make_hand("Ah Kh Qh")
            analysis = analyze_three_cards(cards)
            return strategy.decide_bet1(analysis, default_context)

        result = use_strategy(always_pull_strategy)
        assert result == Decision.PULL
