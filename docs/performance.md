# Performance

This document covers performance benchmarks, targets, and profiling tools.

## Performance Targets

| Metric | Target | Description |
|--------|--------|-------------|
| Throughput | >= 100,000 hands/second | Single-threaded hand simulation |
| Memory | < 4GB RAM | For 10 million hand simulations |
| Hand evaluation | 100% accuracy | Validated against test suite |

## Running Benchmarks

The `benchmarks/` directory contains profiling and benchmark tools:

### Throughput Benchmark

Measures simulation speed across different configurations:

```bash
poetry run python benchmarks/benchmark_throughput.py
```

This runs:
- Hand evaluation throughput
- Deck shuffle/deal operations
- Full session simulation
- Parallel execution scaling

### Memory Profiling

Measures memory usage during large simulations:

```bash
poetry run python benchmarks/benchmark_memory.py
```

### Hotspot Profiling

Identifies performance bottlenecks:

```bash
poetry run python benchmarks/profile_hotspots.py
```

## Optimization Notes

Key optimizations in the codebase:

1. **Immutable Cards**: Cards are frozen dataclasses, enabling safe reuse
2. **Canonical Deck**: Single canonical deck instance copied for each shuffle
3. **Hand Evaluation**: Optimized combinatorial evaluation without generating all permutations
4. **Parallel Execution**: Worker-based parallelization with independent RNG streams

## Scaling

Throughput scales near-linearly with CPU cores for parallel simulations:

```yaml
simulation:
  workers: auto  # Uses all available cores
```

For memory-constrained environments:

```yaml
simulation:
  workers: 1  # Single worker, lower memory
output:
  formats:
    csv:
      include_hands: false  # Don't store per-hand data
```

## See Also

- [Requirements: Non-Functional Requirements](let_it_ride_requirements.md#4-non-functional-requirements) - Full NFR specification
- [Troubleshooting](troubleshooting.md#performance-issues) - Performance troubleshooting
