# Security Review - PR #133: LIR-38 Risk of Ruin Calculator

## Summary

This PR introduces a risk of ruin calculator with Monte Carlo simulation capabilities and visualization support. The implementation demonstrates sound security practices overall with proper input validation, safe division handling, and immutable data structures. Two medium-severity findings relate to potential denial-of-service via unbounded resource consumption in simulation parameters. Low-severity findings include path handling patterns consistent with existing codebase conventions.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

**M1. Denial of Service - Unbounded `simulations_per_level` Parameter (CWE-400)**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 280, 297

The `calculate_risk_of_ruin` function accepts `simulations_per_level` as an integer with a default of 10,000 but no upper bound validation:

```python
def calculate_risk_of_ruin(
    session_results: Sequence[SessionResult],
    bankroll_units: Sequence[int] | None = None,
    base_bet: float | None = None,
    simulations_per_level: int = 10000,  # No upper bound validation
    ...
) -> RiskOfRuinReport:
```

Combined with the nested loop in `_run_monte_carlo_ruin_simulation` (lines 191-214) where each simulation iterates up to `max_sessions_per_sim=10000` times, a malicious or careless caller could specify extremely large values causing CPU exhaustion. With default bankroll_units of 5 levels, the total loop iterations could be:

- `simulations_per_level * max_sessions_per_sim * len(bankroll_units)`
- Example: 1,000,000 * 10,000 * 5 = 50 billion iterations

**Recommendation:** Add upper bound validation with a reasonable maximum:
```python
MAX_SIMULATIONS_PER_LEVEL = 100_000

if simulations_per_level <= 0:
    raise ValueError("simulations_per_level must be positive")
if simulations_per_level > MAX_SIMULATIONS_PER_LEVEL:
    raise ValueError(f"simulations_per_level exceeds maximum of {MAX_SIMULATIONS_PER_LEVEL}")
```

---

**M2. Denial of Service - Unbounded `bankroll_units` Sequence Length (CWE-400)**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 71-83, 278

The `_validate_bankroll_units` function validates that values are positive but does not limit sequence length:

```python
def _validate_bankroll_units(bankroll_units: Sequence[int]) -> None:
    if not bankroll_units:
        raise ValueError("bankroll_units must not be empty")
    if any(units <= 0 for units in bankroll_units):
        raise ValueError("All bankroll units must be positive integers")
    # No length validation
```

Since the main calculation loops over each bankroll level (line 346: `for units in sorted(bankroll_units):`), an extremely long sequence would cause linear resource consumption multiplied by the simulation count.

**Recommendation:** Add maximum length validation:
```python
MAX_BANKROLL_LEVELS = 100

if len(bankroll_units) > MAX_BANKROLL_LEVELS:
    raise ValueError(f"bankroll_units exceeds maximum of {MAX_BANKROLL_LEVELS} levels")
```

### Low

**L1. Directory Traversal - Unconstrained Path Creation (CWE-22)**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/visualizations/risk_curves.py`
Lines: 248-253

The `save_risk_curves` function creates parent directories without validating the path:

```python
path = Path(path)
if path.suffix.lower() != f".{output_format}":
    path = path.with_suffix(f".{output_format}")

# Creates arbitrary directory structure
path.parent.mkdir(parents=True, exist_ok=True)
```

This allows writing to arbitrary filesystem locations if untrusted paths are passed. However, this matches the existing pattern in `histogram.py` (line 242) and `trajectory.py` (line 312), and the application is a CLI tool where file paths are typically provided by trusted users.

**Recommendation:** This is acceptable given the CLI context and consistency with existing patterns. If the API is ever exposed to untrusted input, consider adding path validation or sandboxing.

---

**L2. Integer Overflow Potential for Extreme Bankroll Values (CWE-190)**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Line: 240

The bankroll calculation multiplies `base_bet` by `bankroll_units`:

```python
bankroll = base_bet * bankroll_units
```

Python handles arbitrary precision integers, but when used in NumPy floating-point operations (e.g., threshold comparisons at lines 188-189), extremely large values could cause precision loss. The existing validation for positive values partially mitigates this.

**Recommendation:** Consider adding a reasonable upper bound on individual `bankroll_units` values (e.g., 1,000,000 units) if this function may receive untrusted input.

---

**L3. Non-Cryptographic RNG for Statistical Simulation (CWE-330)**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Line: 340

```python
rng = np.random.default_rng(random_seed)
```

The Monte Carlo simulation uses NumPy's default PRNG which is not cryptographically secure. For a statistical simulation application, this is appropriate and expected behavior. The concern is only if the output is used for actual gambling decisions.

**Recommendation:** This is acceptable for statistical analysis purposes. The existing codebase uses this pattern consistently. No change required.

### Informational

**I1. Proper Division-by-Zero Protection**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Line: 327

```python
estimated_base = total_wagered / (total_hands * 3) if total_hands > 0 else 1.0
```

Good defensive coding practice to prevent division by zero when no hands were played.

---

**I2. Numerical Overflow Prevention**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/risk_of_ruin.py`
Lines: 155-157

```python
# Prevent overflow for very negative exponents
if exponent < -700:
    return 0.0
```

The analytical ruin probability formula includes protection against floating-point overflow in exponential calculations.

## Positive Security Observations

1. **Immutable Data Structures** - `RiskOfRuinResult` and `RiskOfRuinReport` use `@dataclass(frozen=True, slots=True)`, preventing accidental mutation of computed results.

2. **Comprehensive Input Validation** - Dedicated validation functions (`_validate_bankroll_units`, `_validate_session_results`, `_validate_confidence_level`) provide clear error messages and validate input bounds.

3. **Base Bet Validation** - Line 330-331 validates that `base_bet` is positive before proceeding with calculations.

4. **Format Allowlist** - The `save_risk_curves` function (line 241) validates output format against an explicit allowlist (`"png"`, `"svg"`), preventing format injection.

5. **Proper Resource Cleanup** - The visualization code uses `try/finally` to ensure matplotlib figures are closed (lines 256-260), preventing memory leaks.

6. **Safe Path Handling** - Uses `pathlib.Path` for path operations rather than string manipulation, reducing path injection risks.

7. **Type Safety** - Strong typing throughout with proper use of `TYPE_CHECKING` guards prevents type confusion vulnerabilities.

## Summary Table

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | 0 | - |
| High | 0 | - |
| Medium | 2 | Resource exhaustion via unbounded simulation parameters |
| Low | 3 | Path handling, integer overflow potential, RNG considerations |
| Informational | 2 | Positive defensive coding practices |

## Recommendation

**Approve with minor suggestions.** This PR is safe to merge from a security perspective. The medium-severity findings around resource exhaustion (M1, M2) are worth addressing if the API may receive untrusted input, but they do not block merge for a CLI application where parameters are typically user-controlled. The implementation follows established codebase patterns and demonstrates good security practices overall.
