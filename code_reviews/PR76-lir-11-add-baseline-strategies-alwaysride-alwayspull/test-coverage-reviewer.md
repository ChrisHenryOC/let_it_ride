# Test Coverage Review: PR #76 - LIR-11 Add Baseline Strategies

## Summary

The test suite for the baseline strategies (`AlwaysRideStrategy` and `AlwaysPullStrategy`) is comprehensive and well-structured. It covers the core functionality with parameterized tests across multiple hand types, context independence verification, and protocol conformance checks. However, there are opportunities to improve coverage by reusing existing test fixtures, adding runtime protocol type-checking, and including additional edge case testing for bet 2 context independence.

## Findings by Severity

### Medium

#### 1. Duplicate Helper Functions Instead of Reusing Existing Fixtures
**File:** `tests/unit/strategy/test_baseline.py` (lines 194-228 in diff)
**Lines:** 194-228

The test file defines its own `make_card()` and `make_hand()` helper functions that are identical to those already defined in `tests/fixtures/hand_analysis_samples.py`. This duplicates code and creates maintenance burden.

**Current code:**
```python
def make_card(notation: str) -> Card:
    """Create a Card from notation like 'Ah' (Ace of Hearts)."""
    rank_map = {
        "2": Rank.TWO,
        # ... full mapping
    }
```

**Recommendation:** Import from existing fixtures:
```python
from tests.fixtures.hand_analysis_samples import make_card, make_hand
```

---

#### 2. Missing Context Independence Test for Bet 2 Decisions
**File:** `tests/unit/strategy/test_baseline.py` (lines 341-404 in diff)
**Lines:** 341-404

The `TestContextIndependence` class only tests `decide_bet1` for both strategies, but does not verify that `decide_bet2` also ignores context values. For complete coverage, both decision points should be tested with varying context.

**Recommendation:** Add parameterized tests for `decide_bet2` context independence:
```python
@pytest.mark.parametrize(
    "session_profit,hands_played,streak,bankroll",
    [
        (0.0, 0, 0, 1000.0),
        (500.0, 100, 5, 1500.0),
        (-500.0, 100, -5, 500.0),
        (0.0, 1000, 0, 10000.0),
    ],
)
def test_always_ride_bet2_ignores_context(
    self,
    always_ride_strategy: AlwaysRideStrategy,
    session_profit: float,
    hands_played: int,
    streak: int,
    bankroll: float,
) -> None:
    """Test that AlwaysRideStrategy.decide_bet2 returns RIDE regardless of context."""
    context = StrategyContext(
        session_profit=session_profit,
        hands_played=hands_played,
        streak=streak,
        bankroll=bankroll,
        deck_composition=None,
    )
    cards = make_hand("2c 7d Ks 4s")  # Weak 4-card hand
    analysis = analyze_four_cards(cards)

    result = always_ride_strategy.decide_bet2(analysis, context)
    assert result == Decision.RIDE
```

---

#### 3. Protocol Conformance Tests Use Runtime Attribute Checking Instead of isinstance
**File:** `tests/unit/strategy/test_baseline.py` (lines 407-436 in diff)
**Lines:** 407-436

The `TestStrategyProtocolConformance` class uses `hasattr` and `callable` checks rather than using Python's `typing.runtime_checkable` with `isinstance`. While the current approach works, using `isinstance` with a runtime-checkable Protocol is more idiomatic and comprehensive.

**Recommendation:** If the `Strategy` protocol is marked as `@runtime_checkable`, the tests could be simplified:
```python
from typing import runtime_checkable

def test_always_ride_is_strategy_instance(
    self, always_ride_strategy: AlwaysRideStrategy
) -> None:
    """Test that AlwaysRideStrategy is recognized as a Strategy instance."""
    from let_it_ride.strategy import Strategy
    assert isinstance(always_ride_strategy, Strategy)
```

Note: This requires adding `@runtime_checkable` decorator to the `Strategy` protocol in `base.py` if not already present.

---

### Low

