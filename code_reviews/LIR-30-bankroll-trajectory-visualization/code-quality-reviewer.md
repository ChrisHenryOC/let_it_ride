# Code Review: LIR-30 Bankroll Trajectory Visualization

**Reviewer:** Code Quality Reviewer
**PR:** #127
**Date:** 2025-12-13
**Files Reviewed:**
- `src/let_it_ride/analytics/visualizations/trajectory.py` (new, ~314 lines)
- `src/let_it_ride/analytics/visualizations/__init__.py` (modified)
- `src/let_it_ride/analytics/__init__.py` (modified)
- `tests/integration/test_visualizations.py` (modified, ~520 lines added)

## Summary

The LIR-30 implementation is well-structured and follows the established patterns from `histogram.py` closely. The code demonstrates good separation of concerns, proper type annotations, and comprehensive error handling. The test suite is thorough with excellent coverage of edge cases. Two medium-priority issues should be addressed: global RNG state mutation and missing validation for empty history lists.

---

## Findings by Severity

### Medium

#### 1. Global RNG State Mutation in `_sample_sessions`
**File:** `src/let_it_ride/analytics/visualizations/trajectory.py`
**Lines:** 89-95 (diff position ~90)

```python
if random_seed is not None:
    random.seed(random_seed)

indices = random.sample(range(len(results)), n_samples)
```

**Issue:** The function mutates global random state by calling `random.seed()`, which can affect other parts of the application that rely on the global random module. This violates the principle of least surprise and can cause subtle bugs in concurrent or test environments. This is particularly concerning given the project's emphasis on controlled RNG via `RNGManager`.

**Recommendation:** Use a local `random.Random` instance to avoid global state mutation:

```python
def _sample_sessions(
    results: list[SessionResult],
    histories: list[list[float]],
    n_samples: int,
    random_seed: int | None,
) -> tuple[list[SessionResult], list[list[float]]]:
    if len(results) <= n_samples:
        return results, histories

    rng = random.Random(random_seed)  # Local RNG instance
    indices = rng.sample(range(len(results)), n_samples)
    sampled_results = [results[i] for i in indices]
    sampled_histories = [histories[i] for i in indices]
    return sampled_results, sampled_histories
```

This approach:
- Avoids polluting global state
- Makes the function deterministic when seed is provided
- Is consistent with the project's `RNGManager` philosophy of controlled randomness

---

#### 2. Missing Validation for Empty Bankroll Histories
**File:** `src/let_it_ride/analytics/visualizations/trajectory.py`
**Lines:** 132-139 (diff position ~135)

**Issue:** The function validates that `results` and `bankroll_histories` have the same length, but does not validate that individual history lists are non-empty. An empty history list `[]` would result in a plot with only the starting bankroll point, which may be confusing or indicate a data integrity issue.

**Recommendation:** Add validation for empty histories or document that empty histories are acceptable:

```python
if not results:
    raise ValueError("Cannot create trajectory chart from empty results list")

if len(results) != len(bankroll_histories):
    raise ValueError(
        f"Results and histories must have same length. "
        f"Got {len(results)} results and {len(bankroll_histories)} histories."
    )

# Add validation for empty histories:
if any(len(h) == 0 for h in bankroll_histories):
    raise ValueError("Bankroll histories cannot contain empty lists")
```

---

### Low

#### 3. Assumption About Uniform Starting Bankroll Not Enforced
**File:** `src/let_it_ride/analytics/visualizations/trajectory.py`
**Lines:** 149-150 (diff position ~152)

```python
# Get starting bankroll from first session (assume all have same starting bankroll)
starting_bankroll = sampled_results[0].starting_bankroll
```

**Issue:** The comment acknowledges an assumption that all sessions have the same starting bankroll. If this assumption is violated, the baseline line and limit calculations would be incorrect for some sessions, potentially misleading users.

**Recommendation:** Either:
1. Add validation to enforce this assumption:
   ```python
   starting_bankrolls = {r.starting_bankroll for r in sampled_results}
   if len(starting_bankrolls) > 1:
       raise ValueError(
           f"All sessions must have same starting bankroll. Found: {starting_bankrolls}"
       )
   ```
2. Or add the requirement to the function's docstring under Args or Raises.

---

#### 4. Missing Test for Truly Empty History List
**File:** `tests/integration/test_visualizations.py`

**Issue:** The test `test_empty_history_entries` tests single-entry histories `[550.0]`, which is valid. However, there is no test for truly empty histories `[]` to verify the expected behavior (either raise an error or handle gracefully).

**Recommendation:** Add a test case to document and verify the expected behavior for empty history lists.

---

## Positive Observations

### Excellent Consistency with Existing Patterns
The implementation closely mirrors `histogram.py` in structure:
- Matching dataclass configuration pattern with `slots=True`
- Consistent color palette constants at module level
- Similar function signatures and parameter ordering
- Identical file-saving pattern with try/finally for resource cleanup

### Comprehensive Type Annotations
All function signatures have complete type hints including:
- Return types on all functions
- Union types using modern `|` syntax
- Proper `Literal` type for output format
- Type hints on dataclass fields

### Robust Error Handling
- Empty results validation with clear error messages
- Length mismatch validation between results and histories
- Invalid format validation in `save_trajectory_chart`
- Proper use of `strict=True` in `zip()` calls

### Thorough Test Coverage
The test suite covers:
- Basic functionality (figure creation, saving)
- Configuration options (custom titles, DPI, figure size)
- Edge cases (single session, all wins, all losses)
- Sampling behavior (with seed, without seed, fewer than sample limit)
- File format validation (PNG magic bytes, SVG content)
- Integration workflows (full workflow tests)

### Clean Code Structure
- Logical separation of private helper functions (`_get_outcome_color`, `_sample_sessions`)
- Clear docstrings with Args, Returns, and Raises sections
- Consistent naming conventions following snake_case
- Appropriate use of constants for colors (avoiding magic strings inline)

---

## Recommendations Summary

| Priority | Issue | File | Recommendation |
|----------|-------|------|----------------|
| Medium | Global RNG mutation | trajectory.py:89-95 | Use local `random.Random()` instance |
| Medium | Empty history validation | trajectory.py:132-139 | Add validation or document behavior |
| Low | Starting bankroll assumption | trajectory.py:149-150 | Add validation or document requirement |
| Low | Missing test case | test_visualizations.py | Add test for empty history list |

---

## Conclusion

The LIR-30 implementation is production-ready with minor improvements suggested. The code follows project conventions, has excellent test coverage, and demonstrates thoughtful design. The primary recommendation is to address the global RNG state mutation to improve thread safety and test isolation. The second medium-priority item (empty history validation) should be addressed to prevent potential confusion from malformed input data.
