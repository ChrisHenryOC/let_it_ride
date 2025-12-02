"""Custom strategy implementation for Let It Ride.

This module implements configurable strategies that evaluate rules defined
in YAML configuration files. Rules are evaluated in order, and the first
matching rule determines the action. A default rule provides fallback behavior.

Example configuration:
    bet1_rules:
      - condition: "has_paying_hand"
        action: "ride"
      - condition: "is_royal_draw"
        action: "ride"
      - condition: "default"
        action: "pull"
"""

import re
from dataclasses import dataclass
from typing import Any

from let_it_ride.core.hand_analysis import HandAnalysis
from let_it_ride.strategy.base import Decision, StrategyContext

# Valid HandAnalysis field names that can be used in conditions
_VALID_FIELDS = frozenset(
    {
        # Numeric fields
        "high_cards",
        "suited_cards",
        "connected_cards",
        "gaps",
        "suited_high_cards",
        "straight_flush_spread",
        # Boolean fields
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
    }
)

# Pattern for valid identifiers (field names)
_IDENTIFIER_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")

# Pattern for comparison operators
_COMPARISON_PATTERN = re.compile(r"(>=|<=|>|<|==|!=)")

# Pattern for tokenizing conditions
_TOKEN_PATTERN = re.compile(
    r"(\s+|>=|<=|>|<|==|!=|\(|\)|and|or|not|\d+|[a-z_][a-z0-9_]*)"
)


class ConditionParseError(ValueError):
    """Raised when a condition string cannot be parsed."""


class InvalidFieldError(ValueError):
    """Raised when a condition references an invalid HandAnalysis field."""


@dataclass(frozen=True)
class StrategyRule:
    """A single rule in a custom strategy.

    Attributes:
        condition: The condition to evaluate. Can be:
            - "default" - matches all hands (use as fallback)
            - A HandAnalysis field name (e.g., "has_paying_hand")
            - A comparison (e.g., "high_cards >= 2")
            - A compound expression (e.g., "is_royal_draw and suited_high_cards >= 3")
        action: The decision to make if the condition matches.
    """

    condition: str
    action: Decision

    def __post_init__(self) -> None:
        """Validate the rule after creation."""
        # Validate action is a Decision
        if not isinstance(self.action, Decision):
            raise TypeError(f"action must be a Decision, got {type(self.action)}")

        # Validate condition syntax (unless it's "default")
        if self.condition != "default":
            _validate_condition(self.condition)


def _validate_condition(condition: str) -> None:
    """Validate a condition string for syntax and field references.

    Args:
        condition: The condition string to validate.

    Raises:
        ConditionParseError: If the condition has invalid syntax.
        InvalidFieldError: If the condition references an invalid field.
    """
    if not condition or not condition.strip():
        raise ConditionParseError("Condition cannot be empty")

    # Tokenize and validate
    tokens = _tokenize(condition)
    if not tokens:
        raise ConditionParseError(f"Could not parse condition: {condition}")

    # Extract field references and validate
    for token in tokens:
        is_identifier = _IDENTIFIER_PATTERN.match(token) is not None
        is_keyword = token in ("and", "or", "not")
        if is_identifier and not is_keyword and token not in _VALID_FIELDS:
            raise InvalidFieldError(
                f"Invalid field '{token}' in condition. "
                f"Valid fields are: {sorted(_VALID_FIELDS)}"
            )


def _tokenize(condition: str) -> list[str]:
    """Tokenize a condition string into components.

    Args:
        condition: The condition string to tokenize.

    Returns:
        List of tokens (identifiers, operators, numbers).
    """
    tokens = []
    for match in _TOKEN_PATTERN.finditer(condition.lower()):
        token = match.group(1)
        if not token.isspace():
            tokens.append(token)
    return tokens


