# Security Code Review: PR #143 - LIR-58 Multi-Seat Stop Condition Behavior Options

## Summary

This PR adds "seat replacement mode" to `TableSession`, enabling seats that hit stop conditions to reset with fresh bankroll and continue playing until a table-wide round limit is reached. The implementation extends existing simulation logic with no new external inputs, network communication, file I/O, or user-facing interfaces. **No critical or high-severity security vulnerabilities were identified.** The code follows secure coding practices and maintains the same security posture as the existing codebase.

## Findings by Severity

### Critical Severity
None identified.

### High Severity
None identified.

### Medium Severity
None identified.

### Low Severity

#### L-01: Unbounded List Growth in Seat Replacement Mode
**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:159`

```python
self.completed_sessions: list[SeatSessionResult] = []
```

**Description:** In seat replacement mode, the `completed_sessions` list on each `_SeatState` grows unboundedly as seats cycle through sessions. With a very high `table_total_rounds` and stop conditions that trigger frequently (e.g., low `max_hands` or tight win/loss limits), this list could grow very large.

**Impact:** Potential memory exhaustion in extreme configurations. For example, with `table_total_rounds=1,000,000` and `max_hands=1`, each seat would accumulate 1 million `SeatSessionResult` objects.

**Remediation:** Consider adding validation in `TableSessionConfig.__post_init__` to limit the potential number of sessions, or document the expected maximum growth. The existing memory check in `FullConfig` (lines 1179-1186 of `models.py`) validates `num_sessions * num_seats` but does not account for seat replacement mode's multiplying effect.

**CWE Reference:** CWE-400 (Uncontrolled Resource Consumption)

#### L-02: Floating-Point Comparison for Financial Values
**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:302-307`

```python
if profit > 0:
    outcome = SessionOutcome.WIN
elif profit < 0:
    outcome = SessionOutcome.LOSS
else:
    outcome = SessionOutcome.PUSH
```

**Description:** The code uses direct floating-point comparisons for session profit, which is consistent with the existing codebase pattern. While unlikely to cause issues in typical scenarios, floating-point representation can introduce precision errors affecting comparisons.

**Impact:** A session profit that should be exactly 0.0 might be represented as a tiny positive or negative value, potentially causing incorrect outcome classification.

**Remediation:** Consider using a small epsilon tolerance for the zero comparison. This is a pre-existing pattern in the codebase and not introduced by this PR, but the new `_build_session_result_for_seat` method replicates it.

**CWE Reference:** CWE-1339 (Insufficient Precision or Accuracy of a Real Number)

### Informational

#### I-01: Input Validation for table_total_rounds Is Comprehensive
**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:79-81`

```python
if self.table_total_rounds is not None and self.table_total_rounds <= 0:
    raise ValueError("table_total_rounds must be positive if set")
```

**Positive Finding:** The new `table_total_rounds` configuration parameter is properly validated to reject zero or negative values. This prevents potential infinite loops or invalid state.

#### I-02: Use of assert Statements for Internal Invariants
**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:420`, `554`, `559`, `599`

**Description:** The code uses `assert` statements to verify internal invariants (e.g., `assert self._config.table_total_rounds is not None` after checking `seat_replacement_mode`). Assert statements can be disabled with Python's `-O` flag.

**Impact:** Minimal - these assertions verify conditions that are guaranteed by the code flow. For example, line 420 asserts `table_total_rounds is not None` immediately after confirming `seat_replacement_mode` (which checks the same condition).

**Remediation:** None required - these are defensive checks for internal logic, not external input validation.

#### I-03: Reset Method Preserves Completed Sessions
**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:186-201`

```python
def reset(self, current_round: int) -> None:
    """Reset seat state for a new player session.

    Clears all state and starts fresh with the original starting bankroll.
    Does NOT clear completed_sessions - that persists across resets.
    """
```

**Positive Finding:** The `reset()` method explicitly documents that `completed_sessions` is preserved, making the intentional behavior clear and reducing risk of accidental data loss or security-relevant state corruption.

## Security Practices Observed

### Positive Patterns

1. **Immutable Result Objects:** `SeatSessionResult`, `TableSessionResult`, and `SessionResult` use `frozen=True`, preventing accidental or malicious modification after creation.

2. **Slot-based Classes:** The `_SeatState` class uses `__slots__`, preventing arbitrary attribute injection and providing memory efficiency.

3. **No External Input Processing:** The new functionality operates entirely on programmatically-constructed objects with validated types. The `table_total_rounds` parameter is validated in `__post_init__`.

4. **No Dangerous Operations:** The changes do not introduce:
   - `eval()`, `exec()`, or `compile()`
   - `pickle` or other serialization
   - File I/O or subprocess calls
   - Network operations
   - Dynamic imports

5. **Bounded Iteration:** The `run_to_completion()` loop remains bounded. In seat replacement mode, it terminates when `_rounds_played >= table_total_rounds`. In classic mode, it terminates when all seats hit stop conditions.

6. **Backwards Compatibility:** When `table_total_rounds` is `None`, the code falls back to classic behavior, ensuring existing configurations are not affected.

7. **New Stop Reasons Are Non-Sensitive:** The new `StopReason.TABLE_ROUNDS_COMPLETE` and `StopReason.IN_PROGRESS` enum values are informational status indicators with no security implications.

## Conclusion

This PR extends the existing `TableSession` with a well-designed seat replacement feature. The implementation maintains the security posture of the existing codebase with appropriate input validation and no exposure to external attack vectors. The identified low-severity issue (unbounded list growth) is an edge case in extreme configurations and could be addressed with additional validation if needed.

**Recommendation:** Approve from a security perspective.
