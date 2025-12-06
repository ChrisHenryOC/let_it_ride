# Security Code Review: PR #96 - LIR-20 Simulation Controller (Sequential)

**Reviewer:** Security Code Reviewer
**Date:** 2025-12-06
**PR:** #96 - feat: LIR-20 Simulation Controller (Sequential)
**Files Changed:** 4 (+919 lines)

---

## Summary

This PR introduces the `SimulationController` class for orchestrating sequential multi-session poker simulations. The code is well-structured with proper input validation through Pydantic models. The security posture is **good** - no critical or high-severity vulnerabilities were identified. The existing codebase uses a safe custom expression parser for strategy conditions (avoiding `eval()`), and this PR properly leverages that infrastructure.

---

## Findings

### LOW: Potential DoS via Large Session Count

**Location:** `src/let_it_ride/simulation/controller.py` lines 460-470 (run loop)

**Description:** The `SimulationController.run()` method iterates over `num_sessions` without internal resource checks. While the configuration models (`SimulationConfig`) limit `num_sessions` to 100,000,000 (100M), running this many sessions sequentially could consume significant CPU time.

**Impact:** Resource exhaustion on the server if exposed to untrusted configuration input.

**Remediation:** This is mitigated by:
1. Pydantic validation limits `num_sessions` to 100M max (config/models.py line 48)
2. The controller is not directly exposed to external input
3. Progress callback allows monitoring

**Status:** Acceptable risk for current use case.

---

### LOW: Unseeded RNG May Be Less Predictable Than Expected

**Location:** `src/let_it_ride/simulation/controller.py` lines 455-458

```python
if self._base_seed is not None:
    master_rng = random.Random(self._base_seed)
else:
    master_rng = random.Random()
```

**Description:** When no seed is provided, `random.Random()` uses system entropy. This is appropriate for simulation purposes but worth documenting. The standard library `random` module is **not cryptographically secure** and should not be used for any security-sensitive randomness.

**Impact:** None for poker simulation. Would be a concern if this were gambling software handling real money.

**Remediation:**
- The code correctly uses `random.Random` for simulation purposes
- Consider adding documentation noting this is for simulation only
- The config already supports `shuffle_algorithm: cryptographic` for enhanced randomness

**Status:** Informational only.

---

### INFORMATIONAL: Custom Strategy Expression Handling

**Location:** `src/let_it_ride/simulation/controller.py` lines 263-285

**Description:** The `create_strategy()` function handles custom strategies by converting configuration rules to `StrategyRule` instances. I reviewed the underlying `CustomStrategy` implementation in `src/let_it_ride/strategy/custom.py` and confirmed it uses a **safe recursive descent parser** - NOT `eval()` or `exec()`.

The condition expressions are:
1. Tokenized with strict regex patterns (lines 50-55 of custom.py)
2. Validated against a whitelist of allowed field names (`_VALID_FIELDS`)
3. Parsed via `_ExpressionParser` which only allows: identifiers, numbers, comparisons, and boolean operators

**Positive Security Practices Observed:**
- Explicit rejection of unknown fields: `InvalidFieldError`
- No use of `eval()`, `exec()`, or `compile()` on user input
- Frozen dataclass for `StrategyRule` prevents mutation
- Pre-tokenization at rule creation time (fail-fast validation)

**Status:** No vulnerability - good security design.

---

### INFORMATIONAL: Input Validation via Pydantic

**Location:** All configuration handling

**Description:** The PR leverages existing Pydantic models with comprehensive validation:
- `FullConfig` with `extra="forbid"` prevents unknown fields
- Numeric ranges enforced via `Field(ge=..., le=...)`
- Literal types for enums prevent arbitrary string injection
- Model validators for cross-field validation

**Status:** No vulnerability - proper defense in depth.

---

### INFORMATIONAL: No File System Operations

**Description:** The `SimulationController` does not perform any file I/O, path operations, or external command execution. Results are returned as dataclass instances, leaving persistence to higher-level code.

**Status:** No vulnerability.

---

### INFORMATIONAL: No Network Operations

**Description:** The controller operates purely in-memory with no network calls, API requests, or external data fetching.

**Status:** No vulnerability.

---

### INFORMATIONAL: No Pickle/Deserialization

**Description:** The code does not use `pickle`, `marshal`, or any unsafe deserialization patterns. Data structures are built from validated Pydantic models.

**Status:** No vulnerability.

---

## Recommendations

1. **Documentation**: Consider adding a note in CLAUDE.md or docstrings that this simulator is for analysis purposes only and should not be used for real-money gambling without additional security review.

2. **Progress Callback Trust**: The `progress_callback` is called with trusted integer values. If this callback were ever to write to external systems, ensure the callback implementation validates inputs appropriately.

3. **Future Parallel Implementation**: When implementing parallel simulation (multi-worker), ensure proper isolation between worker processes and consider potential race conditions in shared state.

---

## Test Coverage Observations

The integration tests in `tests/integration/test_controller.py` include:
- Reproducibility tests (same seed = same results)
- Session isolation tests
- Stop condition boundary tests
- Multiple strategy type tests

**Recommendation:** Consider adding a test that explicitly verifies custom strategy conditions with potentially malicious-looking input (e.g., conditions with SQL-like syntax, shell metacharacters) to document the parser's rejection behavior.

---

## Conclusion

**Security Assessment: PASS**

No critical, high, or medium severity vulnerabilities were identified. The implementation follows secure coding practices with proper input validation through Pydantic models and safe expression parsing for custom strategies. The code is suitable for merge from a security perspective.

---

## Files Reviewed

| File | Lines Changed | Security Relevance |
|------|---------------|-------------------|
| `src/let_it_ride/simulation/controller.py` | +395 | Core implementation - reviewed |
| `src/let_it_ride/simulation/__init__.py` | +19 | Module exports - reviewed |
| `tests/integration/test_controller.py` | +408 | Test coverage - reviewed |
| `scratchpads/issue-23-simulation-controller.md` | +104 | Documentation only |

---

## References

- CWE-94: Improper Control of Generation of Code ('Code Injection') - **Not applicable** - no `eval()` usage
- CWE-400: Uncontrolled Resource Consumption - **Low risk** - mitigated by config limits
- CWE-338: Use of Cryptographically Weak PRNG - **Informational** - appropriate for simulation
