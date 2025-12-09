# Performance Review: PR #115 - LIR-24 RNG Quality and Seeding

## Summary

The RNGManager implementation is well-designed for performance with appropriate use of `__slots__` and `frozen=True, slots=True` dataclasses. The code follows good practices for reproducible simulation seeding. However, there are two medium-severity performance concerns: the `validate_rng_quality` function has O(n log n) complexity due to sorting for median calculation, and the `_runs_test` creates unnecessary intermediate lists. These issues are acceptable for validation code (not hot path) but could be optimized if validation is called frequently.

## Findings by Severity

### Critical Issues

None identified.

### High Severity Issues

None identified.

### Medium Severity Issues

#### 1. O(n log n) Median Calculation in Runs Test
**File:** `src/let_it_ride/simulation/rng.py:313`

```python
median = sorted(samples)[n // 2]
```

**Impact:** The runs test sorts the entire sample array to find the median, which has O(n log n) complexity. With the default `sample_size=10000`, this creates a 10,000-element sorted copy of the list.

**Recommendation:** Use `statistics.median()` which is O(n) on average using the quickselect algorithm, or use `numpy.median()` if numpy is available:

```python
# Option 1: Standard library (O(n) average)
import statistics
median = statistics.median(samples)

# Option 2: If performance-critical, use nth_element approach
# Python stdlib doesn't have this, but you could implement it
```

**Mitigating Factor:** This is validation code, not on the hot path. If `validate_rng_quality` is called once per simulation run, the impact is negligible. Only a concern if called per-session or per-hand.

#### 2. Intermediate List Creation in Runs Test
**File:** `src/let_it_ride/simulation/rng.py:316`

```python
binary = [1 if s >= median else 0 for s in samples]
```

**Impact:** Creates a 10,000-element intermediate list when a generator would suffice for counting runs. Combined with the subsequent iteration at line 319-321, this is O(2n) space and O(2n) time.

**Recommendation:** Compute runs in a single pass without materializing the binary list:

```python
def _runs_test(samples: Sequence[float], alpha: float) -> tuple[float, bool]:
    n = len(samples)
    if n < 20:
        return 0.0, True

    # Use statistics.median for O(n) median (or sorted for current behavior)
    median = sorted(samples)[n // 2]

    # Single-pass computation
    runs = 1
    n1 = 0  # count above median
    prev_above = samples[0] >= median
    if prev_above:
        n1 = 1

    for s in samples[1:]:
        curr_above = s >= median
        if curr_above:
            n1 += 1
        if curr_above != prev_above:
            runs += 1
            prev_above = curr_above

    n2 = n - n1
    # ... rest of calculation
```

This eliminates the intermediate list and reduces to O(n) time and O(1) space (excluding the sorted median calculation).

### Low Severity Issues

#### 3. Dictionary Comprehension for Session Seeds
**File:** `src/let_it_ride/simulation/rng.py:158-161`

```python
return {
    session_id: self._master_rng.randint(0, self._MAX_SEED)
    for session_id in range(num_sessions)
}
```

**Impact:** Creates a dictionary keyed by consecutive integers 0 to n-1. This is slightly less memory-efficient than a list and has O(n) lookup overhead for no benefit since keys are sequential.

**Note:** This is already used optimally in `parallel.py:248` where worker_seeds are extracted by session_id, so the dict structure is appropriate for the API. No change needed.

#### 4. Temporary Random Instance in create_worker_rng
**File:** `src/let_it_ride/simulation/rng.py:140-143`

```python
combined_seed = (self._base_seed * 31 + worker_id) % (self._MAX_SEED + 1)
worker_master = random.Random(combined_seed)
worker_seed = worker_master.randint(0, self._MAX_SEED)
return random.Random(worker_seed)
```

**Impact:** Creates two `random.Random` instances where one would suffice. The intermediate RNG is created just to generate one seed value.

**Recommendation:** The design is intentional for seed quality (mixing via RNG rather than simple arithmetic). The overhead is minimal since this is called once per worker, not per session. Keep as-is.

## Positive Performance Observations

### Excellent Practices Noted

1. **`__slots__` Usage (rng.py:64)**
   ```python
   __slots__ = ("_base_seed", "_use_crypto", "_seed_counter", "_master_rng")
   ```
   This reduces memory overhead per RNGManager instance and provides faster attribute access.

2. **Frozen Slots Dataclass (rng.py:25-26)**
   ```python
   @dataclass(frozen=True, slots=True)
   class RNGQualityResult:
   ```
   Excellent choice for immutable result objects with minimal memory footprint.

3. **Pre-computed Critical Values (rng.py:362-401)**
   The chi-square critical value tables avoid runtime computation of inverse CDF values, providing O(1) lookup for common cases.

4. **Pre-allocated Result List in Parallel Merge (parallel.py:286)**
   ```python
   results: list[SessionResult | None] = [None] * num_sessions
   ```
   Good use of pre-allocation for O(1) direct assignment instead of dict-based collection.

5. **Efficient Session Seed Pre-generation**
   The pattern of pre-generating all seeds before parallel execution ensures determinism without synchronization overhead during parallel execution.

## Performance Targets Assessment

| Target | Assessment |
|--------|------------|
| >= 100,000 hands/second | **No impact** - RNG is initialized once per session, not per hand. The Mersenne Twister RNG used by `random.Random` is highly efficient. |
| < 4GB RAM for 10M hands | **No impact** - RNGManager uses fixed memory regardless of simulation size. Session seeds dict is O(n) but with small per-entry overhead. |

## Concurrency Considerations

1. **Thread Safety:** The RNGManager is NOT thread-safe (mutable state in `_seed_counter` and `_master_rng`). This is acceptable because the parallel implementation correctly uses pre-generated seeds rather than sharing an RNGManager across processes.

2. **Process Independence:** Each worker process creates fresh components (strategy, paytables, betting system) per `parallel.py:139-143`, ensuring no shared mutable state across processes.

3. **Reproducibility Guarantee:** The pre-generation of all session seeds (`create_session_seeds`) before parallel distribution ensures deterministic results regardless of worker execution order.

## Recommendations Summary

| Priority | Recommendation | Effort | Impact |
|----------|---------------|--------|--------|
| Low | Replace `sorted()` with `statistics.median()` in runs test | Low | Minor - validation only |
| Low | Refactor `_runs_test` for single-pass computation | Medium | Minor - validation only |

## Conclusion

The RNG implementation is well-suited for the project's performance targets. The identified issues are in validation code that runs infrequently and do not affect the simulation hot path. The use of `__slots__`, frozen dataclasses, and proper parallel seed management demonstrates good performance awareness. No changes are required to meet the 100,000 hands/second throughput target or the memory budget.
