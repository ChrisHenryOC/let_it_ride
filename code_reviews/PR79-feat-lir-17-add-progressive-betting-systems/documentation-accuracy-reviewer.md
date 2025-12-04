# Documentation Accuracy Review: PR #79 - Progressive Betting Systems

## Summary

This PR adds five progressive betting systems (Martingale, ReverseMartingale, Paroli, D'Alembert, Fibonacci) with comprehensive documentation. The documentation quality is excellent overall, with complete docstrings on all public APIs, accurate type hints, and thorough parameter descriptions. There are a few documentation inconsistencies worth addressing.

## Findings by Severity

### Medium Severity

#### 1. Inconsistent Push Handling Documentation Between Systems

**File:** `src/let_it_ride/bankroll/betting_systems.py`

The documentation for `record_result()` handles push (result = 0) inconsistently across betting systems:

- **MartingaleBetting (lines 194-202)**: Documents "Win or push - reset progression" - treats push as win
- **ReverseMartingaleBetting (lines 316-324)**: Documents "Loss or push - reset streak" - treats push as loss
- **ParoliBetting (lines 438-446)**: Documents "Loss or push - reset count" - treats push as loss
- **DAlembertBetting (lines 556-564)**: Documents "Push (result == 0) - no change" - treats push as neutral
- **FibonacciBetting (lines 679-687)**: Documents "Push (result == 0) - no change" - treats push as neutral

This inconsistency may confuse developers about expected behavior. While the implementation appears intentional (each system can have its own push semantics), the class-level docstrings do not explain these differences.

**Location:** Lines 105-110, 227-232, 349-354, 471-476, 587-592 (class docstrings)

**Recommendation:** Add a note to each class docstring clarifying the push behavior, e.g., "A push (result = 0) resets the progression" or "A push (result = 0) has no effect on position."

---

#### 2. ReverseMartingale and Paroli Class Docstrings Appear Nearly Identical

**File:** `src/let_it_ride/bankroll/betting_systems.py`

**ReverseMartingale (lines 227-232):**
```python
"""Reverse Martingale (Anti-Martingale/Parlay) betting system.

Increases bet after wins, resets to base bet after losses.
Optionally resets after reaching a profit target streak.
"""
```

**Paroli (lines 349-354):**
```python
"""Paroli betting system.

Increases bet after wins by a multiplier, resets to base bet after
a specified number of consecutive wins or any loss.
"""
```

The functional distinction between these two systems is subtle and could be clearer. Both increase bets after wins and reset after N wins. The Paroli docstring does not explain how it differs from Reverse Martingale.

**Recommendation:** Clarify the difference in the Paroli docstring, e.g., "Similar to Reverse Martingale but specifically designed for..." or explicitly state that they are functionally equivalent with different naming conventions from gambling literature.

---

### Low Severity

#### 3. FibonacciBetting Class Docstring Missing Sequence Description

**File:** `src/let_it_ride/bankroll/betting_systems.py`
**Location:** Lines 587-592

The class docstring states:
```python
"""Fibonacci betting system.

Follows the Fibonacci sequence on losses, regresses on wins.
Bet = base_unit * fibonacci[position].
"""
```

This does not indicate what the Fibonacci sequence values are. A developer unfamiliar with the sequence would benefit from seeing the first few values (1, 1, 2, 3, 5, 8, 13...).

**Recommendation:** Add the first several values of the sequence to the class docstring, or reference the `_FIBONACCI` class attribute.

---

#### 4. Missing Cross-Reference to BettingSystem Protocol

**File:** `src/let_it_ride/bankroll/betting_systems.py`

None of the five new betting system classes mention that they implement the `BettingSystem` protocol in their class docstrings. While the tests verify protocol compliance, the documentation should make this explicit.

**Recommendation:** Add a brief note like "Implements the BettingSystem protocol." to each class docstring.

---

#### 5. README Betting Systems Reference Could Be More Specific

**File:** `README.md`
**Location:** Line 10

The README mentions:
```
- **Bankroll Management**: Various betting progression systems (flat, Martingale, Paroli, etc.)
```

This PR adds D'Alembert and Fibonacci systems that are not mentioned. While "etc." covers them, the documentation could be more complete.

**Recommendation:** Consider updating to explicitly list all available systems, or use a more comprehensive phrase like "(flat, Martingale, Paroli, D'Alembert, Fibonacci, and more)".

---

#### 6. Scratchpad Implementation Plan Differs Slightly from Implementation

**File:** `scratchpads/issue-20-progressive-betting.md`

The scratchpad states for DAlembertBetting:
- **Parameters**: base_bet, unit (5.0), min_bet (5.0), max_bet (500)

However, the implementation does not include validation that `base_bet` falls within `min_bet` and `max_bet` bounds. This is not necessarily wrong, but the scratchpad does not clarify this edge case.

**Recommendation:** This is informational only. The scratchpad is not end-user documentation.

---

## Documentation Quality Highlights (Positive)

1. **Complete Parameter Documentation**: All `__init__` methods have comprehensive docstrings with Args, Raises, and default value documentation.

2. **Accurate Type Hints**: All method signatures include proper type hints matching the docstrings.

3. **Property Documentation**: All properties have docstrings describing what they return.

4. **Error Documentation**: ValueError exceptions are properly documented in Raises sections.

5. **Test Docstrings**: All test methods have descriptive docstrings explaining what they verify.

6. **Consistent Format**: Documentation follows a consistent style across all five betting systems.

---

## Recommendations Summary

| Priority | Issue | Action |
|----------|-------|--------|
| Medium | Inconsistent push handling docs | Add push behavior note to each class docstring |
| Medium | Paroli vs ReverseMartingale distinction unclear | Clarify distinction in Paroli docstring |
| Low | Fibonacci sequence not shown | Add first few sequence values to docstring |
| Low | No protocol reference in docstrings | Add "Implements BettingSystem protocol" note |
| Low | README incomplete betting systems list | Update README to list all systems |

---

## Conclusion

The documentation in this PR is of high quality. All public APIs are documented with accurate parameter types, return values, and exception conditions. The medium-severity issues relate to clarifying behavioral differences between systems, particularly around push handling, which could benefit users trying to understand the subtle differences between systems. The test documentation is comprehensive and clearly describes expected behaviors.
