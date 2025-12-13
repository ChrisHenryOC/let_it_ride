# Documentation Review: PR #130 - LIR-35 Performance Optimization and Benchmarking

## Summary

This PR adds a comprehensive performance benchmarking suite including throughput benchmarks, memory profiling, cProfile hotspot analysis, and performance documentation. The documentation is largely accurate and well-written, with thorough docstrings and helpful inline comments. However, there are a few documentation inconsistencies between the performance guide and actual code implementations, and one claim about `__slots__` usage is inaccurate.

## Findings by Severity

### High

No high severity documentation issues found.

### Medium

**1. Inaccurate `__slots__` claim for Table class**

File: `docs/performance.md` (lines 56-60 in diff, corresponding to lines 99-103 in doc)

The documentation states:
```markdown
### `__slots__`
Mutable session state classes use `__slots__` to reduce per-instance memory:
- `Session`
- `TableSession._SeatState`
- `Table`
```

However, the `Table` class at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/table.py` does NOT use `__slots__`. The class is defined as a regular class without `__slots__`:

```python
class Table:
    """Orchestrates multiple player positions at a Let It Ride table.
    ...
    """

    def __init__(
        self,
        ...
```

The `Session` class does have `__slots__` (verified at line 197 of session.py), and `TableSession._SeatState` also has `__slots__` (verified at line 130 of table_session.py), but `Table` does not. The documentation should either:
- Remove `Table` from this list, or
- Add `__slots__` to the `Table` class to match the documentation

**2. Hand evaluation target mismatch between benchmark code and documentation**

File: `benchmarks/__init__.py` (lines 12-13 in diff)

The package docstring states:
```python
"""Performance benchmarking suite for Let It Ride simulator.
...
Performance Targets:
- Hand evaluation: >500,000 hands/second
```

However, the scratchpad notes at `scratchpads/issue-38-performance-benchmarking.md` (lines 43-44) show:
```markdown
| Hand evaluation (5-card) | 324k/s | 332k/s | 500k/s | N/A |
```

The 5-card hand evaluation does NOT meet the 500k/s target (only achieves ~332k/s), yet this is documented as "N/A" status rather than "FAIL". The benchmark target documentation should clarify that this target applies specifically to the component benchmark, not the full simulation (which meets its 100k target), or acknowledge that 5-card evaluation falls short but the overall simulation target is met.

### Low

**1. Missing docstring for `line_profiler` in usage instructions**

File: `benchmarks/profile_hotspots.py` (lines 17-18 in diff)

The module docstring mentions:
```python
"""...
For detailed line-by-line profiling (requires line_profiler):
    poetry run python benchmarks/profile_hotspots.py --line-profile
```

However, the `--line-profile` option is not actually implemented in the `argparse` setup at the bottom of the file. The documented command-line option does not exist in the code. The `main()` function only supports `--sessions`, `--hands`, `--output`, and `--summary` options.

**2. Minor inconsistency in performance targets between CLAUDE.md and docs/performance.md**

File: `/Users/chrishenry/source/let_it_ride/CLAUDE.md` (lines 91-95)

CLAUDE.md states:
```markdown
## Performance Targets
- Throughput: >=100,000 hands/second
- Memory: <4GB RAM for 10M hands
- Hand evaluation accuracy: 100%
```

The new `docs/performance.md` adds additional targets not in CLAUDE.md:
- Sequential throughput: >=25,000 hands/second
- Startup time: <2 seconds

While not strictly incorrect, these should be synchronized to avoid confusion.

**3. Documentation refers to optimizations not visible in diff**

File: `docs/performance.md` (lines 70-75 in diff, corresponding to lines 113-118)

The documentation describes optimization in `hand_evaluator.py`:
```markdown
### 2. Hand Evaluation (`core/hand_evaluator.py`)
- Pre-computed lookup tables for rank values
- Direct dict-based frequency counting (faster than `Counter` for small inputs)
- Frozen dataclass results for immutability without overhead
```

These are accurate descriptions of the existing code (verified in the source), but they were NOT added by this PR - they are pre-existing optimizations. The documentation might give the impression these were optimizations performed as part of this PR. Consider clarifying that these were pre-existing and the PR primarily optimized deck operations.

**4. Benchmark result values may become stale**

File: `docs/performance.md` (lines 10-14 in diff)

The documentation includes specific "Typical Achievement" values:
```markdown
| Full simulation throughput | >=100,000 hands/second | ~120,000 hands/sec (4 workers) |
| Sequential throughput | >=25,000 hands/second | ~38,000 hands/sec |
| Memory usage (10M hands) | <4GB | ~2GB |
```

These specific numbers will likely become outdated as the codebase evolves. Consider either:
- Removing specific "typical" numbers and just keeping targets
- Adding a note that these are approximate values from initial benchmarking

**5. Missing type hints in benchmark return value documentation**

File: `benchmarks/benchmark_throughput.py` (lines 106-107 in diff)

The `BenchmarkResult` dataclass has good docstrings, but the `meets_target` property lacks a docstring explaining the `None` return case:

```python
@property
def meets_target(self) -> bool | None:
    """Check if throughput meets target, if one is set."""
```

The docstring should clarify what `None` means (i.e., when no target is set, it returns `None`).

**6. Performance test documentation thresholds differ from benchmark targets**

File: `tests/e2e/test_performance.py` (lines 62, 93)

The test file uses reduced thresholds to accommodate CI overhead:
- Line 62: `min_threshold = 10_000  # Reduced for coverage/CI overhead` (target is 100k)
- Line 93: `min_threshold = 5_000  # Reduced for coverage/CI overhead` (production baseline 20K+)

While these have good comments explaining the discrepancy, the large gap between test thresholds and documented targets (10x difference) could be confusing. The relationship between CI test thresholds and production targets could be more clearly documented in `docs/performance.md`.

