"""Unit tests for CustomStrategy implementation.

This module tests the CustomStrategy class and its condition parsing/evaluation
capabilities, including:
- StrategyRule creation and validation
- Condition parsing and evaluation
- Boolean operators (and, or, not)
- Comparison operators (>=, <=, >, <, ==, !=)
- First-match-wins rule priority
- Default rule fallback
- Error handling for invalid conditions
"""

import pytest

from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_analysis import analyze_four_cards, analyze_three_cards
from let_it_ride.strategy import (
    ConditionParseError,
    CustomStrategy,
    Decision,
    InvalidFieldError,
    StrategyContext,
    StrategyRule,
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


class TestStrategyRule:
    """Tests for StrategyRule dataclass."""

    def test_create_valid_rule(self) -> None:
        """Test creating a valid strategy rule."""
        rule = StrategyRule(condition="has_paying_hand", action=Decision.RIDE)
        assert rule.condition == "has_paying_hand"
        assert rule.action == Decision.RIDE

    def test_create_default_rule(self) -> None:
        """Test creating a default rule."""
        rule = StrategyRule(condition="default", action=Decision.PULL)
        assert rule.condition == "default"
        assert rule.action == Decision.PULL

    def test_create_rule_with_comparison(self) -> None:
        """Test creating a rule with a comparison condition."""
        rule = StrategyRule(condition="high_cards >= 2", action=Decision.RIDE)
        assert rule.condition == "high_cards >= 2"
        assert rule.action == Decision.RIDE

    def test_create_rule_with_compound_condition(self) -> None:
        """Test creating a rule with compound condition."""
        rule = StrategyRule(
            condition="is_flush_draw and high_cards >= 1",
            action=Decision.RIDE,
        )
        assert "is_flush_draw" in rule.condition
        assert rule.action == Decision.RIDE

    def test_invalid_field_raises_error(self) -> None:
        """Test that invalid field names raise InvalidFieldError."""
        with pytest.raises(InvalidFieldError) as exc_info:
            StrategyRule(condition="invalid_field", action=Decision.RIDE)
        assert "invalid_field" in str(exc_info.value)

    def test_empty_condition_raises_error(self) -> None:
        """Test that empty condition raises ConditionParseError."""
        with pytest.raises(ConditionParseError):
            StrategyRule(condition="", action=Decision.RIDE)

    def test_whitespace_condition_raises_error(self) -> None:
        """Test that whitespace-only condition raises ConditionParseError."""
        with pytest.raises(ConditionParseError):
            StrategyRule(condition="   ", action=Decision.RIDE)

    def test_invalid_action_type_raises_error(self) -> None:
        """Test that invalid action type raises TypeError."""
        with pytest.raises(TypeError):
            StrategyRule(condition="default", action="ride")  # type: ignore[arg-type]

    def test_rule_is_frozen(self) -> None:
        """Test that StrategyRule is immutable."""
        from dataclasses import FrozenInstanceError

        rule = StrategyRule(condition="default", action=Decision.PULL)
        with pytest.raises(FrozenInstanceError):
            rule.condition = "new_condition"  # type: ignore[misc]


class TestConditionEvaluation:
    """Tests for condition evaluation logic."""

    def test_evaluate_boolean_field_true(self, default_context: StrategyContext) -> None:
        """Test evaluating a boolean field that is True."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Pair of Kings - has_paying_hand is True
        cards = make_hand("Kh Ks 5d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_evaluate_boolean_field_false(self, default_context: StrategyContext) -> None:
        """Test evaluating a boolean field that is False."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Low pair - has_paying_hand is False
        cards = make_hand("5h 5s 9d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_evaluate_comparison_gte(self, default_context: StrategyContext) -> None:
        """Test >= comparison operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="high_cards >= 2", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Two high cards (King, Queen)
        cards = make_hand("Kh Qs 5d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

        # One high card
        cards = make_hand("Kh 5s 3d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_evaluate_comparison_gt(self, default_context: StrategyContext) -> None:
        """Test > comparison operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="high_cards > 2", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Three high cards (Ace, King, Queen)
        cards = make_hand("Ah Ks Qd")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

        # Exactly two high cards
        cards = make_hand("Kh Qs 5d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_evaluate_comparison_lte(self, default_context: StrategyContext) -> None:
        """Test <= comparison operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="high_cards <= 1", action=Decision.PULL),
                StrategyRule(condition="default", action=Decision.RIDE),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # One high card
        cards = make_hand("Ah 5s 3d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

        # Two high cards
        cards = make_hand("Ah Ks 3d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_evaluate_comparison_lt(self, default_context: StrategyContext) -> None:
        """Test < comparison operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="suited_cards < 3", action=Decision.PULL),
                StrategyRule(condition="default", action=Decision.RIDE),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Two suited cards
        cards = make_hand("Ah Kh 3d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

        # Three suited cards
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_evaluate_comparison_eq(self, default_context: StrategyContext) -> None:
        """Test == comparison operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="suited_cards == 3", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Exactly 3 suited cards
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_evaluate_comparison_ne(self, default_context: StrategyContext) -> None:
        """Test != comparison operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="suited_cards != 3", action=Decision.PULL),
                StrategyRule(condition="default", action=Decision.RIDE),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # 2 suited cards (not 3)
        cards = make_hand("Ah Kh 3d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

        # 3 suited cards
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_evaluate_and_operator(self, default_context: StrategyContext) -> None:
        """Test 'and' boolean operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(
                    condition="is_flush_draw and high_cards >= 2",
                    action=Decision.RIDE,
                ),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Flush draw with 2 high cards
        cards = make_hand("Ah Kh 5h")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

        # Flush draw with only 1 high card
        cards = make_hand("Ah 5h 3h")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

        # 2 high cards but no flush draw
        cards = make_hand("Ah Ks 5d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_evaluate_or_operator(self, default_context: StrategyContext) -> None:
        """Test 'or' boolean operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(
                    condition="has_paying_hand or is_royal_draw",
                    action=Decision.RIDE,
                ),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Paying hand (pair of Kings)
        cards = make_hand("Kh Ks 5d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

        # Royal draw (not a paying hand)
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

        # Neither
        cards = make_hand("2h 5s 9d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_evaluate_not_operator(self, default_context: StrategyContext) -> None:
        """Test 'not' boolean operator."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(
                    condition="not has_paying_hand",
                    action=Decision.PULL,
                ),
                StrategyRule(condition="default", action=Decision.RIDE),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # No paying hand
        cards = make_hand("2h 5s 9d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

        # Has paying hand
        cards = make_hand("Kh Ks 5d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_evaluate_parentheses(self, default_context: StrategyContext) -> None:
        """Test parenthesized expressions."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(
                    condition="(is_flush_draw or is_straight_draw) and high_cards >= 2",
                    action=Decision.RIDE,
                ),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Flush draw with 2 high cards
        cards = make_hand("Ah Kh 5h")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

        # Flush draw but only 1 high card
        cards = make_hand("Ah 5h 3h")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL

    def test_evaluate_default(self, default_context: StrategyContext) -> None:
        """Test that 'default' condition always matches."""
        strategy = CustomStrategy(
            bet1_rules=[StrategyRule(condition="default", action=Decision.RIDE)],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Any hand should match default
        cards = make_hand("2h 5s 9d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE


class TestRulePriority:
    """Tests for rule evaluation priority (first match wins)."""

    def test_first_matching_rule_wins(self, default_context: StrategyContext) -> None:
        """Test that the first matching rule determines the decision."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="is_royal_draw", action=Decision.RIDE),
                StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
                StrategyRule(condition="is_flush_draw", action=Decision.PULL),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Royal draw is also a flush draw - first rule should win
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        result = strategy.decide_bet1(analysis, default_context)
        # Should be RIDE from is_royal_draw, not PULL from is_flush_draw
        assert result == Decision.RIDE

    def test_later_rule_matches_if_earlier_dont(
        self, default_context: StrategyContext
    ) -> None:
        """Test that later rules match if earlier ones don't."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
                StrategyRule(condition="is_royal_draw", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Royal draw without paying hand
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        # Second rule should match
        assert strategy.decide_bet1(analysis, default_context) == Decision.RIDE

    def test_default_rule_as_fallback(self, default_context: StrategyContext) -> None:
        """Test that default rule catches unmatched hands."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Hand with no paying hand
        cards = make_hand("2h 5s 9d")
        analysis = analyze_three_cards(cards)
        assert strategy.decide_bet1(analysis, default_context) == Decision.PULL


class TestCustomStrategyCreation:
    """Tests for CustomStrategy creation and configuration."""

    def test_create_with_rule_lists(self) -> None:
        """Test creating a CustomStrategy with rule lists."""
        bet1_rules = [
            StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
            StrategyRule(condition="default", action=Decision.PULL),
        ]
        bet2_rules = [
            StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
            StrategyRule(condition="default", action=Decision.PULL),
        ]
        strategy = CustomStrategy(bet1_rules=bet1_rules, bet2_rules=bet2_rules)
        assert len(strategy.bet1_rules) == 2
        assert len(strategy.bet2_rules) == 2

    def test_create_from_config(self) -> None:
        """Test creating a CustomStrategy from a config dictionary."""
        config = {
            "bet1_rules": [
                {"condition": "has_paying_hand", "action": "ride"},
                {"condition": "is_royal_draw", "action": "ride"},
                {"condition": "default", "action": "pull"},
            ],
            "bet2_rules": [
                {"condition": "has_paying_hand", "action": "ride"},
                {"condition": "default", "action": "pull"},
            ],
        }
        strategy = CustomStrategy.from_config(config)
        assert len(strategy.bet1_rules) == 3
        assert len(strategy.bet2_rules) == 2
        assert strategy.bet1_rules[0].condition == "has_paying_hand"
        assert strategy.bet1_rules[0].action == Decision.RIDE

    def test_empty_bet1_rules_raises_error(self) -> None:
        """Test that empty bet1_rules raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            CustomStrategy(
                bet1_rules=[],
                bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
            )
        assert "bet1_rules cannot be empty" in str(exc_info.value)

    def test_empty_bet2_rules_raises_error(self) -> None:
        """Test that empty bet2_rules raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            CustomStrategy(
                bet1_rules=[StrategyRule(condition="default", action=Decision.PULL)],
                bet2_rules=[],
            )
        assert "bet2_rules cannot be empty" in str(exc_info.value)

    def test_no_matching_rule_raises_error(
        self, default_context: StrategyContext
    ) -> None:
        """Test that no matching rule raises ValueError."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
                # No default rule!
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        # Hand that doesn't match any rule
        cards = make_hand("2h 5s 9d")
        analysis = analyze_three_cards(cards)
        with pytest.raises(ValueError) as exc_info:
            strategy.decide_bet1(analysis, default_context)
        assert "No rule matched" in str(exc_info.value)


class TestBet2Decisions:
    """Tests for Bet 2 (4-card) decisions."""

    def test_bet2_paying_hand_ride(self, default_context: StrategyContext) -> None:
        """Test Bet 2 decision for paying hands."""
        strategy = CustomStrategy(
            bet1_rules=[StrategyRule(condition="default", action=Decision.PULL)],
            bet2_rules=[
                StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
        )
        # Two pair
        cards = make_hand("Ah As Kd Kc")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_flush_draw_ride(self, default_context: StrategyContext) -> None:
        """Test Bet 2 decision for flush draws."""
        strategy = CustomStrategy(
            bet1_rules=[StrategyRule(condition="default", action=Decision.PULL)],
            bet2_rules=[
                StrategyRule(condition="is_flush_draw", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
        )
        # 4-card flush draw
        cards = make_hand("2h 5h 9h Kh")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.RIDE

    def test_bet2_no_draw_pull(self, default_context: StrategyContext) -> None:
        """Test Bet 2 decision for hands with no draws."""
        strategy = CustomStrategy(
            bet1_rules=[StrategyRule(condition="default", action=Decision.PULL)],
            bet2_rules=[
                StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
        )
        # No paying hand, no draws
        cards = make_hand("2h 5s 9d Kc")
        analysis = analyze_four_cards(cards)
        assert strategy.decide_bet2(analysis, default_context) == Decision.PULL


class TestAllValidFields:
    """Tests to ensure all valid HandAnalysis fields work in conditions."""

    @pytest.mark.parametrize(
        "field",
        [
            "high_cards",
            "suited_cards",
            "connected_cards",
            "gaps",
            "suited_high_cards",
            "straight_flush_spread",
        ],
    )
    def test_numeric_fields(
        self, field: str, default_context: StrategyContext
    ) -> None:
        """Test that all numeric fields can be used in conditions."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition=f"{field} >= 0", action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        # Should not raise, field should be accessible
        result = strategy.decide_bet1(analysis, default_context)
        assert result in (Decision.RIDE, Decision.PULL)

    @pytest.mark.parametrize(
        "field",
        [
            "has_paying_hand",
            "has_pair",
            "has_high_pair",
            "has_trips",
            "is_flush_draw",
            "is_straight_draw",
            "is_open_straight_draw",
            "is_inside_straight_draw",
            "is_straight_flush_draw",
            "is_royal_draw",
            "is_excluded_sf_consecutive",
        ],
    )
    def test_boolean_fields(
        self, field: str, default_context: StrategyContext
    ) -> None:
        """Test that all boolean fields can be used in conditions."""
        strategy = CustomStrategy(
            bet1_rules=[
                StrategyRule(condition=field, action=Decision.RIDE),
                StrategyRule(condition="default", action=Decision.PULL),
            ],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        cards = make_hand("Ah Kh Qh")
        analysis = analyze_three_cards(cards)
        # Should not raise, field should be accessible
        result = strategy.decide_bet1(analysis, default_context)
        assert result in (Decision.RIDE, Decision.PULL)


class TestStrategyProtocol:
    """Tests that CustomStrategy conforms to the Strategy protocol."""

    def test_has_decide_bet1(self) -> None:
        """Test that CustomStrategy has decide_bet1 method."""
        strategy = CustomStrategy(
            bet1_rules=[StrategyRule(condition="default", action=Decision.PULL)],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        assert hasattr(strategy, "decide_bet1")
        assert callable(strategy.decide_bet1)

    def test_has_decide_bet2(self) -> None:
        """Test that CustomStrategy has decide_bet2 method."""
        strategy = CustomStrategy(
            bet1_rules=[StrategyRule(condition="default", action=Decision.PULL)],
            bet2_rules=[StrategyRule(condition="default", action=Decision.PULL)],
        )
        assert hasattr(strategy, "decide_bet2")
        assert callable(strategy.decide_bet2)
