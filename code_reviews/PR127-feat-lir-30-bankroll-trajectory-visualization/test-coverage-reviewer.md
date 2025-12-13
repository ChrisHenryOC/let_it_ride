# Test Coverage Review - PR #127

## Summary

PR #127 adds comprehensive test coverage for the new bankroll trajectory visualization feature with 35+ test cases organized across 4 test classes. The tests cover primary functionality well, including figure creation, configuration options, file I/O, and sampling behavior. However, there are notable gaps in edge case coverage for input validation scenarios (empty histories, mismatched starting bankrolls) and the `show_limits=False` configuration path when limits are provided.

## Findings

### Critical

None

### High

None

### Medium

#### M1: Missing Test for Empty Bankroll History Lists

**File:** `tests/integration/test_visualizations.py`
**Context:** `TestTrajectoryIntegration` class (around line 1201)

The test `test_empty_history_entries` (line 1201) tests a single-entry history `[550.0]` but does not test a truly empty history list `[]`. The implementation at `trajectory.py:166-167` would handle this by creating:

```python
full_history = [starting_bankroll, *history]  # becomes [500.0] with empty history
x_values = list(range(len(full_history)))     # becomes [0]
```

This produces a single-point trajectory which may be semantically incorrect (a session with 0 hands should arguably be rejected). The current behavior is undefined and untested.

**Recommendation:** Add test case for `histories = [[]]` to verify expected behavior or add input validation.

---

#### M2: Missing Test for Different Starting Bankrolls Across Sessions

**File:** `tests/integration/test_visualizations.py`
**Context:** `TestPlotBankrollTrajectories` class

The implementation at `trajectory.py:149-150` extracts starting bankroll from only the first session:

```python
# Get starting bankroll from first session (assume all have same starting bankroll)
starting_bankroll = sampled_results[0].starting_bankroll
```

No test verifies behavior when sessions have different `starting_bankroll` values. If sessions have varying starting bankrolls (e.g., 500.0 and 1000.0), the baseline and limit reference lines would be incorrectly calculated for non-first sessions.

**Recommendation:** Add test that passes sessions with different starting bankrolls and verifies either:
- An error is raised, or
- The behavior is documented and the test captures it explicitly

---

#### M3: Missing Test for `show_limits=False` with Limits Provided

**File:** `tests/integration/test_visualizations.py`
**Context:** `TestPlotBankrollTrajectories` class (around line 764)

The test `test_custom_config` (line 764) sets `show_limits=False` but does not pass `win_limit` or `loss_limit` parameters. The implementation at `trajectory.py:202-223` has logic to conditionally add limit lines:

```python
if config.show_limits:
    if win_limit is not None:
        # Add win limit line...
```

There is no test verifying that when `show_limits=False` but limit values ARE provided, the reference lines are correctly suppressed.

**Recommendation:** Add test case:
```python
def test_limits_suppressed_when_show_limits_false(self, sample_trajectories):
    results, histories = sample_trajectories
    config = TrajectoryConfig(show_limits=False)
    fig = plot_bankroll_trajectories(
        results, histories, config=config,
        win_limit=100.0, loss_limit=100.0  # Provided but should not appear
    )
    ax = fig.axes[0]
    legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert not any("Win Limit" in t for t in legend_texts)
    assert not any("Loss Limit" in t for t in legend_texts)
```

---

### Low

#### L1: No Test for Sampling Without Seed (Non-Deterministic Path)

**File:** `tests/integration/test_visualizations.py`
**Location:** `TestPlotBankrollTrajectories` class

The test `test_sampling_with_seed` (line 871) tests deterministic sampling with a fixed seed. However, there is no explicit test for the `random_seed=None` path in `_sample_sessions` (trajectory.py:89-92) which exercises the non-deterministic code branch.

**Recommendation:** Add a test that runs sampling with `random_seed=None` and verifies the figure is created successfully, ensuring the branch at `trajectory.py:89` (`if random_seed is not None`) has coverage for both True and False.