def _evaluate_condition(condition: str, analysis: HandAnalysis) -> bool:
    """Evaluate a condition against a hand analysis.

    This function safely evaluates condition expressions without using eval().
    It parses the condition and evaluates it using the HandAnalysis fields.

    Args:
        condition: The condition string to evaluate.
        analysis: The hand analysis to evaluate against.

    Returns:
        True if the condition matches, False otherwise.
    """
    if condition == "default":
        return True

    tokens = _tokenize(condition)
    if not tokens:
        return False

    # Build expression tree and evaluate
    return _evaluate_tokens(tokens, analysis)


def _evaluate_tokens(tokens: list[str], analysis: HandAnalysis) -> bool:
    """Evaluate a list of tokens as a boolean expression.

    Implements a simple recursive descent parser for boolean expressions
    with support for and, or, not, and comparisons.

    Grammar:
        expression -> or_expr
        or_expr -> and_expr ('or' and_expr)*
        and_expr -> not_expr ('and' not_expr)*
        not_expr -> 'not' not_expr | comparison
        comparison -> primary (comp_op primary)?
        primary -> field | number | '(' expression ')'

    Args:
        tokens: List of tokens to evaluate.
        analysis: The hand analysis to evaluate against.

    Returns:
        Boolean result of the expression.
    """
    parser = _ExpressionParser(tokens, analysis)
    return parser.parse()


