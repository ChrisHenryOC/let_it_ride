# Security Code Review: PR #127 - LIR-30 Bankroll Trajectory Visualization

**Reviewer:** Security Code Reviewer
**Date:** 2025-12-13
**PR Title:** feat: LIR-30 Bankroll Trajectory Visualization
**Files Changed:** 5 files (1 new, 4 modified)

## Summary

This PR adds bankroll trajectory visualization functionality for displaying line charts of session bankroll histories. The implementation follows the same secure patterns established in the existing `histogram.py` module. **No critical or high-severity security vulnerabilities were identified.** The code operates on internal simulation data structures without external user input processing, significantly reducing the attack surface.

## Findings by Severity

### Critical

None identified.

### High

None identified.

### Medium

None identified.

### Low

#### L-01: Global Random State Modification

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py`
**Lines:** 243-244 (diff position 90-91 in trajectory.py hunk)

**Description:**
The `_sample_sessions` function modifies the global `random` module state when a seed is provided:

```python
if random_seed is not None:
    random.seed(random_seed)
```

**Impact:**
This could cause unintended side effects if other parts of the application rely on the global random state during or after trajectory plotting. While not a security vulnerability per se, unpredictable RNG state in a gambling simulator could lead to reproducibility issues in simulations running concurrently with visualization.

**Recommendation:**
Use a local `random.Random` instance to avoid polluting global state:

```python
rng = random.Random(random_seed) if random_seed is not None else random.Random()
indices = rng.sample(range(len(results)), n_samples)
```

This follows the principle of least surprise and prevents potential interference with the main simulation RNG managed by `RNGManager`.

---

### Informational

#### I-01: Positive Security Observations

The following security-positive practices were observed in this PR:

1. **Input Validation** (`trajectory.py:286-293`): The code properly validates input data, raising `ValueError` for empty results and mismatched list lengths before processing.

2. **Path Handling** (`trajectory.py:450-455`): Uses `pathlib.Path` for safe path manipulation rather than string concatenation. The `mkdir(parents=True, exist_ok=True)` pattern is used safely for directory creation.

3. **Format Validation** (`trajectory.py:443-444`): Output format is validated against an explicit allowlist (`"png"`, `"svg"`) before use, preventing unexpected file format injection.

4. **Resource Cleanup** (`trajectory.py:465-468`): Uses try/finally to ensure matplotlib figures are closed even if saving fails, preventing resource leaks.

5. **Type Safety**: Uses Python type hints throughout, enabling static analysis tools to catch type-related issues.

6. **No External Input Processing**: The visualization functions operate only on internal `SessionResult` and `list[float]` data structures. There is no parsing of user-supplied strings, file content, or network data, which eliminates common injection attack vectors.

7. **No Dangerous Operations**: The code does not use `eval()`, `exec()`, `pickle`, `subprocess`, or other potentially dangerous Python functions.

#### I-02: File Path Note

**File:** `trajectory.py:450-455`

The `save_trajectory_chart` function creates directories and writes files based on a `Path` parameter. In the current usage context (internal simulation output), this is safe. However, if this function were ever exposed to handle user-supplied paths in a web context, path traversal validation would be needed. The current internal-only usage is appropriate.

## Files Reviewed

| File | Status | Security Notes |
|------|--------|----------------|
| `src/let_it_ride/analytics/visualizations/trajectory.py` | NEW | Main implementation - no significant issues |
| `src/let_it_ride/analytics/visualizations/__init__.py` | MODIFIED | Export additions only - safe |
| `src/let_it_ride/analytics/__init__.py` | MODIFIED | Export additions only - safe |
| `src/let_it_ride/analytics/export_json.py` | MODIFIED | Formatting change only - safe |
| `tests/integration/test_visualizations.py` | MODIFIED | Test code - not security critical |

## Recommendations Summary

1. **Optional Improvement (L-01):** Consider using a local `random.Random` instance in `_sample_sessions` to avoid modifying global random state.

## Conclusion

This PR introduces no security vulnerabilities. The code follows established secure patterns from the existing codebase, properly validates inputs, and handles resources safely. The implementation is appropriate for a data visualization module operating on internal simulation data.

**Recommendation: APPROVE** from a security perspective.