#### 4. Limited Variety in Sample Hands for Parameterized Tests
**File:** `tests/unit/strategy/test_baseline.py` (lines 256-270 in diff)
**Lines:** 256-270

While the test uses 5 sample hands for each category, the existing `tests/fixtures/hand_analysis_samples.py` provides a much richer set of pre-defined hands covering more edge cases. Using these would improve coverage breadth.

**Current samples:**
```python
THREE_CARD_HANDS = [
    "Ah Kh Qh",  # Strong royal draw
    "2c 7d Ks",  # Weak garbage hand
    "Ts Ts 5c",  # Paying pair of tens
    "3h 4h 5h",  # Suited consecutive
    "9c 9d 9s",  # Trips
]
```

**Recommendation:** Import and use existing fixture samples:
```python
from tests.fixtures.hand_analysis_samples import (
    THREE_CARD_TRIPS_SAMPLES,
    THREE_CARD_HIGH_PAIR_SAMPLES,
    THREE_CARD_LOW_PAIR_SAMPLES,
    THREE_CARD_ROYAL_DRAW_SAMPLES,
    THREE_CARD_NO_DRAW_SAMPLES,
    # etc.
)
```

---

#### 5. No Test for deck_composition Context Field
**File:** `tests/unit/strategy/test_baseline.py` (lines 341-404 in diff)

The context independence tests always pass `deck_composition=None`. There is no test verifying the strategies also ignore a populated `deck_composition` field.

**Recommendation:** Add a test case with populated deck composition:
```python
def test_always_ride_ignores_deck_composition(
    self,
    always_ride_strategy: AlwaysRideStrategy,
) -> None:
    """Test that AlwaysRideStrategy ignores deck composition."""
    from let_it_ride.core.card import Rank

    context = StrategyContext(
        session_profit=0.0,
        hands_played=0,
        streak=0,
        bankroll=1000.0,
        deck_composition={Rank.ACE: 2, Rank.KING: 4},  # Non-None composition
    )
    cards = make_hand("2c 7d Ks")
    analysis = analyze_three_cards(cards)

    result = always_ride_strategy.decide_bet1(analysis, context)
    assert result == Decision.RIDE
```

---

## Specific Recommendations

| Priority | File | Line | Recommendation |
|----------|------|------|----------------|
| Medium | test_baseline.py | 194 | Reuse `make_card`/`make_hand` from `tests/fixtures/hand_analysis_samples.py` |
| Medium | test_baseline.py | 341-404 | Add `decide_bet2` context independence tests for both strategies |
| Medium | test_baseline.py | 407-436 | Consider using `isinstance` with `@runtime_checkable` Protocol |
| Low | test_baseline.py | 256-270 | Use existing hand sample fixtures for broader coverage |
| Low | test_baseline.py | 341-404 | Add test case with non-None `deck_composition` |

## Positive Observations

1. **Well-organized test structure**: The tests are logically grouped into classes by behavior (Bet1, Bet2, ContextIndependence, ProtocolConformance, ProtocolTyping).

2. **Good use of parameterization**: The `@pytest.mark.parametrize` decorator is used effectively to test multiple hand types without code duplication.

3. **Clear test naming**: Test method names clearly describe what is being tested (e.g., `test_always_returns_ride`, `test_always_pull_ignores_context`).

4. **Protocol typing tests**: The `TestStrategyProtocolTyping` class demonstrates that strategies can be used where the `Strategy` protocol is expected, which is valuable for type-safety verification.

5. **Comprehensive context variation**: Tests cover winning, losing, and neutral session states with varying bankrolls and streaks.

## Coverage Summary

| Aspect | Coverage | Notes |
|--------|----------|-------|
| Core functionality (decide_bet1/bet2) | Excellent | Both strategies tested with multiple hand types |
| Context independence | Good | Missing bet2 tests, missing deck_composition variation |
| Protocol conformance | Good | Could use isinstance with runtime_checkable |
| Edge cases | Adequate | Could leverage existing fixtures for more variety |
| Integration with existing fixtures | Missing | Duplicate helpers instead of reuse |
