# Test Coverage Review: PR #79 - Progressive Betting Systems

## Summary

This PR implements 5 progressive betting systems (Martingale, Reverse Martingale, Paroli, D'Alembert, and Fibonacci) with comprehensive test coverage. The test suite is well-structured following the arrange-act-assert pattern with good coverage of initialization, progression logic, reset behavior, and protocol compliance. However, there are several missing edge cases and opportunities for more robust testing, particularly around boundary conditions and state consistency.

---

## Findings by Severity

### High Severity

#### H1: Missing validation test for base_bet < min_bet in D'Alembert
**File:** `tests/unit/bankroll/test_betting_systems.py`
**Lines:** Tests around line 1487-1491

The D'Alembert system accepts `base_bet` and `min_bet` parameters independently, but there is no validation or test for when `base_bet < min_bet`. This creates an inconsistent state where the initial bet is below the configured minimum.

**Current behavior:** If `base_bet=5.0` and `min_bet=10.0`, the system starts at bet 5 but can never go below 10 after a win. This is logically inconsistent.

**Recommendation:** Add validation in the implementation that `base_bet >= min_bet`, and add a corresponding test:
```python
def test_initialization_base_bet_less_than_min_bet_raises(self) -> None:
    """Verify base_bet < min_bet raises ValueError."""
    with pytest.raises(ValueError):
        DAlembertBetting(base_bet=5.0, min_bet=10.0)
```

#### H2: Missing negative bankroll test for all progressive systems
**File:** `tests/unit/bankroll/test_betting_systems.py`

While `MartingaleBetting` has a `test_zero_bankroll` test, the other systems (ReverseMartingale, Paroli, D'Alembert, Fibonacci) are missing explicit tests for negative bankroll scenarios. Although the implementations check for `bankroll <= 0`, this edge case should be explicitly tested.

**Affected systems:** ReverseMartingaleBetting, ParoliBetting, DAlembertBetting, FibonacciBetting

**Recommendation:** Add negative bankroll tests for each system:
```python
def test_negative_bankroll_returns_zero(self) -> None:
    """Verify negative bankroll returns zero bet."""
    betting = ReverseMartingaleBetting(base_bet=10.0)
    context = BettingContext(
        bankroll=-50.0,
        starting_bankroll=1000.0,
        session_profit=-1050.0,
        last_result=-10.0,
        streak=-5,
        hands_played=5,
    )
    assert betting.get_bet(context) == 0.0
```

### Medium Severity

#### M1: Inconsistent push handling across Martingale and Reverse Martingale
**File:** `src/let_it_ride/bankroll/betting_systems.py`
**Lines:** 203-205 (Martingale) vs 325-333 (ReverseMartingale)

Martingale treats push (result=0) as a win (resets progression), while ReverseMartingale and Paroli treat push as a loss (resets streak). While the tests document this behavior, the semantic inconsistency is not highlighted. Consider adding a test that explicitly documents and tests this design decision.

**Recommendation:** Add comparative behavior tests documenting the intentional difference:
```python
class TestPushBehaviorConsistency:
    """Tests documenting push handling across systems."""

    def test_martingale_treats_push_as_win(self) -> None:
        """Martingale resets on push (conservative approach)."""
        # ... test implementation

    def test_reverse_martingale_treats_push_as_loss(self) -> None:
        """ReverseMartingale resets on push (conservative for progression)."""
        # ... test implementation
```

#### M2: Missing floating-point precision tests
**File:** `tests/unit/bankroll/test_betting_systems.py`

No tests verify behavior with floating-point edge cases (very small bets, very large bets, or precision issues after many multiplications). The Martingale system with non-integer multipliers or base bets could accumulate floating-point errors.

**Recommendation:** Add floating-point precision tests:
```python
def test_non_integer_multiplier_precision(self) -> None:
    """Verify bet calculation with non-integer multiplier."""
    betting = MartingaleBetting(base_bet=10.0, loss_multiplier=1.5)
    context = BettingContext(bankroll=1000.0, ...)

    betting.record_result(-10.0)  # 15.0
    betting.record_result(-15.0)  # 22.5
    betting.record_result(-22.5)  # 33.75
    assert betting.get_bet(context) == pytest.approx(33.75)
```

#### M3: Missing test for max_position exceeding Fibonacci array bounds
**File:** `src/let_it_ride/bankroll/betting_systems.py`
**Line:** 630

The implementation caps `max_position` at `len(self._FIBONACCI) - 1`, which is correct. However, there is no test verifying this clamping behavior when a user requests a max_position larger than the pre-computed Fibonacci sequence.

**Recommendation:** Add test:
```python
def test_max_position_clamped_to_sequence_length(self) -> None:
    """Verify max_position is clamped to available Fibonacci numbers."""
    betting = FibonacciBetting(max_position=100)  # Exceeds 20 elements
    assert betting.max_position == 19  # len(_FIBONACCI) - 1
```

#### M4: Missing test for base_bet > max_bet validation in D'Alembert
**File:** `tests/unit/bankroll/test_betting_systems.py`

D'Alembert validates `min_bet > max_bet` but does not validate when `base_bet > max_bet`. This could create an inconsistent initial state.

**Recommendation:** Add validation test or update implementation to validate this constraint.

### Low Severity

#### L1: No property-based testing for bet progression invariants
**File:** `tests/unit/bankroll/test_betting_systems.py`

The test file does not use property-based testing (hypothesis library) to verify invariants like:
- Bet amount is always >= 0
- Bet amount never exceeds bankroll
- Bet amount never exceeds max_bet

**Recommendation:** Consider adding hypothesis tests for stronger coverage:
```python
from hypothesis import given, strategies as st

@given(
    bankroll=st.floats(min_value=0, max_value=10000),
    base_bet=st.floats(min_value=1, max_value=100),
)
def test_bet_never_exceeds_bankroll(bankroll: float, base_bet: float) -> None:
    """Verify bet never exceeds available bankroll."""
    betting = MartingaleBetting(base_bet=min(base_bet, 100))
    context = BettingContext(bankroll=bankroll, ...)
    assert betting.get_bet(context) <= max(bankroll, 0)
```

#### L2: Missing explicit test for hasattr protocol checks
**File:** `tests/unit/bankroll/test_betting_systems.py`
**Line:** 987-992

The `test_implements_betting_system` test uses `hasattr` checks, but this is a weak protocol compliance test. Consider using `isinstance` with `typing.runtime_checkable` or calling the methods to verify they work correctly.

**Recommendation:** The existing `test_can_be_used_as_betting_system` tests are good; consider removing or enhancing the `hasattr`-based tests.

#### L3: No test for very long loss/win sequences
**File:** `tests/unit/bankroll/test_betting_systems.py`

Tests do not verify system stability after many consecutive operations (e.g., 100+ losses followed by a win). While the max_progressions/max_position caps should handle this, explicit stress tests would increase confidence.

**Recommendation:** Add a stress test:
```python
def test_martingale_stable_after_many_losses(self) -> None:
    """Verify system is stable after many consecutive losses."""
    betting = MartingaleBetting(base_bet=10.0, max_progressions=5)
    context = BettingContext(bankroll=100000.0, ...)

    for _ in range(100):
        betting.record_result(-betting.get_bet(context))

    # Should be capped and stable
    assert betting.current_progression == 4  # max_progressions - 1
```

---

## Missing Test Scenarios

### Critical Gaps

1. **No zero/negative bankroll tests for 4 of 5 systems** (see H2)
2. **No validation for base_bet < min_bet in D'Alembert** (see H1)

### Important Gaps

1. **No test for Fibonacci with max_position > array length** (see M3)
2. **No floating-point precision verification** (see M2)
3. **No property-based tests for invariants** (see L1)

### Nice-to-Have

1. Concurrency/thread-safety tests (if systems will be used in parallel simulation)
2. Serialization/deserialization tests for system state
3. Performance benchmarks for rapid bet calculations

---

## Recommendations

### Immediate Actions (Pre-Merge)

1. Add negative bankroll tests for ReverseMartingale, Paroli, D'Alembert, and Fibonacci
2. Add validation that `base_bet >= min_bet` in D'Alembert implementation
3. Add test for max_position clamping in Fibonacci

### Post-Merge Improvements

1. Add hypothesis-based property tests for bet invariants
2. Add stress tests for long sequences of wins/losses
3. Consider adding floating-point precision tests with pytest.approx

---

## Coverage Summary

| System | Init Tests | Progression Tests | Reset Tests | Edge Cases | Protocol |
|--------|-----------|-------------------|-------------|------------|----------|
| MartingaleBetting | Good | Good | Good | Good | Good |
| ReverseMartingaleBetting | Good | Good | Good | Missing bankroll | Good |
| ParoliBetting | Good | Good | Good | Missing bankroll | Good |
| DAlembertBetting | Good | Good | Good | Missing base<min | Good |
| FibonacciBetting | Good | Good | Good | Missing max_pos clamp | Good |

**Overall Assessment:** Good test coverage with solid structure. A few edge cases should be addressed before merge to ensure production robustness.