class _ExpressionParser:
    """Recursive descent parser for condition expressions."""

    def __init__(self, tokens: list[str], analysis: HandAnalysis) -> None:
        self.tokens = tokens
        self.analysis = analysis
        self.pos = 0

    def parse(self) -> bool:
        """Parse and evaluate the full expression."""
        result = self._or_expr()
        # Ensure all tokens consumed
        if self.pos < len(self.tokens):
            raise ConditionParseError(
                f"Unexpected token: {self.tokens[self.pos]} at position {self.pos}"
            )
        return result

    def _current(self) -> str | None:
        """Get current token or None if exhausted."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self) -> str | None:
        """Advance to next token and return the previous one."""
        token = self._current()
        self.pos += 1
        return token

    def _or_expr(self) -> bool:
        """Parse OR expression: and_expr ('or' and_expr)*"""
        left = self._and_expr()
        while self._current() == "or":
            self._advance()  # consume 'or'
            right = self._and_expr()
            left = left or right
        return left

    def _and_expr(self) -> bool:
        """Parse AND expression: not_expr ('and' not_expr)*"""
        left = self._not_expr()
        while self._current() == "and":
            self._advance()  # consume 'and'
            right = self._not_expr()
            left = left and right
        return left

    def _not_expr(self) -> bool:
        """Parse NOT expression: 'not' not_expr | comparison"""
        if self._current() == "not":
            self._advance()  # consume 'not'
            return not self._not_expr()
        return self._comparison()

    def _comparison(self) -> bool:
        """Parse comparison: primary (comp_op primary)?"""
        left = self._primary()

        comp_ops = (">=", "<=", ">", "<", "==", "!=")
        if self._current() in comp_ops:
            op = self._advance()
            right = self._primary()
            return self._apply_comparison(left, op, right)

        # If no comparison, treat as boolean
        return bool(left)

    def _apply_comparison(
        self, left: Any, op: str | None, right: Any
    ) -> bool:
        """Apply a comparison operator to two values."""
        if op == ">=":
            return bool(left >= right)
        if op == "<=":
            return bool(left <= right)
        if op == ">":
            return bool(left > right)
        if op == "<":
            return bool(left < right)
        if op == "==":
            return bool(left == right)
        if op == "!=":
            return bool(left != right)
        raise ConditionParseError(f"Unknown comparison operator: {op}")

    def _primary(self) -> Any:
        """Parse primary: field | number | '(' expression ')'"""
        token = self._current()

        if token is None:
            raise ConditionParseError("Unexpected end of expression")

        # Parenthesized expression
        if token == "(":
            self._advance()  # consume '('
            result = self._or_expr()
            if self._current() != ")":
                raise ConditionParseError("Expected closing parenthesis")
            self._advance()  # consume ')'
            return result

        # Number literal
        if token.isdigit():
            self._advance()
            return int(token)

        # Field reference
        if token in _VALID_FIELDS:
            self._advance()
            return getattr(self.analysis, token)

        raise ConditionParseError(f"Unexpected token: {token}")


class CustomStrategy:
    """Strategy implementation that evaluates configurable rules.

    Rules are evaluated in order for both Bet 1 and Bet 2 decisions.
    The first rule whose condition matches determines the action.
    A "default" condition can be used as a fallback.

    Attributes:
        bet1_rules: Rules for the 3-card (Bet 1) decision.
        bet2_rules: Rules for the 4-card (Bet 2) decision.
    """

    def __init__(
        self,
        bet1_rules: list[StrategyRule],
        bet2_rules: list[StrategyRule],
    ) -> None:
        """Initialize a custom strategy with rule lists.

        Args:
            bet1_rules: Rules for Bet 1 decisions (3-card hand).
            bet2_rules: Rules for Bet 2 decisions (4-card hand).

        Raises:
            ValueError: If rule lists are empty.
        """
        if not bet1_rules:
            raise ValueError("bet1_rules cannot be empty")
        if not bet2_rules:
            raise ValueError("bet2_rules cannot be empty")

        self.bet1_rules = bet1_rules
        self.bet2_rules = bet2_rules

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "CustomStrategy":
        """Create a CustomStrategy from a configuration dictionary.

        The configuration dictionary should have this structure:
            {
                "bet1_rules": [
                    {"condition": "has_paying_hand", "action": "ride"},
                    {"condition": "default", "action": "pull"},
                ],
                "bet2_rules": [
                    {"condition": "has_paying_hand", "action": "ride"},
                    {"condition": "default", "action": "pull"},
                ],
            }

        Args:
            config: Configuration dictionary with bet1_rules and bet2_rules.

        Returns:
            A configured CustomStrategy instance.

        Raises:
            ValueError: If configuration is invalid.
            KeyError: If required keys are missing.
        """
        bet1_rules = [
            StrategyRule(
                condition=rule["condition"],
                action=Decision(rule["action"]),
            )
            for rule in config["bet1_rules"]
        ]

        bet2_rules = [
            StrategyRule(
                condition=rule["condition"],
                action=Decision(rule["action"]),
            )
            for rule in config["bet2_rules"]
        ]

        return cls(bet1_rules=bet1_rules, bet2_rules=bet2_rules)

    def decide_bet1(
        self,
        analysis: HandAnalysis,
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        """Decide whether to pull or ride Bet 1 (3-card decision).

        Evaluates bet1_rules in order and returns the action of the
        first matching rule.

        Args:
            analysis: Analysis of the player's 3-card hand.
            context: Session context (not used by default, available for extension).

        Returns:
            Decision.RIDE or Decision.PULL based on first matching rule.

        Raises:
            ValueError: If no rule matches (should have a default rule).
        """
        return self._evaluate_rules(self.bet1_rules, analysis)

    def decide_bet2(
        self,
        analysis: HandAnalysis,
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        """Decide whether to pull or ride Bet 2 (4-card decision).

        Evaluates bet2_rules in order and returns the action of the
        first matching rule.

        Args:
            analysis: Analysis of the 4-card hand (3 player + 1 community).
            context: Session context (not used by default, available for extension).

        Returns:
            Decision.RIDE or Decision.PULL based on first matching rule.

        Raises:
            ValueError: If no rule matches (should have a default rule).
        """
        return self._evaluate_rules(self.bet2_rules, analysis)

    def _evaluate_rules(
        self, rules: list[StrategyRule], analysis: HandAnalysis
    ) -> Decision:
        """Evaluate a list of rules and return the first matching action.

        Args:
            rules: List of rules to evaluate in order.
            analysis: Hand analysis to evaluate against.

        Returns:
            The action from the first matching rule.

        Raises:
            ValueError: If no rule matches.
        """
        for rule in rules:
            if _evaluate_condition(rule.condition, analysis):
                return rule.action

        raise ValueError(
            "No rule matched. Consider adding a 'default' rule as fallback."
        )
