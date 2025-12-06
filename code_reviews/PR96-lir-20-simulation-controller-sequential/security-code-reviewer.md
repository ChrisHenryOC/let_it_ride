# Security Code Review: PR #96 - LIR-20 Simulation Controller (Sequential)

**Reviewer:** Security Code Reviewer (Updated Review)
**Date:** 2025-12-06
**PR:** #96 - feat: LIR-20 Simulation Controller (Sequential)
**Files Changed:** Primary: `controller.py` (+433), `test_controller.py` (+408)

---

## Summary

This PR implements a `SimulationController` class for orchestrating sequential multi-session poker simulations. The security posture is **good** - no critical or high-severity vulnerabilities were identified. The code properly leverages Pydantic for input validation and uses a safe recursive descent parser for custom strategy expressions (avoiding `eval()` and `exec()`). Two low-severity findings and several informational observations are documented below.

---

## Findings by Severity

### Critical

*None identified.*

### High

*None identified.*

### Medium

*None identified.*

### Low

#### L1: Unseeded RNG Uses Non-Cryptographic PRNG

**Location:** `src/let_it_ride/simulation/controller.py` lines 306-310 (diff position ~327)

```python
if self._base_seed is not None:
    master_rng = random.Random(self._base_seed)
else:
    master_rng = random.Random()
```

**Description:** When no seed is provided, `random.Random()` uses the standard library's Mersenne Twister PRNG seeded from system entropy. This is **not cryptographically secure** and should not be used for security-sensitive randomness.

**Impact:** Low for this application. This is a simulation tool, not real-money gambling software. The non-cryptographic PRNG is acceptable for statistical simulation purposes.

**CWE Reference:** CWE-338 (Use of Cryptographically Weak PRNG)

**Remediation:**
- The current implementation is appropriate for simulation purposes
- Document in code comments that this is for simulation only
- The config already supports `shuffle_algorithm: cryptographic` for the deck, which is the more critical randomness source
- If this were to be used for real-money applications, the entire RNG strategy would need review

**Status:** Acceptable for current use case.

---

#### L2: Potential Resource Consumption with Maximum Session Count

**Location:** `src/let_it_ride/simulation/controller.py` - `run()` method loop

**Description:** The `SimulationController.run()` method iterates over `num_sessions` without internal timeout or cancellation checks. The Pydantic model allows up to 100,000,000 sessions.

**Impact:** If an attacker could supply configuration input, they could cause resource exhaustion. However:
1. Pydantic validation limits `num_sessions` to 100M max
2. The controller is not directly exposed to external input (CLI layer handles this)
3. Progress callback enables monitoring

**CWE Reference:** CWE-400 (Uncontrolled Resource Consumption)

**Remediation:** This is adequately mitigated by existing controls. Consider adding an optional cancellation mechanism for long-running simulations in future work.

**Status:** Acceptable risk.

---

### Informational

#### I1: Safe Expression Parser for Custom Strategies (Positive Finding)

**Location:** `src/let_it_ride/simulation/controller.py` lines 99-136 (`create_strategy`)

**Description:** The `create_strategy()` function handles custom strategies by converting configuration rules to `StrategyRule` instances. I verified that the underlying `CustomStrategy` implementation in `src/let_it_ride/strategy/custom.py` uses a **safe recursive descent parser** - NOT `eval()` or `exec()`.

**Security Controls Verified:**
- Condition expressions are tokenized with strict regex patterns (`_TOKEN_PATTERN`)
- Field names validated against a frozen whitelist (`_VALID_FIELDS`)
- Parser uses `_ExpressionParser` class with explicit grammar (only allows: identifiers, numbers, comparisons, boolean operators)
- `StrategyRule` is a frozen dataclass preventing post-creation mutation
- Pre-tokenization at rule creation time provides fail-fast validation
- Unknown fields rejected with `InvalidFieldError`

**No use of dangerous functions:** Confirmed no `eval()`, `exec()`, `compile()`, or `__import__` usage.

