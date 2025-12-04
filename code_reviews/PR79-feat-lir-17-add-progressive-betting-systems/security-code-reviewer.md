# Security Code Review: PR #79 - Progressive Betting Systems

**Reviewer:** Security Code Reviewer
**PR:** #79 - feat: LIR-17 Add progressive betting systems
**Date:** 2025-12-04

## Summary

This PR adds five progressive betting systems (Martingale, ReverseMartingale, Paroli, D'Alembert, and Fibonacci) to the Let It Ride simulator. The implementation follows secure coding practices with proper input validation at initialization time and bounded state management. No critical or high severity security issues were identified. A few low-severity observations and recommendations are noted below.

## Security Analysis

### Attack Surface Assessment

The betting systems accept:
1. **Constructor parameters**: float and int values for configuration (base_bet, multipliers, max values)
2. **Runtime inputs**: BettingContext dataclass (bankroll state) and float results

The code does NOT:
- Accept external user input directly (YAML config loading is handled elsewhere)
- Perform file I/O, network operations, or subprocess calls
- Use `eval()`, `exec()`, `pickle`, or other dangerous Python constructs
- Access databases or external services

### Findings

---

#### Finding 1: Potential Float Overflow with Exponential Calculations [Low]

**Location:** `src/let_it_ride/bankroll/betting_systems.py`
- Line 186: `bet = self._base_bet * (self._loss_multiplier ** self._current_progression)` (MartingaleBetting)
- Line 308: `bet = self._base_bet * (self._win_multiplier ** self._win_streak)` (ReverseMartingaleBetting)
- Line 430: `bet = self._base_bet * (self._win_multiplier ** self._consecutive_wins)` (ParoliBetting)

**Description:**
While progressions and streaks are bounded, the exponential calculation could produce extremely large float values before the `min()` cap is applied. With Python floats (IEEE 754 double precision), values up to ~1.8e308 are supported, so overflow to `inf` is unlikely in practice given the bounded progressions.

**Impact:**
Minimal - the capping logic (`min(bet, self._max_bet)`) would still work correctly even with very large intermediate values. Python handles float overflow gracefully by returning `inf`, and `min(inf, 500.0)` correctly returns `500.0`.

**Recommendation:**
No code change required. The current safeguards are adequate. For defense-in-depth, the calculation order could be reversed to apply limits earlier, but this is optimization rather than security.

---

#### Finding 2: Input Validation is Properly Implemented [Positive]

**Location:** All betting system `__init__` methods

**Description:**
All five betting systems implement comprehensive input validation:
- `base_bet > 0` is enforced
- `max_bet > 0` is enforced
- Multipliers > 1 (where applicable)
- Minimum values for progressions/positions
- D'Alembert validates `min_bet <= max_bet`

This prevents invalid state that could cause unexpected behavior.

**Example:**
```python
if base_bet <= 0:
    raise ValueError("Base bet must be positive")
if loss_multiplier <= 1:
    raise ValueError("Loss multiplier must be greater than 1")
```

---

#### Finding 3: State Bounds are Properly Maintained [Positive]

**Location:** All `record_result()` methods

**Description:**
All progression/position state is properly bounded:
- MartingaleBetting: `min(progression + 1, max_progressions - 1)`
- ReverseMartingale/Paroli: Reset to 0 when target reached
- D'Alembert: `max(bet - unit, min_bet)` and `min(bet + unit, max_bet)`
- Fibonacci: `max(0, position - regression)` and `min(position + 1, max_position)`

This prevents unbounded state growth that could lead to resource exhaustion.

---

#### Finding 4: Fibonacci Position Bounds Protection [Positive]

**Location:** `src/let_it_ride/bankroll/betting_systems.py`, line 630

**Description:**
The Fibonacci implementation correctly bounds `max_position` to the pre-computed sequence length:
```python
self._max_position = min(max_position, len(self._FIBONACCI) - 1)
```

This prevents potential index-out-of-bounds access if a user specifies a `max_position` larger than the pre-computed sequence.

---

#### Finding 5: Missing Validation for base_bet < min_bet in D'Alembert [Low]

**Location:** `src/let_it_ride/bankroll/betting_systems.py`, `DAlembertBetting.__init__()` (lines 516-551)

**Description:**
The D'Alembert system allows `base_bet` to be less than `min_bet`. While functionally this works (the first win would clamp to `min_bet`), it could be considered semantically inconsistent:

```python
betting = DAlembertBetting(base_bet=3.0, min_bet=5.0, max_bet=500.0)
# base_bet=3.0 is less than min_bet=5.0
# First get_bet returns 3.0, first win sets current_bet to max(3-5, 5) = 5
```

**Impact:**
Minimal - the behavior is predictable and the clamping works correctly. This is more of a usability concern than a security issue.

**Recommendation:**
Consider adding validation: `if base_bet < min_bet: raise ValueError("Base bet cannot be less than min bet")`

---

#### Finding 6: No Thread Safety for Stateful Betting Systems [Low]

**Location:** All progressive betting system classes

**Description:**
The betting systems store mutable state (`_current_progression`, `_win_streak`, `_consecutive_wins`, `_position`, `_current_bet`) without synchronization primitives. If instances were shared across threads, race conditions could occur.

**Impact:**
Low - per the architecture in CLAUDE.md, `Session` manages a betting system instance, and `SimulationController` handles parallelization. Each session should have its own betting system instance. However, this is not enforced by the code itself.

**Recommendation:**
Document that betting system instances are NOT thread-safe and should not be shared across threads. This aligns with typical Python practices for mutable objects.

---

## Verification Checklist

| Security Control | Status |
|------------------|--------|
| Input validation on all constructor parameters | PASS |
| State bounds enforcement | PASS |
| No use of eval/exec/compile | PASS |
| No unsafe deserialization | PASS |
| No file/network operations | PASS |
| No SQL/NoSQL injection vectors | N/A |
| No command injection vectors | N/A |
| Bankroll-based bet capping | PASS |
| Zero/negative bankroll handling | PASS |

## Conclusion

The progressive betting systems implementation is **secure for its intended use case**. The code follows Python best practices:

1. Strong input validation at initialization
2. Bounded state management preventing resource exhaustion
3. Defensive programming with `min()` caps on calculated values
4. No use of dangerous Python constructs

No changes are required to merge this PR from a security perspective. The low-severity observations above are recommendations for future improvement.

## Files Reviewed

- `src/let_it_ride/bankroll/betting_systems.py` (lines 103-707 - new code)
- `src/let_it_ride/bankroll/__init__.py` (export additions)
- `tests/unit/bankroll/test_betting_systems.py` (test additions)
