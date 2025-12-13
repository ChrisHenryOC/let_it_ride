# Security Review - PR #127

## Summary

This PR adds bankroll trajectory visualization for displaying line charts of session bankroll histories. The implementation follows secure patterns established in the existing `histogram.py` module and operates solely on internal simulation data structures without processing external user input. No critical or high-severity security vulnerabilities were identified. One low-severity issue related to global RNG state mutation was found.

## Findings

### Critical

None.

### High

None.

### Medium

None.

### Low

#### L-01: Global Random State Mutation

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py`
**Lines:** 89-92

**Description:**
The `_sample_sessions` function modifies the global `random` module state when a seed is provided:

```python
if random_seed is not None:
    random.seed(random_seed)

indices = random.sample(range(len(results)), n_samples)
```

**Security Impact:**
While not a direct security vulnerability, modifying global RNG state can cause unintended side effects if other parts of the application rely on the global random state. In a gambling simulator where reproducibility and RNG integrity are important, polluting global state could lead to:
- Non-reproducible results in concurrent/parallel visualization generation
- Potential interference with the main simulation RNG managed by `RNGManager`
- Test isolation issues where one test's RNG state affects another

This is particularly relevant given the project's emphasis on controlled RNG via `RNGManager` (documented in CLAUDE.md).

**CWE Reference:** CWE-330 (Use of Insufficiently Random Values) - tangentially related due to RNG state predictability concerns.

**Recommendation:**
Use a local `random.Random` instance to avoid polluting global state:

```python
def _sample_sessions(
    results: list[SessionResult],
    histories: list[list[float]],
    n_samples: int,
    random_seed: int | None,
) -> tuple[list[SessionResult], list[list[float]]]:
    if len(results) <= n_samples:
        return results, histories

    rng = random.Random(random_seed)  # Local instance - does not affect global state
    indices = rng.sample(range(len(results)), n_samples)
    sampled_results = [results[i] for i in indices]
    sampled_histories = [histories[i] for i in indices]
    return sampled_results, sampled_histories
```

This approach:
- Avoids polluting global state
- Maintains determinism when seed is provided
- Is consistent with the project's `RNGManager` philosophy

---

## Positive Security Observations

The following security-positive practices were observed in this PR:

### 1. Input Validation (trajectory.py:132-139)
The code properly validates input data, raising `ValueError` for empty results and mismatched list lengths before processing:
```python
if not results:
    raise ValueError("Cannot create trajectory chart from empty results list")

if len(results) != len(bankroll_histories):
    raise ValueError(...)
```

### 2. Safe Path Handling (trajectory.py:296-301)
Uses `pathlib.Path` for safe path manipulation rather than string concatenation:
```python
path = Path(path)
if path.suffix.lower() != f".{output_format}":
    path = path.with_suffix(f".{output_format}")

path.parent.mkdir(parents=True, exist_ok=True)
```

### 3. Output Format Allowlist (trajectory.py:289-290)
Output format is validated against an explicit allowlist before use:
```python
if output_format not in ("png", "svg"):
    raise ValueError(f"Invalid format '{output_format}'. Must be 'png' or 'svg'.")
```
This prevents unexpected file format injection.

### 4. Resource Cleanup (trajectory.py:311-314)
Uses try/finally to ensure matplotlib figures are closed even if saving fails, preventing resource leaks:
```python
try:
    fig.savefig(path, format=output_format, dpi=config.dpi, bbox_inches="tight")
finally:
    plt.close(fig)
```

### 5. No Dangerous Operations
The code does not use:
- `eval()`, `exec()`, or `compile()`
- `pickle` deserialization
- `subprocess` with shell=True
- Unsafe string formatting for SQL/commands

### 6. Type Safety
Complete type annotations throughout enable static analysis tools (mypy) to catch type-related issues.

### 7. Internal Data Only
The visualization functions operate only on internal `SessionResult` and `list[float]` data structures. There is no parsing of user-supplied strings, file content, or network data, which eliminates common injection attack vectors.

---

## File Path Considerations

**File:** `trajectory.py:296-301`

The `save_trajectory_chart` function creates directories and writes files based on a `Path` parameter. In the current usage context (internal simulation output), this is safe because:
- The path comes from the CLI or configuration, not from untrusted user input
- The application is a local command-line tool, not a web service

If this function were ever exposed to handle user-supplied paths in a web context, path traversal validation would be needed. The current internal-only usage is appropriate.

---

## Files Reviewed

| File | Status | Security Assessment |
|------|--------|---------------------|
| `src/let_it_ride/analytics/visualizations/trajectory.py` | NEW | One low-severity issue (global RNG) |
| `src/let_it_ride/analytics/visualizations/__init__.py` | MODIFIED | Export additions only - safe |
| `src/let_it_ride/analytics/__init__.py` | MODIFIED | Export additions only - safe |
| `src/let_it_ride/analytics/export_json.py` | MODIFIED | Formatting change only - safe |
| `tests/integration/test_visualizations.py` | MODIFIED | Test code - not security critical |
| `scratchpads/issue-33-bankroll-trajectory.md` | NEW | Documentation only |
| `code_reviews/LIR-30-*/*.md` | NEW | Review documentation only |

---

## Recommendations

1. **Address L-01 (Low Priority):** Replace the global `random.seed()` call with a local `random.Random()` instance to prevent global state pollution. This is a minor improvement that aligns with the project's RNG management philosophy.

2. **No other changes required:** The implementation demonstrates good security practices for a data visualization module.

---

## Conclusion

This PR introduces no significant security vulnerabilities. The code follows established secure patterns from the existing codebase, properly validates inputs, and handles resources safely. The single low-severity finding (global RNG state mutation) is a best-practice improvement rather than an exploitable vulnerability.

**Recommendation: APPROVE** from a security perspective.
