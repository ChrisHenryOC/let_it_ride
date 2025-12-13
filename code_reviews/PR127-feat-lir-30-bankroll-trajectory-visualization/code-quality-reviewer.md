# Code Quality Review - PR #127

## Summary

PR #127 implements bankroll trajectory visualization (LIR-30) with a well-structured module that closely follows established patterns from `histogram.py`. The implementation demonstrates good separation of concerns, proper type annotations throughout, and comprehensive test coverage. The primary issue is global RNG state mutation in `_sample_sessions`, which should use a local `Random` instance to avoid side effects in concurrent environments or tests.

## Findings

### Critical

None

### High

None

### Medium

#### M1: Global RNG State Mutation in `_sample_sessions`

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:89-92`

```python
if random_seed is not None:
    random.seed(random_seed)

indices = random.sample(range(len(results)), n_samples)
```

**Issue:** The function mutates global random state by calling `random.seed()`. This violates encapsulation and can cause subtle bugs:
- In test environments where multiple tests run in sequence, prior test state can bleed through
- In concurrent contexts (if visualization is called from parallel workers), unpredictable behavior occurs
- This pattern contradicts the project's `RNGManager` philosophy of controlled, isolated randomness

**Recommendation:** Use a local `random.Random` instance:

```python
def _sample_sessions(
    results: list[SessionResult],
    histories: list[list[float]],
    n_samples: int,
    random_seed: int | None,
) -> tuple[list[SessionResult], list[list[float]]]:
    if len(results) <= n_samples:
        return results, histories

    rng = random.Random(random_seed)  # Local instance, no global mutation
    indices = rng.sample(range(len(results)), n_samples)
    sampled_results = [results[i] for i in indices]
    sampled_histories = [histories[i] for i in indices]
    return sampled_results, sampled_histories
```

---

#### M2: Missing Validation for Empty Bankroll Histories

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:132-139`

**Issue:** The function validates that `results` and `bankroll_histories` have matching lengths, but does not validate that individual history lists are non-empty. An empty history (`[]`) would create:

```python
full_history = [starting_bankroll, *[]]  # becomes [500.0]
x_values = list(range(1))                 # becomes [0]
```

This results in a single-point "trajectory" which is technically valid but may indicate malformed input data.

**Recommendation:** Add explicit validation or document the expected behavior:

```python
if any(len(h) == 0 for h in bankroll_histories):
    raise ValueError("Bankroll histories cannot contain empty lists")
```

Alternatively, add documentation clarifying that empty histories represent 0-hand sessions and will display as single points.

---

### Low

#### L1: Starting Bankroll Assumption Not Enforced

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:149-150`

```python
# Get starting bankroll from first session (assume all have same starting bankroll)
starting_bankroll = sampled_results[0].starting_bankroll
```

**Issue:** The code assumes all sessions share the same starting bankroll but does not validate this. If sessions have different starting bankrolls, the baseline and limit lines would be misleading for some trajectories.

**Recommendation:** Either validate the assumption:

```python
starting_bankrolls = {r.starting_bankroll for r in sampled_results}
if len(starting_bankrolls) > 1:
    raise ValueError(
        f"All sessions must have same starting bankroll for visualization. "
        f"Found: {starting_bankrolls}"
    )
starting_bankroll = sampled_results[0].starting_bankroll
```

Or document this requirement in the function's docstring under "Args" or "Raises".

---

#### L2: Test Coverage Gap for `show_limits=False` with Limits Provided

**File:** `tests/integration/test_visualizations.py:764-784`

**Issue:** The test `test_custom_config` sets `show_limits=False` but does not pass `win_limit` or `loss_limit`. There is no test verifying that when `show_limits=False` AND limit values ARE provided, the reference lines are correctly suppressed.

**Recommendation:** Add a test case:

```python
def test_limits_suppressed_when_disabled(
    self, sample_trajectories: tuple[list[SessionResult], list[list[float]]]
) -> None:
    """Test that limit lines are hidden when show_limits=False."""
    results, histories = sample_trajectories
    config = TrajectoryConfig(show_limits=False)
    fig = plot_bankroll_trajectories(
        results, histories, config=config,
        win_limit=100.0, loss_limit=100.0  # Provided but should be hidden
    )
    ax = fig.axes[0]
    legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert not any("Win Limit" in t for t in legend_texts)
    assert not any("Loss Limit" in t for t in legend_texts)
    matplotlib.pyplot.close(fig)
```

---

#### L3: Unused Import in Diff Context

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:22`

**Issue:** The constant `LIMIT_COLOR = "#3498db"` is defined but never used in the implementation. The win limit uses `PROFIT_COLOR` and loss limit uses `LOSS_COLOR`.

**Recommendation:** Either remove the unused constant or document it as reserved for future use. If the intention was to use it for limit lines, consider whether a distinct color would improve readability.

---

## Positive Observations

### Excellent Pattern Consistency
The implementation closely mirrors `histogram.py`:
- Same dataclass configuration pattern with `slots=True`
- Consistent color constant declarations at module level
- Matching function signature styles
- Identical file-saving pattern with `try/finally` cleanup

### Complete Type Annotations
All function signatures have proper type hints:
- Modern union syntax (`TrajectoryConfig | None`)
- `Literal` types for constrained parameters (`Literal["png", "svg"]`)
- Return types on all functions including helpers

### Robust Error Handling
- Empty results validation with descriptive error message
- Length mismatch validation between parallel data structures
- Invalid format validation in save function
- Proper `strict=True` in `zip()` calls prevents silent data misalignment

### Comprehensive Test Suite
The tests cover:
- Happy path functionality (figure creation, file saving)
- Configuration options (custom titles, DPI, figure size)
- Edge cases (single session, all wins, all losses)
- Sampling behavior (deterministic with seed, bounded by limit)
- File format validation (PNG magic bytes, SVG content)
- Directory creation

### Clean Separation of Concerns
- `_get_outcome_color`: isolated color mapping logic
- `_sample_sessions`: isolated sampling logic
- `plot_bankroll_trajectories`: pure visualization, returns figure
- `save_trajectory_chart`: I/O wrapper with cleanup

---

## Recommendations

| Priority | Issue | Location | Action |
|----------|-------|----------|--------|
| Medium | Global RNG mutation | trajectory.py:89-92 | Use local `random.Random(random_seed)` instance |
| Medium | Empty history validation | trajectory.py:132-139 | Add validation or document expected behavior |
| Low | Starting bankroll assumption | trajectory.py:149-150 | Add validation or document requirement |
| Low | Missing test case | test_visualizations.py | Add test for `show_limits=False` with limits provided |
| Low | Unused constant | trajectory.py:22 | Remove `LIMIT_COLOR` or document future use |

---

## Conclusion

The LIR-30 implementation is well-executed and production-ready. The code follows project conventions, demonstrates clean architecture, and has thorough test coverage. The primary recommendation is to fix the global RNG state mutation to ensure thread safety and test isolation. This aligns with the project's established `RNGManager` pattern for controlled randomness.

**Verdict:** Approve with minor changes (address M1 before merge).
