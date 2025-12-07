# LIR-21: Parallel Session Execution

**GitHub Issue**: #24
**Status**: In Progress

## Overview

Add parallel execution support using multiprocessing for improved throughput. The `ParallelExecutor` manages worker pools to execute sessions concurrently while maintaining reproducibility through deterministic RNG seeding.

## Key Design Decisions

### 1. RNG Seeding Strategy

To maintain determinism in parallel execution:
1. Pre-generate ALL session seeds from the master RNG BEFORE parallel execution begins
2. Each session gets a deterministic seed regardless of which worker executes it
3. Workers receive session ID → seed mappings, not RNG objects

```python
# Pre-generate all seeds
seeds = {}
master_rng = random.Random(base_seed)
for session_id in range(num_sessions):
    seeds[session_id] = master_rng.randint(0, 2**31 - 1)

# Worker receives specific seeds for its batch
worker_batch = [(session_id, seeds[session_id]) for session_id in worker_session_ids]
```

### 2. Architecture

```
SimulationController
    │
    ├── workers == 1 → Sequential execution (existing code path)
    │
    └── workers > 1 → ParallelExecutor
                          │
                          ├── Create worker pool
                          ├── Pre-generate all session seeds
                          ├── Distribute session batches to workers
                          ├── Collect results
                          └── Aggregate progress callbacks
```

### 3. Worker Process Design

Each worker:
- Receives: session IDs, FullConfig (serialized), session seeds
- Creates: Fresh Strategy, Paytables, BettingSystemFactory (not shared across processes)
- Returns: List of SessionResult objects

### 4. Session Batching

Divide sessions evenly among workers:
```python
batch_size = ceil(num_sessions / num_workers)
# Worker 0: sessions 0..batch_size-1
# Worker 1: sessions batch_size..2*batch_size-1
# etc.
```

### 5. Progress Aggregation

Use `multiprocessing.Queue` for progress updates:
- Workers send (worker_id, sessions_completed) to queue
- Main process polls queue and aggregates into single callback

## Files to Create

- `src/let_it_ride/simulation/parallel.py`
- `tests/integration/test_parallel.py`

## Files to Modify

- `src/let_it_ride/simulation/controller.py` - Add parallel execution path

## Implementation Tasks

1. [x] Review existing SimulationController
2. [x] Create ParallelExecutor class
3. [x] Implement worker function (top-level for pickling)
4. [x] Implement session batching
5. [x] Implement RNG pre-seeding
6. [x] Implement progress reporting (at completion, Queue-based not implemented)
7. [x] Implement graceful worker failure handling
8. [x] Integrate into SimulationController
9. [x] Write integration tests
10. [x] Test parallel vs sequential equivalence

## Testing Strategy

### Integration Tests
1. Parallel produces correct number of sessions
2. Same seed produces identical results (parallel vs sequential)
3. Different seeds produce different results
4. Progress callback invoked correctly
5. Worker failure handling
6. Auto worker count detection

### Equivalence Test
Run same config with workers=1 and workers=N, verify statistically equivalent results (session profits should match exactly when same seed used).