---

#### L2: No Unit Test for `_get_outcome_color` Helper

**File:** `src/let_it_ride/analytics/visualizations/trajectory.py:53-66`

The internal helper function `_get_outcome_color` is only implicitly tested through integration tests. While acceptable for a simple helper, direct unit tests would provide faster feedback on color mapping changes.

**Recommendation:** Optional - add unit tests if the color scheme is likely to change:
```python
def test_get_outcome_color_mapping():
    assert _get_outcome_color(SessionOutcome.WIN) == "#2ecc71"
    assert _get_outcome_color(SessionOutcome.LOSS) == "#e74c3c"
    assert _get_outcome_color(SessionOutcome.PUSH) == "#95a5a6"
```

---

#### L3: Missing Test for Large Session Count Annotation Formatting

**File:** `tests/integration/test_visualizations.py`

The annotation at `trajectory.py:232` formats total sessions with comma separator:
```python
annotation_text = f"Showing {displayed} of {total_sessions:,} sessions\n"
```

No test verifies comma formatting works correctly for large numbers (e.g., 1,000,000 sessions showing as "1,000,000"). The `large_trajectories` fixture only has 50 sessions.

**Recommendation:** Add test with 1000+ sessions to verify comma formatting in annotation text.

---

#### L4: Test Coverage for `all_losses` and `all_pushes` Trajectory Scenarios Missing

**File:** `tests/integration/test_visualizations.py`
**Location:** `TestTrajectoryIntegration` class

While `test_all_wins` (line 1170) tests behavior when all sessions are wins, there are no corresponding tests for `test_all_losses` or `test_all_pushes` trajectory scenarios. The histogram tests have these variations (lines 489, 517).

**Recommendation:** Add `test_all_losses` and `test_all_pushes` methods to `TestTrajectoryIntegration` for parity with histogram tests.

---

## Coverage Summary Table

| Aspect | Coverage Status | Notes |
|--------|-----------------|-------|
| Happy path (normal usage) | Well covered | 35+ test cases |
| Error handling (empty list, mismatched lengths) | Covered | Lines 732-743 |
| Configuration options | Mostly covered | Missing `show_limits=False` + limits combo |
| File I/O (PNG, SVG, directory creation) | Well covered | Lines 931-1050 |
| Edge cases (single session, uniform outcomes) | Partially covered | Missing all-losses, all-pushes, empty history |
| Input validation edge cases | **Gaps exist** | Different starting bankrolls, empty histories |
| Sampling behavior | Covered | Seeded and unseeded sampling |
| Performance/stress testing | Not covered | Acceptable for visualization code |

## Recommendations

### Priority 1 (Should Fix)

1. **Add test for empty history list `[[]]`** - This is an edge case that could cause confusing visualizations or hide data integrity issues. Either add validation to reject empty histories or add a test documenting the expected behavior.

2. **Add test for `show_limits=False` with limit values provided** - Ensures the configuration flag properly suppresses limit lines even when limit values are passed.

### Priority 2 (Should Consider)

3. **Add test for sessions with different starting bankrolls** - The current implementation silently uses only the first session's starting bankroll, which could produce misleading visualizations. Either add validation or test the current behavior explicitly.

4. **Add explicit test for non-seeded sampling** - Ensures the `random_seed=None` branch has coverage.

### Priority 3 (Nice to Have)

5. **Add `test_all_losses` and `test_all_pushes` to trajectory integration tests** - For consistency with histogram tests and complete outcome coverage.

6. **Add test for large session count formatting** - Verify comma formatting works for 1000+ sessions.

---

## Files Reviewed

| File | Lines Added | Test Ratio |
|------|-------------|------------|
| `src/let_it_ride/analytics/visualizations/trajectory.py` | 314 | N/A |
| `tests/integration/test_visualizations.py` (trajectory section) | ~610 | 1.94:1 |

The test-to-code ratio of approximately 2:1 is healthy for visualization code. The primary gaps are in edge case coverage rather than overall volume.
