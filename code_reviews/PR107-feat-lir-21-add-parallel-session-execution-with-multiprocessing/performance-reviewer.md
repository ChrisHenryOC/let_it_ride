# Performance Review: PR #107 - Parallel Session Execution

**Reviewer**: Performance Specialist
**Date**: 2025-12-07
**PR Title**: feat: LIR-21 Add parallel session execution with multiprocessing

## Summary

This PR introduces parallel session execution using Python's `multiprocessing.Pool`. The implementation is fundamentally sound with good design choices around deterministic seeding and session batching. However, there are several performance concerns related to IPC overhead from serializing the entire `FullConfig` object per worker, suboptimal progress callback behavior, and a potential optimization opportunity in result merging. The code should meet the 100,000 hands/second target, but the identified issues could limit scalability for very large simulations.

---

## Findings by Severity

### High Severity

#### H1: Full Config Serialization Overhead per Worker Task

**Location**: `/src/let_it_ride/simulation/parallel.py`, lines 296-311, 596-604

**Issue**: Each `WorkerTask` includes the complete `FullConfig` object, which is a deeply nested Pydantic model (see `config/models.py` - over 1100 lines of nested models). This config is serialized and deserialized for **every worker task**.

For a simulation with:
- 1M sessions
- 8 workers
- 8 worker tasks

Each task serializes/deserializes `FullConfig`, but this is only 8 times total, which is acceptable. However, if the batching logic ever changed to create more granular tasks (e.g., for progress reporting), this would become a significant bottleneck.

**Current Impact**: Low (only N worker tasks created)
**Potential Impact**: High if task granularity increases

**Recommendation**: Consider extracting only the necessary fields into a lightweight, pickle-optimized dataclass for worker communication rather than passing the full Pydantic model. This would also reduce memory footprint per worker.

```python
@dataclass(frozen=True, slots=True)
class WorkerConfig:
    """Lightweight config for worker processes."""
    strategy_type: str
    strategy_custom: CustomStrategyConfig | None
    bankroll_config: BankrollConfig  # Already a Pydantic model, but smaller
    bonus_strategy: BonusStrategyConfig
    dealer_config: DealerConfig
    hands_per_session: int
    # ... only what's needed
```

---

### Medium Severity

#### M1: Dictionary Comprehension Creates Full Copy of Session Seeds per Worker

**Location**: `/src/let_it_ride/simulation/parallel.py`, line 347 (diff line 594)

**Issue**: In `_create_worker_tasks`, the code creates a new dictionary containing only the seeds needed by each worker:

```python
worker_seeds = {sid: session_seeds[sid] for sid in session_ids}
```

For a simulation with 1M sessions across 8 workers, this means:
- Master process holds 1M seeds (dict of ~32 bytes per entry = ~32MB)
- Each worker task gets a copy of ~125K seeds (~4MB each)
- Total memory for seeds: ~32MB + 8*4MB = ~64MB

This is within acceptable limits but adds unnecessary IPC overhead since each seed dict must be pickled and sent to workers.

**Recommendation**: Since session IDs are contiguous ranges, consider passing only the range boundaries and the master RNG seed, then having workers regenerate their seeds locally:

```python
@dataclass(frozen=True, slots=True)
class WorkerTask:
    worker_id: int
    session_id_start: int
    session_id_end: int
    base_seed: int | None  # Workers regenerate seeds from this
    config: FullConfig
```

Workers would then skip the appropriate number of RNG calls to reach their session range. This trades computation for IPC bandwidth.

---

#### M2: Result Merging Uses Dictionary with O(n) Memory Overhead

**Location**: `/src/let_it_ride/simulation/parallel.py`, lines 361-395 (diff lines 607-643)

**Issue**: The `_merge_results` method collects all results into a dictionary keyed by session_id, then creates an ordered list:

```python
results_by_id: dict[int, SessionResult] = {}
for worker_result in worker_results:
    for session_id, session_result in worker_result.session_results:
        results_by_id[session_id] = session_result

return [results_by_id[i] for i in range(num_sessions)]
```

For 1M sessions, this:
1. Creates a dict with 1M entries (memory overhead for hash table)
2. Creates a final list of 1M items
3. Temporarily holds both in memory

**Recommendation**: Since worker results arrive in worker order (not session order), but each worker's internal results are in session order, use a more memory-efficient merge:

```python
def _merge_results(
    self, worker_results: list[WorkerResult], num_sessions: int
) -> list[SessionResult]:
    # Pre-allocate result list
    results: list[SessionResult | None] = [None] * num_sessions

    for worker_result in worker_results:
        if worker_result.error is not None:
            raise RuntimeError(f"Worker {worker_result.worker_id}: {worker_result.error}")
        for session_id, session_result in worker_result.session_results:
            results[session_id] = session_result

    # Verify completeness
    missing = [i for i, r in enumerate(results) if r is None]
    if missing:
        raise RuntimeError(f"Missing results for {len(missing)} sessions")

    return results  # type: ignore[return-value]
```

This avoids the dict overhead entirely.

---

#### M3: Progress Callback Only Called at Completion in Parallel Mode

**Location**: `/src/let_it_ride/simulation/parallel.py`, lines 427-429 (diff lines 674-676)

**Issue**: The parallel execution only reports progress once all sessions complete:

```python
if progress_callback is not None:
    progress_callback(num_sessions, num_sessions)
```

For long-running simulations (e.g., 10M sessions), users have no visibility into progress. The scratchpad document mentions "Progress aggregation via multiprocessing Queue" but this wasn't implemented.

**Impact**: Poor user experience for large simulations; no way to estimate remaining time.