**Status:** Good security design.

---

#### I2: Pydantic Input Validation (Positive Finding)

**Description:** The PR properly leverages Pydantic models with comprehensive validation:
- `FullConfig` with `extra="forbid"` prevents unknown fields (injection mitigation)
- Numeric ranges enforced via `Field(ge=..., le=...)`
- `Literal` types for strategy/betting system types prevent arbitrary string injection
- Model validators provide cross-field validation

**Status:** Proper defense in depth.

---

#### I3: No Unsafe Operations

**Verified that the controller does NOT:**
- Perform file I/O or path operations (no path traversal risk)
- Execute shell commands or subprocess calls
- Make network requests
- Use `pickle`, `marshal`, or unsafe deserialization
- Use dynamic imports or `__import__`
- Access environment variables
- Write to logs with user-controlled data (no log injection)

**Status:** Clean attack surface.

---

#### I4: Progress Callback Trust Boundary

**Location:** `src/let_it_ride/simulation/controller.py` lines 343-344 (diff position ~205)

```python
if self._progress_callback is not None:
    self._progress_callback(session_id + 1, num_sessions)
```

**Description:** The progress callback is called with trusted integer values (session_id + 1, num_sessions). The callback is provided by the caller, so it operates within the same trust boundary.

**Consideration:** If the callback were to write to external systems (e.g., logging to a file or database), the callback implementation should validate inputs. However, this is the callback implementer's responsibility.

**Status:** No action required.

---

## Files Reviewed

| File | Lines Changed | Security Relevance |
|------|---------------|-------------------|
| `src/let_it_ride/simulation/controller.py` | +433 | Core implementation - fully reviewed |
| `src/let_it_ride/simulation/__init__.py` | +15 | Module exports only |
| `tests/integration/test_controller.py` | +408 | Test code - reviewed |
| `scratchpads/issue-23-simulation-controller.md` | +104 | Planning document - N/A |
| Review documents | +966 | Documentation - N/A |

---

## Specific Recommendations

### Priority 1: Documentation

Add a comment near the RNG initialization clarifying the security context:

```python
# Note: random.Random is used for simulation reproducibility.
# This is NOT cryptographically secure and should not be used
# for real-money gambling applications without security review.
```

### Priority 2: Future Work - Parallel Implementation

When implementing parallel simulation (LIR-21), ensure:
- Worker process isolation prevents shared state corruption
- No race conditions in result aggregation
- Consider worker timeout/cancellation mechanisms

### Priority 3: Test Coverage

Consider adding a security-focused test verifying that custom strategy conditions properly reject malicious-looking input:

```python
def test_custom_strategy_rejects_injection_attempts() -> None:
    """Verify expression parser rejects SQL-like and shell-like syntax."""
    malicious_conditions = [
        "'; DROP TABLE hands; --",
        "$(whoami)",
        "__import__('os').system('ls')",
        "eval('1+1')",
    ]
    for condition in malicious_conditions:
        with pytest.raises((InvalidFieldError, ConditionParseError)):
            StrategyRule(condition=condition, action=Decision.PULL)
```

---

## Conclusion

**Security Assessment: PASS**

No critical, high, or medium severity vulnerabilities were identified. The implementation follows secure coding practices:
- Proper input validation through Pydantic models
- Safe expression parsing without `eval()`
- No file system, network, or shell operations
- Appropriate use of PRNG for simulation purposes

The code is suitable for merge from a security perspective.

---

## References

| CWE | Description | Applicability |
|-----|-------------|---------------|
| CWE-94 | Code Injection | Not applicable - safe parser used |
| CWE-338 | Weak PRNG | Low - appropriate for simulation |
| CWE-400 | Resource Consumption | Low - mitigated by config limits |
| CWE-78 | OS Command Injection | Not applicable - no subprocess |
| CWE-22 | Path Traversal | Not applicable - no file ops |
