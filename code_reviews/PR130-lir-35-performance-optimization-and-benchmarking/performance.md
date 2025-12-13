# Performance Review: PR #130 - LIR-35 Performance Optimization and Benchmarking

## Summary

This PR introduces a comprehensive performance benchmarking suite and applies optimizations to the deck operations. The optimizations are well-targeted, moving from a Python-level Fisher-Yates loop to the C-implemented `random.shuffle()` and reusing list memory in deck reset. However, the benchmarking code itself contains several performance patterns that could be improved, and there are missed optimization opportunities in the hot path that could help achieve the stated targets more reliably.

## Findings by Severity

### High

**H1. Hand evaluation benchmark generates hands inefficiently - potential memory pressure**

File: `/Users/chrishenry/source/let_it_ride/benchmarks/benchmark_throughput.py`
Lines: 300-304

```python
# Pre-generate hands to avoid random overhead in timing
hands = [rng.sample(all_cards, 5) for _ in range(iterations)]
```

Pre-generating 100,000 hands as a list of lists allocates approximately 5MB of memory upfront (100,000 * 5 cards * ~100 bytes per Card reference). This is acceptable for benchmarking, but the same pattern in `benchmark_three_card_evaluation` and `benchmark_hand_evaluation` could cause memory pressure when running all benchmarks in sequence. Consider using a generator with `itertools.islice` or pre-allocating with a fixed-size buffer if memory becomes constrained.

**H2. 5-card hand evaluation target (500k/s) is not met according to scratchpad results**

File: `/Users/chrishenry/source/let_it_ride/scratchpads/issue-38-performance-benchmarking.md`
Lines: 939-945

The scratchpad reports 5-card hand evaluation at 332k/s vs. target of 500k/s, marked as "N/A". While the overall simulation target of 100k hands/s is achieved, the hand evaluator itself is a significant bottleneck. The `evaluate_five_card_hand` function at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/hand_evaluator.py` lines 111-276 performs:

1. Set creation for duplicate check (line 127)
2. Two list comprehensions (lines 132-133)
3. Dictionary creation via loop (lines 136-138)
4. Multiple `sorted()` calls (lines 145, 162-164)

For a true hot-path optimization, consider:
- Using a tuple comparison instead of set for duplicate detection
- Pre-computing rank values in Card class (avoiding `.value` lookups)
- Using a lookup table approach for hand evaluation (Cactus Kev style)

---

### Medium

**M1. `dealt_cards()` returns a defensive copy on every call**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/deck.py`
Lines: 75-80

```python
def dealt_cards(self) -> list[Card]:
    """Return a copy of the list of dealt cards.

    Returns a copy to prevent external modification.
    """
    return self._dealt.copy()
```

If this method is called frequently during simulation (e.g., for logging or validation), the copy allocates a new list on each call. Consider:
- Returning a tuple (immutable, no defensive copy needed)
- Providing a `dealt_cards_view()` that returns a read-only view if Python 3.11+ features are available
- Documenting that callers should cache the result if called multiple times

**M2. Memory benchmark lacks warmup run**

File: `/Users/chrishenry/source/let_it_ride/benchmarks/benchmark_memory.py`
Lines: 69-129

The memory benchmark measures the first run without a warmup. Python's memory allocator (pymalloc) and the JIT-like optimizations in the runtime mean the first run may have different allocation patterns than steady-state. Consider running a small warmup simulation before starting `tracemalloc`:

```python
# Warmup to stabilize Python's internal allocators
gc.collect()
_ = SimulationController(config).run()  # Discard result
gc.collect()
tracemalloc.start()
# ... actual measurement
```

**M3. Profile hotspot analysis accesses internal pstats API**

File: `/Users/chrishenry/source/let_it_ride/benchmarks/profile_hotspots.py`
Lines: 673-675

```python
# Access the internal stats dict (type: ignore for pstats internal API)
stats_dict = stats.stats  # type: ignore[attr-defined]
```

Accessing `stats.stats` directly is fragile as it relies on an undocumented internal API. The `pstats` module API may change between Python versions. Consider using `stats.print_stats()` to a StringIO and parsing, or documenting the specific Python version dependency.

**M4. Parallel executor creates new `WorkerTask` with full config copy per worker**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py`
Lines: 247-257

```python
tasks.append(
    WorkerTask(
        worker_id=worker_id,
        session_ids=session_ids,
        session_seeds=worker_seeds,
        config=config,  # Full config passed to each worker
    )
)
```

Each `WorkerTask` contains the full `FullConfig` object which gets pickled and sent to worker processes. While this is necessary for multiprocessing, for very large configs with extensive custom strategy rules or paytables, this could add serialization overhead. This is acceptable for typical use but worth documenting as a potential issue for complex configurations.

---

### Low

**L1. Deck class missing `__slots__` declaration**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/deck.py`
Lines: 20-30

The `Deck` class is instantiated once per session but the PR's performance documentation mentions `__slots__` is used on frequently instantiated classes. Since the performance guide at `/Users/chrishenry/source/let_it_ride/docs/performance.md` lines 847-851 mentions "Table" uses `__slots__`, the `Deck` class should follow the same pattern for consistency:

```python
class Deck:
    __slots__ = ("_cards", "_dealt")
```

**L2. List comprehension in deal() creates intermediate list**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/core/deck.py`
Lines: 66-68

```python
# Use pop() for O(1) removal from end, avoiding list slice allocation
dealt = [self._cards.pop() for _ in range(count)]
self._dealt.extend(dealt)
```

This creates an intermediate list `dealt` before extending `_dealt`. For the typical case of dealing 3 or 5 cards, this is negligible, but could be optimized to:

```python
for _ in range(count):
    card = self._cards.pop()
    self._dealt.append(card)
return self._dealt[-count:]
```

However, the current implementation is clearer and the cost is minimal. Consider only if profiling shows this as a bottleneck.

**L3. Benchmark results not programmatically comparable to targets**

File: `/Users/chrishenry/source/let_it_ride/benchmarks/benchmark_throughput.py`
Lines: 459-468

The `run_all_benchmarks()` function returns results but there is no automated CI integration or exit code based on target failures. Consider adding a `main()` that exits with non-zero status if any target-bearing benchmark fails, enabling CI/CD enforcement:

```python
if __name__ == "__main__":
    results = run_all_benchmarks()
    print_results(results)
    # Exit with error if any benchmarks with targets failed
    if any(r.meets_target is False for r in results):
        sys.exit(1)
```

**L4. Progress callback not utilized in parallel mode for intermediate progress**

File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py`
Lines: 330-333

```python
# Report progress (all sessions complete)
if progress_callback is not None:
    progress_callback(num_sessions, num_sessions)
```

The progress callback is only called once at completion in parallel mode, not incrementally. While documented, this could be improved using `imap_unordered` with a callback per batch completion for long-running simulations.

**L5. Performance documentation claims sorting network for 3-card but it is conditional swaps**

File: `/Users/chrishenry/source/let_it_ride/docs/performance.md`
Lines: 830-831

```
- Sorting network for 3-element sort (avoids `sorted()` allocation)
```

The code in `three_card_evaluator.py` lines 77-82 uses conditional swaps which is correct, but "sorting network" is a specific term for a fixed sequence of comparators. The current implementation uses data-dependent branches (three `if` statements) rather than a true sorting network. This is a documentation accuracy issue rather than a performance issue.
