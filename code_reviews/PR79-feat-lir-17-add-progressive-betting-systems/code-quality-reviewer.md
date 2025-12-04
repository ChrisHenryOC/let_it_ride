# Code Quality Review: PR #79 - Progressive Betting Systems

## Summary

This PR implements five progressive betting systems (Martingale, Reverse Martingale, Paroli, D'Alembert, and Fibonacci) following the established `BettingSystem` protocol. The code is well-structured, follows the existing patterns in the codebase, and includes comprehensive tests. There are a few medium-severity issues related to code duplication and inconsistent edge case handling that should be addressed.

---

## Findings by Severity

### High

#### 1. Inconsistent Push Handling Across Systems

**Location:** `src/let_it_ride/bankroll/betting_systems.py`

**Issue:** The treatment of push (result == 0) is inconsistent across betting systems:

- **MartingaleBetting** (line 203): Treats push as a win (`if result >= 0`)
- **ReverseMartingaleBetting** (line 331-332): Treats push as a loss (`if result > 0: ... else:`)
- **ParoliBetting** (line 453-454): Treats push as a loss (`if result > 0: ... else:`)
- **DAlembertBetting** (line 565-571): No change on push (explicit handling)
- **FibonacciBetting** (line 688-694): No change on push (explicit handling)

**Impact:** This inconsistency could confuse users and lead to unexpected behavior. Martingale treating a push as a "win" and resetting progression seems counterintuitive compared to D'Alembert and Fibonacci which correctly preserve state on pushes.

**Recommendation:** Standardize push handling. Consider treating push as "no change" across all systems (like D'Alembert and Fibonacci do), or at minimum, document the behavior clearly in each class docstring.

**Diff position for MartingaleBetting record_result:** Line 203 (position = 203 - 99 = 104 in the diff)

---

### Medium

#### 2. Significant Code Duplication Across Classes

**Location:** `src/let_it_ride/bankroll/betting_systems.py` (lines 105-707)

**Issue:** All five betting system classes share nearly identical patterns:
- Same validation logic in `__init__` (checking positive values, multiplier > 1)
- Same bankroll check at start of `get_bet` (`if context.bankroll <= 0: return 0.0`)
- Same capping pattern (`bet = min(bet, self._max_bet); bet = min(bet, context.bankroll)`)
- Identical property getter patterns

**Impact:** Violates DRY principle. Any bug fix or enhancement needs to be applied to multiple classes.

**Recommendation:** Consider creating a base class or mixin that handles common functionality:

```python
class _ProgressiveBettingBase:
    """Base class for progressive betting systems with common functionality."""

    def _cap_bet(self, bet: float, context: BettingContext) -> float:
        """Apply max_bet and bankroll caps to calculated bet."""
        if context.bankroll <= 0:
            return 0.0
        bet = min(bet, self._max_bet)
        bet = min(bet, context.bankroll)
        return bet
```

This is a suggestion for future improvement; the current implementation is functional.

---

#### 3. Missing Validation: base_bet vs min_bet/max_bet Relationship

**Location:** `src/let_it_ride/bankroll/betting_systems.py`

**DAlembertBetting (lines 480-515):** No validation that `base_bet` is within the `[min_bet, max_bet]` range.

**Example:** A user could create:
```python
betting = DAlembertBetting(base_bet=100.0, min_bet=5.0, max_bet=50.0)
```

This would set `base_bet=100` but `max_bet=50`, meaning the initial bet would be clamped. While `get_bet()` handles this via bankroll capping, it could still confuse users.

**Recommendation:** Add validation in `__init__`:
```python
if base_bet > max_bet:
    raise ValueError("Base bet cannot exceed max bet")
if base_bet < min_bet:
    raise ValueError("Base bet cannot be less than min bet")
```

---

#### 4. FibonacciBetting - Inconsistent Parameter Naming

**Location:** `src/let_it_ride/bankroll/betting_systems.py`, line 599-605

**Issue:** `FibonacciBetting` uses `base_unit` instead of `base_bet`, which breaks the naming convention established by the other four systems. This could cause confusion when switching between betting systems or creating a factory.

**Recommendation:** Either rename to `base_bet` for consistency, or add documentation explaining why the naming differs (i.e., because Fibonacci uses units multiplied by sequence values rather than direct multipliers).

---

#### 5. ParoliBetting vs ReverseMartingaleBetting - Near Duplicate Functionality

**Location:** `src/let_it_ride/bankroll/betting_systems.py`

**Issue:** `ParoliBetting` and `ReverseMartingaleBetting` are functionally nearly identical:
- Both increase bet after wins using a multiplier
- Both reset after a specified number of consecutive wins
- Both reset after any loss

The only behavioral difference is the parameter names (`profit_target_streak` vs `wins_before_reset`). The implementations have the same logic.

**Impact:** Potential maintenance burden and user confusion about which to use.

**Recommendation:** Document the distinction clearly in the class docstrings, or consider if one should be an alias for the other. The Paroli system is traditionally just a specific variant of Reverse Martingale.

---

### Low

#### 6. Magic Number in Fibonacci Sequence

**Location:** `src/let_it_ride/bankroll/betting_systems.py`, line 597

```python
_FIBONACCI: tuple[int, ...] = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765)
```

**Issue:** The tuple contains 20 pre-computed values. The comment says "first 20 numbers should cover most needs" but doesn't explain why 20 was chosen.

**Recommendation:** Add a constant:
```python
_FIBONACCI_SIZE = 20
_FIBONACCI: tuple[int, ...] = (...)  # Pre-computed for performance (first 20 values)
```

---

#### 7. Minor - Consider Using `@property` with `@cached_property` for Fibonacci

**Location:** `src/let_it_ride/bankroll/betting_systems.py`, line 597

**Issue:** The Fibonacci sequence is defined as a class variable (tuple), which is efficient. However, if the sequence ever needed to be generated dynamically or extended, this approach would need refactoring.

**Recommendation:** Current implementation is fine for this use case. No change needed.

---

#### 8. Test File - Extensive BettingContext Boilerplate

**Location:** `tests/unit/bankroll/test_betting_systems.py`

**Issue:** Every test creates the same `BettingContext` with similar values. Consider using a pytest fixture to reduce boilerplate.

**Example from multiple tests:**
```python
context = BettingContext(
    bankroll=1000.0,
    starting_bankroll=1000.0,
    session_profit=0.0,
    last_result=None,
    streak=0,
    hands_played=0,
)
```

**Recommendation:** Add a fixture:
```python
@pytest.fixture
def default_context():
    return BettingContext(
        bankroll=1000.0,
        starting_bankroll=1000.0,
        session_profit=0.0,
        last_result=None,
        streak=0,
        hands_played=0,
    )
```

---

## Positive Aspects

1. **Excellent Protocol Compliance:** All five classes correctly implement the `BettingSystem` protocol with `get_bet()`, `record_result()`, and `reset()` methods.

2. **Proper Use of `__slots__`:** All classes use `__slots__` for memory efficiency, which aligns with the project's performance targets.

3. **Comprehensive Input Validation:** Each class validates inputs in `__init__` with clear error messages.

4. **Thorough Test Coverage:** The test file includes initialization tests, progression logic tests, edge case tests (max bet, bankroll limits), reset behavior, and protocol compliance tests for each system.

5. **Clean Property Accessors:** All internal state is exposed via read-only properties, maintaining encapsulation.

6. **Clear Docstrings:** Each class and method has clear, descriptive docstrings explaining behavior.

7. **Consistent Repr Implementation:** All classes provide meaningful `__repr__` output for debugging.

---

## Actionable Recommendations (Prioritized)

1. **[High]** Standardize push handling across all systems - decide whether push should be treated as win, loss, or no-change, and apply consistently.

2. **[Medium]** Add validation in `DAlembertBetting` to ensure `base_bet` is within `[min_bet, max_bet]` range.

3. **[Medium]** Document the distinction between `ParoliBetting` and `ReverseMartingaleBetting` in class docstrings.

4. **[Low]** Consider creating a pytest fixture for the common `BettingContext` to reduce test boilerplate.

5. **[Future]** Consider extracting common validation and capping logic into a base class to reduce duplication.

---

## Files Reviewed

| File | Lines Changed | Assessment |
|------|---------------|------------|
| `src/let_it_ride/bankroll/betting_systems.py` | +605 | Good structure, some inconsistencies |
| `src/let_it_ride/bankroll/__init__.py` | +10 | Clean exports |
| `tests/unit/bankroll/test_betting_systems.py` | +1357 | Comprehensive tests |
| `scratchpads/issue-20-progressive-betting.md` | +60 | Good planning document |

---

## Conclusion

This PR successfully implements five progressive betting systems that follow the established `BettingSystem` protocol. The code is well-tested and follows project conventions. The main concerns are the inconsistent push handling across systems and minor code duplication. Overall, this is a solid implementation that achieves the stated goals.

**Recommendation:** Approve with minor changes to standardize push handling.
