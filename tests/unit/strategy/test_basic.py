"""Unit tests for BasicStrategy implementation.

This module tests the BasicStrategy class against the mathematically
optimal basic strategy charts for Let It Ride.
"""

import pytest

from let_it_ride.core.hand_analysis import analyze_four_cards, analyze_three_cards
from let_it_ride.strategy import BasicStrategy, Decision, StrategyContext

# Import test fixtures
from tests.fixtures.basic_strategy_cases import (
    BET1_EXCLUDED_CONSECUTIVE_PULL,
    BET1_LOW_PAIRS_PULL,
    BET1_NO_DRAW_PULL,
    BET1_PAYING_HANDS_RIDE,
    BET1_ROYAL_DRAWS_RIDE,
    BET1_SF_SPREAD4_NO_HIGH_PULL,
    BET1_SF_SPREAD4_WITH_HIGH_RIDE,
    BET1_SF_SPREAD5_1HIGH_PULL,
    BET1_SF_SPREAD5_WITH_2HIGH_RIDE,
    BET1_SUITED_CONSECUTIVE_RIDE,
    BET1_UNSUITED_CONSECUTIVE_PULL,
    BET2_FLUSH_DRAWS_RIDE,
    BET2_INSIDE_STRAIGHT_4HIGH_RIDE_CORRECT,
    BET2_INSIDE_STRAIGHT_UNDER_4HIGH_PULL,
    BET2_LOW_PAIRS_PULL,
    BET2_NO_DRAW_PULL,
    BET2_OPEN_STRAIGHT_NO_HIGH_PULL,
    BET2_OPEN_STRAIGHT_WITH_HIGH_RIDE,
    BET2_PAYING_HANDS_RIDE,
)


@pytest.fixture
def strategy() -> BasicStrategy:
    """Create a BasicStrategy instance for testing."""
    return BasicStrategy()


@pytest.fixture
def default_context() -> StrategyContext:
    """Create a default StrategyContext for testing.

    BasicStrategy doesn't use context, so this is just a placeholder.
    """
    return StrategyContext(
        session_profit=0.0,
        hands_played=0,
        streak=0,
        bankroll=1000.0,
        deck_composition=None,
    )


