# Security Review - PR #78

## Summary

This PR adds dealer discard mechanics to the Let It Ride poker simulator through a new `DealerConfig` Pydantic model and corresponding `GameEngine` modifications. The changes are well-implemented from a security perspective, with proper input validation via Pydantic's type constraints and safe defaults that maintain backwards compatibility. No critical or high-severity security issues were identified.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

None identified.

### Low

#### L-01: No Upper Bound Validation for Combined Card Removal

**Location:** `src/let_it_ride/config/models.py:92` (DealerConfig)

**Description:** The `discard_cards` field allows values up to 10, and while this is validated individually, there is no cross-validation with the deck size to ensure the game remains playable. With a standard 52-card deck, the game requires at minimum 5 cards (3 player + 2 community). Discarding 10 cards leaves 42 cards available, which is sufficient, but this could become an issue if multi-deck support is removed or modified.

**Impact:** Currently low risk since the maximum discard (10 cards) still leaves sufficient cards in a 52-card deck. This is more of a defensive coding concern.

**Remediation:** Consider adding a note in the docstring or a cross-validator if future changes might affect deck sizes. The current implementation is acceptable for the existing use case.

**CWE Reference:** CWE-20: Improper Input Validation

---

### Informational

#### I-01: Discarded Cards Accessible for Validation (Positive Finding)

**Location:** `src/let_it_ride/core/game_engine.py:211-221`

**Description:** The `last_discarded_cards()` method properly returns a copy of the internal list rather than the list itself. This prevents external code from modifying internal state, which is a good defensive programming practice.

**Code:**
```python
def last_discarded_cards(self) -> list[Card]:
    """Return the cards discarded by the dealer in the last hand."""
    return self._last_discarded_cards.copy()
```

---

#### I-02: Safe Default Configuration

**Location:** `src/let_it_ride/config/models.py:91`

**Description:** The `discard_enabled` field defaults to `False`, ensuring backwards compatibility and requiring explicit opt-in for the new behavior. This follows the principle of safe defaults.

---

#### I-03: RNG Usage is Appropriate

**Location:** `src/let_it_ride/core/game_engine.py:133`

**Description:** The code uses the injected `random.Random` instance for shuffling, which allows for:
1. Reproducible results via seeding (important for testing and validation)
2. No direct use of the global random state
3. The shuffle occurs before discarding, maintaining proper randomization

For a simulation tool (not a real gambling application), using `random.Random` with Fisher-Yates is appropriate. The codebase also supports a "cryptographic" shuffle algorithm option for higher security needs.

---

## Recommendations

1. **Documentation Enhancement (Optional):** Consider adding a brief note in the `DealerConfig` docstring explaining that the maximum 10-card limit ensures sufficient cards remain for gameplay with a standard 52-card deck.

2. **Test Coverage Verification:** The test file `tests/unit/core/test_dealer_mechanics.py` includes comprehensive tests including:
   - Boundary value testing (1 and 10 cards)
   - Validation that discarded cards don't appear in player hands
   - Reproducibility with same RNG seed
   - Copy semantics for `last_discarded_cards()`

   All security-relevant behaviors are well-tested.

## Files Reviewed

| File | Status |
|------|--------|
| `src/let_it_ride/config/models.py` | Reviewed - No issues |
| `src/let_it_ride/core/game_engine.py` | Reviewed - No issues |
| `tests/unit/core/test_dealer_mechanics.py` | Reviewed - Good coverage |

## Security Checklist

- [x] Input validation present (Pydantic Field constraints)
- [x] No injection vulnerabilities
- [x] No unsafe deserialization
- [x] No hardcoded secrets
- [x] Safe defaults (discard_enabled=False)
- [x] Proper encapsulation (returns copy, not reference)
- [x] RNG appropriate for use case (simulation, not real gambling)
- [x] No path traversal risks
- [x] No command injection risks
- [x] No eval/exec usage

## Conclusion

This PR demonstrates good security practices for a simulation application. The use of Pydantic models ensures strong input validation, defaults are secure (requiring explicit opt-in), and internal state is properly encapsulated. No security changes are required for this PR to be merged.
