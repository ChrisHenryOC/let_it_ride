# Performance Guide

This document describes the Let It Ride simulator's performance characteristics, benchmarking methodology, and optimization techniques.

## Performance Targets

The simulator has the following performance targets:

| Metric | Target | Typical Achievement |
|--------|--------|---------------------|
| Full simulation throughput | ≥100,000 hands/second | ~120,000 hands/sec (4 workers) |
| Sequential throughput | ≥25,000 hands/second | ~38,000 hands/sec |
| Memory usage (10M hands) | <4GB | ~2GB |
| Startup time | <2 seconds | <1 second |

## Running Benchmarks

### Throughput Benchmarks

```bash
poetry run python benchmarks/benchmark_throughput.py
```

This runs several benchmarks:
- **Hand Evaluation (5-card)**: Isolated hand evaluation throughput
- **Hand Evaluation (3-card)**: Three-card bonus hand evaluation
- **Deck Operations**: Shuffle, reset, and deal operations
- **Full Simulation (sequential)**: Single-worker simulation
- **Full Simulation (parallel)**: Multi-worker simulation

### Memory Benchmarks

```bash
poetry run python benchmarks/benchmark_memory.py
```

Measures memory usage at various simulation scales:
- Small (1K sessions)
- Medium (10K sessions)
- Large (100K sessions)
- 10M hands target test

### Profiling

```bash
# Full profile output
poetry run python benchmarks/profile_hotspots.py

# Summary only
poetry run python benchmarks/profile_hotspots.py --summary

# Save for external visualization (snakeviz)
poetry run python benchmarks/profile_hotspots.py --output profile.prof
```

## Hot Paths

The following functions are on the critical path and have been optimized:

### 1. Deck Operations (`core/deck.py`)

- `shuffle()`: Uses Python's built-in `random.shuffle()` which is implemented in C
- `reset()`: Reuses list memory via `clear()` + `extend()` instead of creating new lists
- `deal()`: Uses `pop()` for O(1) removal from list end

### 2. Hand Evaluation (`core/hand_evaluator.py`)

- Pre-computed lookup tables for rank values
- Direct dict-based frequency counting (faster than `Counter` for small inputs)
- Frozen dataclass results for immutability without overhead

### 3. Three-Card Evaluation (`core/three_card_evaluator.py`)

- Sorting network for 3-element sort (avoids `sorted()` allocation)
- Direct variable unpacking (avoids list/dict allocations)
- Manual unique rank calculation without dict overhead

### 4. Hand Analysis (`core/hand_analysis.py`)

- Single-pass suit grouping
- Optimized straight potential analysis with early exits
- Pre-computed high card value set

## Memory Efficiency

The codebase uses several techniques to minimize memory usage:

### Frozen Dataclasses
Results are stored in frozen dataclasses which:
- Use less memory than regular objects
- Are hashable (can be cached if needed)
- Prevent accidental mutation

### `__slots__`
Mutable session state classes use `__slots__` to reduce per-instance memory:
- `Session`
- `TableSession._SeatState`
- `Table`

### List Reuse
Deck operations reuse list memory rather than creating new lists each hand:
```python
# Before (creates new list each call):
self._cards = list(_CANONICAL_DECK)

# After (reuses existing list memory):
self._cards.clear()
self._cards.extend(_CANONICAL_DECK)
```

## Parallel Execution

For large simulations, parallel execution provides significant speedup:

```yaml
simulation:
  workers: 4  # Use multiple CPU cores
```

Workers are independent and share no state, avoiding synchronization overhead.

## Profiling Your Own Simulations

To profile a specific configuration:

```python
from benchmarks.profile_hotspots import profile_simulation

# Profile and print results
output = profile_simulation(num_sessions=1000, hands_per_session=100)
print(output)
```

## Performance Testing

The e2e test suite includes performance tests:

```bash
# Run all performance tests
poetry run pytest tests/e2e/test_performance.py -v

# Run only slow tests (more thorough)
poetry run pytest tests/e2e/test_performance.py -v -m slow
```

Performance tests verify:
- Minimum throughput thresholds
- Memory usage constraints
- Parallel scaling efficiency
- Configuration overhead (bonus, dealer discard, strategies)

## Tips for Optimal Performance

1. **Use parallel execution** for large simulations (>1000 sessions)
2. **Disable bonus betting** if not needed (adds ~30% overhead)
3. **Use basic strategy** - custom strategies with complex conditions may be slower
4. **Set appropriate stop conditions** - shorter sessions complete faster
5. **Run without coverage** - pytest coverage adds ~60% overhead