**Recommendation**: Implement incremental progress reporting. Options:
1. Use `Pool.imap_unordered` with progress updates per completed worker
2. Use `multiprocessing.Queue` for granular progress (as mentioned in scratchpad)
3. At minimum, report progress per completed worker:

```python
with Pool(processes=len(tasks)) as pool:
    worker_results = []
    for i, result in enumerate(pool.imap_unordered(run_worker_sessions, tasks)):
        worker_results.append(result)
        if progress_callback is not None:
            completed = sum(len(wr.session_results) for wr in worker_results)
            progress_callback(completed, num_sessions)
```

---

### Low Severity

#### L1: Duplicate Helper Functions Between parallel.py and controller.py

**Location**: `/src/let_it_ride/simulation/parallel.py`, lines 81-150 (diff lines 328-397)

**Issue**: The functions `_get_main_paytable`, `_get_bonus_paytable`, and `_calculate_bonus_bet` are duplicated from `controller.py`. While this doesn't directly impact performance, it creates maintenance burden and potential for divergence.

**Recommendation**: Extract these helper functions to a shared module (e.g., `simulation/helpers.py`) or import them from controller. Note: The current duplication was likely done to avoid circular imports, but this can be restructured.

---

#### L2: `get_effective_worker_count` Function Duplicated in Two Locations

**Location**: `/src/let_it_ride/simulation/parallel.py`, lines 435-446 (diff lines 682-693)

**Issue**: This logic (resolving "auto" to CPU count) is also present in `ParallelExecutor.__init__`. Minor code duplication.

**Recommendation**: The standalone function is needed for `_should_use_parallel` in controller.py, but consider having `ParallelExecutor.__init__` call this function rather than duplicating the logic.

---

## Performance Target Analysis

### Throughput Target: >= 100,000 hands/second

**Assessment**: LIKELY ACHIEVABLE

The parallel implementation should help achieve this target when:
- Running on multi-core systems (4+ cores)
- Simulating enough sessions to amortize worker pool overhead (>= 10 sessions, per `_MIN_SESSIONS_FOR_PARALLEL`)

**Bottleneck Analysis**:
1. Worker pool creation: One-time cost of ~100-500ms for spawning processes
2. IPC overhead: ~1-5MB per worker for config + seeds (acceptable)
3. Result aggregation: O(n) with current dict approach, but single-threaded

**Recommendation for benchmarking**: Add a benchmark test that measures hands/second with various worker counts and session configurations.

### Memory Target: < 4GB RAM for 10M hands

**Assessment**: LIKELY ACHIEVABLE

Memory analysis for 10M hands (assuming 50 hands/session = 200K sessions):

1. **Session seeds**: 200K * 32 bytes = 6.4 MB
2. **Session results**: 200K * ~200 bytes = 40 MB
3. **Worker overhead**: 8 workers * ~50MB each = 400 MB
4. **Config duplication**: 8 * ~10KB = 80 KB (negligible)

Total estimated peak: ~500 MB, well under 4GB target.

**Note**: The main memory consumer will be any detailed logging or hand-by-hand tracking, not the parallel execution infrastructure.

---

## Specific Code Recommendations

### 1. Consider `maxtasksperchild` for Long Simulations

**Location**: `/src/let_it_ride/simulation/parallel.py`, line 424 (diff line 671)

```python
with Pool(processes=len(tasks)) as pool:
```

For very long simulations, worker processes may accumulate memory over time. Consider:

```python
with Pool(processes=len(tasks), maxtasksperchild=100) as pool:
```

This recycles workers periodically to prevent memory bloat.

### 2. Add Worker Process Initialization

Consider using `initializer` parameter to pre-import heavy modules in workers:

```python
def _worker_init():
    """Initialize worker process."""
    # Pre-import heavy modules to avoid per-task import overhead
    import let_it_ride.core.game_engine  # noqa: F401
    import let_it_ride.strategy  # noqa: F401

with Pool(processes=len(tasks), initializer=_worker_init) as pool:
```

### 3. Consider `Pool.map` Chunk Size

The current code uses default chunking. For many sessions, explicit chunk sizing may improve performance:

```python
chunk_size = max(1, len(tasks) // (len(tasks) * 4))
worker_results = pool.map(run_worker_sessions, tasks, chunksize=chunk_size)
```

However, since each task already contains a batch of sessions, this is less critical.

---

## Well-Optimized Sections

1. **Deterministic RNG seeding**: Pre-generating all seeds before distribution ensures reproducibility regardless of worker execution order. This is the correct approach.

2. **Session batching strategy**: Dividing sessions evenly among workers minimizes load imbalance. The `ceil()` approach ensures all sessions are covered.

3. **Worker-local component creation**: Creating Strategy, Paytables, etc. fresh in each worker avoids serialization of complex objects and potential pickle issues.

4. **Use of `__slots__`**: Both `WorkerTask` and `WorkerResult` use `slots=True` for memory efficiency.

5. **Threshold for parallel execution**: The `_MIN_SESSIONS_FOR_PARALLEL = 10` threshold appropriately avoids parallel overhead for small simulations.

---

## Summary of Recommended Changes

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| High | Consider lightweight WorkerConfig | Medium | Reduces IPC overhead |
| Medium | Optimize result merging | Low | Reduces memory usage |
| Medium | Add incremental progress reporting | Medium | Improves UX |
| Medium | Pass seed ranges instead of seed dicts | Medium | Reduces IPC |
| Low | Deduplicate helper functions | Low | Maintainability |

---

## Files Modified in This PR

- `src/let_it_ride/simulation/controller.py` - Added parallel execution path
- `src/let_it_ride/simulation/parallel.py` - New file with ParallelExecutor
- `tests/integration/test_parallel.py` - Comprehensive test coverage
- `scratchpads/issue-24-parallel-execution.md` - Design documentation