class TestBet1PayingHands:
    """Test Bet 1 decisions for paying hands (pair 10+, trips)."""

    @pytest.mark.parametrize("cards,expected,description", BET1_PAYING_HANDS_RIDE)
    def test_paying_hands_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that paying hands result in RIDE."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize("cards,expected,description", BET1_LOW_PAIRS_PULL)
    def test_low_pairs_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that low pairs (below 10s) result in PULL."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestBet1RoyalDraws:
    """Test Bet 1 decisions for royal flush draws."""

    @pytest.mark.parametrize("cards,expected,description", BET1_ROYAL_DRAWS_RIDE)
    def test_royal_draws_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that royal flush draws result in RIDE."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestBet1SuitedConsecutive:
    """Test Bet 1 decisions for suited consecutive hands."""

    @pytest.mark.parametrize("cards,expected,description", BET1_SUITED_CONSECUTIVE_RIDE)
    def test_suited_consecutive_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that suited consecutive (non-excluded) hands result in RIDE."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize(
        "cards,expected,description", BET1_EXCLUDED_CONSECUTIVE_PULL
    )
    def test_excluded_consecutive_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that A-2-3 and 2-3-4 suited result in PULL."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestBet1StraightFlushDraws:
    """Test Bet 1 decisions for straight flush draws with gaps."""

    @pytest.mark.parametrize(
        "cards,expected,description", BET1_SF_SPREAD4_WITH_HIGH_RIDE
    )
    def test_sf_spread4_with_high_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that SF draws with spread 4 and 1+ high card result in RIDE."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize("cards,expected,description", BET1_SF_SPREAD4_NO_HIGH_PULL)
    def test_sf_spread4_no_high_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that SF draws with spread 4 and 0 high cards result in PULL."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize(
        "cards,expected,description", BET1_SF_SPREAD5_WITH_2HIGH_RIDE
    )
    def test_sf_spread5_with_2high_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that SF draws with spread 5 and 2+ high cards result in RIDE."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize("cards,expected,description", BET1_SF_SPREAD5_1HIGH_PULL)
    def test_sf_spread5_1high_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that SF draws with spread 5 and <2 high cards result in PULL."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestBet1NoDraws:
    """Test Bet 1 decisions for hands with no draws."""

    @pytest.mark.parametrize(
        "cards,expected,description", BET1_UNSUITED_CONSECUTIVE_PULL
    )
    def test_unsuited_consecutive_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that unsuited consecutive hands result in PULL."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize("cards,expected,description", BET1_NO_DRAW_PULL)
    def test_no_draw_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that hands with no draw potential result in PULL."""
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestBet2PayingHands:
    """Test Bet 2 decisions for paying hands."""

    @pytest.mark.parametrize("cards,expected,description", BET2_PAYING_HANDS_RIDE)
    def test_paying_hands_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that paying hands result in RIDE."""
        analysis = analyze_four_cards(cards)
        result = strategy.decide_bet2(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize("cards,expected,description", BET2_LOW_PAIRS_PULL)
    def test_low_pairs_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that low pairs result in PULL."""
        analysis = analyze_four_cards(cards)
        result = strategy.decide_bet2(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestBet2FlushDraws:
    """Test Bet 2 decisions for flush draws."""

    @pytest.mark.parametrize("cards,expected,description", BET2_FLUSH_DRAWS_RIDE)
    def test_flush_draws_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that 4-card flush draws result in RIDE."""
        analysis = analyze_four_cards(cards)
        result = strategy.decide_bet2(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestBet2StraightDraws:
    """Test Bet 2 decisions for straight draws."""

    @pytest.mark.parametrize(
        "cards,expected,description", BET2_OPEN_STRAIGHT_WITH_HIGH_RIDE
    )
    def test_open_straight_with_high_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that open-ended straights with 1+ high card result in RIDE."""
        analysis = analyze_four_cards(cards)
        result = strategy.decide_bet2(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize(
        "cards,expected,description", BET2_OPEN_STRAIGHT_NO_HIGH_PULL
    )
    def test_open_straight_no_high_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that open-ended straights with 0 high cards result in PULL."""
        analysis = analyze_four_cards(cards)
        result = strategy.decide_bet2(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize(
        "cards,expected,description", BET2_INSIDE_STRAIGHT_4HIGH_RIDE_CORRECT
    )
    def test_inside_straight_4high_ride(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that inside straights with 4 high cards result in RIDE."""
        analysis = analyze_four_cards(cards)
        result = strategy.decide_bet2(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"

    @pytest.mark.parametrize(
        "cards,expected,description", BET2_INSIDE_STRAIGHT_UNDER_4HIGH_PULL
    )
    def test_inside_straight_under_4high_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that inside straights with <4 high cards result in PULL."""
        analysis = analyze_four_cards(cards)
        result = strategy.decide_bet2(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestBet2NoDraws:
    """Test Bet 2 decisions for hands with no draws."""

    @pytest.mark.parametrize("cards,expected,description", BET2_NO_DRAW_PULL)
    def test_no_draw_pull(
        self,
        strategy: BasicStrategy,
        default_context: StrategyContext,
        cards: list,
        expected: Decision,
        description: str,
    ) -> None:
        """Test that hands with no draw potential result in PULL."""
        analysis = analyze_four_cards(cards)
        result = strategy.decide_bet2(analysis, default_context)
        assert result == expected, f"{description}: expected {expected}, got {result}"


class TestStrategyProtocol:
    """Test that BasicStrategy conforms to the Strategy protocol."""

    def test_has_decide_bet1(self, strategy: BasicStrategy) -> None:
        """Test that BasicStrategy has decide_bet1 method."""
        assert hasattr(strategy, "decide_bet1")
        assert callable(strategy.decide_bet1)

    def test_has_decide_bet2(self, strategy: BasicStrategy) -> None:
        """Test that BasicStrategy has decide_bet2 method."""
        assert hasattr(strategy, "decide_bet2")
        assert callable(strategy.decide_bet2)


class TestDecisionEnum:
    """Test the Decision enum."""

    def test_decision_values(self) -> None:
        """Test that Decision has PULL and RIDE values."""
        assert Decision.PULL.value == "pull"
        assert Decision.RIDE.value == "ride"

    def test_decision_members(self) -> None:
        """Test that Decision has exactly PULL and RIDE."""
        assert set(Decision.__members__.keys()) == {"PULL", "RIDE"}


class TestStrategyContext:
    """Test the StrategyContext dataclass."""

    def test_create_context(self) -> None:
        """Test creating a StrategyContext."""
        context = StrategyContext(
            session_profit=100.0,
            hands_played=50,
            streak=3,
            bankroll=1100.0,
            deck_composition=None,
        )
        assert context.session_profit == 100.0
        assert context.hands_played == 50
        assert context.streak == 3
        assert context.bankroll == 1100.0
        assert context.deck_composition is None

    def test_context_with_deck_composition(self) -> None:
        """Test creating a StrategyContext with deck composition."""
        from let_it_ride.core.card import Rank

        composition = {Rank.ACE: 4, Rank.KING: 3}
        context = StrategyContext(
            session_profit=0.0,
            hands_played=0,
            streak=0,
            bankroll=1000.0,
            deck_composition=composition,
        )
        assert context.deck_composition == composition

    def test_context_is_frozen(self) -> None:
        """Test that StrategyContext is immutable."""
        from dataclasses import FrozenInstanceError

        context = StrategyContext(
            session_profit=0.0,
            hands_played=0,
            streak=0,
            bankroll=1000.0,
        )
        with pytest.raises(FrozenInstanceError):
            context.bankroll = 2000.0  # type: ignore[misc]
