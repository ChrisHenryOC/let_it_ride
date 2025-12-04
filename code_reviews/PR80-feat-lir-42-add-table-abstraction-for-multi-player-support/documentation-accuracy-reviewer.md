# Documentation Accuracy Review: PR #80

**PR Title:** feat: LIR-42 Add Table abstraction for multi-player support
**Reviewer:** Documentation Accuracy Reviewer
**Date:** 2025-12-04

## Summary

This PR introduces a Table abstraction for multi-player support with comprehensive documentation. The code documentation is generally excellent, with complete docstrings for all public classes and methods. However, there is one notable documentation inaccuracy: the `DealerConfig` docstring in `models.py` (existing code, not changed in this PR) and the `TableRoundResult.dealer_discards` attribute documentation state that discards happen "before dealing" when the implementation now correctly performs discards **after** player cards are dealt, as part of dealing community cards.

## Findings by Severity

### Medium

#### 1. Inaccurate docstring for `TableRoundResult.dealer_discards` attribute
**File:** `src/let_it_ride/core/table.py`
**Lines:** 67 (diff line 343)

The docstring for `dealer_discards` states: "Cards discarded by dealer before dealing (None if disabled)."

However, per the updated dealing sequence documented in this PR's changes to `let_it_ride_requirements.md` and the actual implementation in `play_round()`, the dealer discard now happens **after** player cards are dealt (Step 3), not before. The docstring should say "Cards discarded by dealer when dealing community cards" or similar.

**Current:**
```python
dealer_discards: Cards discarded by dealer before dealing (None if disabled).
```

**Recommended:**
```python
dealer_discards: Cards discarded by dealer when dealing community cards (None if disabled).
```

#### 2. Pre-existing DealerConfig docstring is now outdated
**File:** `src/let_it_ride/config/models.py`
**Lines:** 77-86 (not in diff, but related)

The existing `DealerConfig` docstring states:
- "In some casino variations, the dealer takes cards and discards before dealing to players."
- Attribute descriptions: "Enable dealer discard before player deal" and "Number of cards dealer discards before player deal"

This is now inaccurate given the corrected dealing sequence where discards happen **after** player cards are dealt. While this file was not modified in this PR, the `TableConfig` addition creates a dependency, and the `DealerConfig` description should be updated for consistency with the new understanding of casino dealing mechanics.

**Note:** This is a pre-existing issue that should be addressed separately, not blocking this PR.

### Low

#### 3. Minor: Scratchpad file placement in version control
**File:** `scratchpads/issue-72-table-abstraction.md`
**Lines:** 99-193 (diff lines 99-193)

The scratchpad file is being committed to version control. Per CLAUDE.md, scratchpads are placed in `/scratchpads` and appear to be transient working documents. Consider whether this file should be in `.gitignore` or if it serves as useful implementation documentation that should remain.

**Recommendation:** If intended as permanent documentation, consider moving to `docs/` directory. If transient, add to `.gitignore`.

## Positive Observations

### Excellent Documentation Practices

1. **PlayerSeat dataclass (lines 303-334):** Complete attribute documentation with clear descriptions of all 12 fields, including edge case handling (e.g., "0 if not playing bonus", "None if no bonus bet").

2. **TableRoundResult dataclass (lines 337-351):** Clear, concise attribute documentation.

3. **Table class (lines 353-358):** Good class-level docstring explaining the purpose and shared resource model.

4. **Table.__init__ (lines 369-380):** All 7 parameters documented with clear descriptions, including default behavior notes.

5. **Table.play_round (lines 401-415):** Complete Args, Returns, and Raises sections documenting all parameters and error conditions.

6. **Table._process_seat (lines 491-503):** Internal method appropriately documented with Args and Returns.

7. **Table.last_discarded_cards (lines 564-569):** Clear documentation including edge cases (empty tuple when disabled).

8. **TableConfig (lines 202-217):** Follows project pattern with class docstring, Attributes section, and Pydantic Field annotations matching docs.

### Documentation Updates

The PR correctly updates multiple documentation files to reflect the corrected dealer discard timing:

- `docs/let_it_ride_implementation_plan.md`: Updated LIR-41 description and acceptance criteria
- `docs/let_it_ride_requirements.md`: Updated Section 2.5 (Dealer Card Handling), FR-806, and Section 5.3 configuration documentation

These updates ensure consistency between requirements documentation and implementation.

## Recommendations

1. **Update `TableRoundResult.dealer_discards` docstring** (Medium priority)
   - File: `src/let_it_ride/core/table.py:67`
   - Change "before dealing" to "when dealing community cards"

2. **Consider updating `DealerConfig` docstring** (Low priority, separate PR)
   - File: `src/let_it_ride/config/models.py:77-86`
   - Update to reflect post-player-deal discard timing

3. **README Update** (Low priority, not blocking)
   - The README does not mention multi-player or table features. Consider adding a bullet point under Features for multi-player table support after this PR merges.

## Test Documentation

The test file `tests/unit/core/test_table.py` includes excellent test docstrings that serve as documentation:

- Test class docstrings clearly describe test category purpose
- Individual test docstrings explain expected behavior
- Tests for deck usage include calculations as inline comments (e.g., "52 - 23 = 29 remaining")

## Conclusion

Documentation quality is high overall. The single medium-severity issue is a minor wording inconsistency in one attribute docstring. The pre-existing `DealerConfig` docstring issue should be tracked for a future cleanup PR.

**Recommendation:** Approve with suggestion to fix the `dealer_discards` attribute docstring wording.
