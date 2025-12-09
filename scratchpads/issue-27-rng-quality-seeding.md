# LIR-24: RNG Quality and Seeding

**GitHub Issue:** https://github.com/chrishenry/let_it_ride/issues/27

## Overview

Implement proper RNG management for reproducibility and statistical quality by creating an `RNGManager` class that centralizes seed management.

## Current State Analysis

RNG logic is currently scattered across:
- `controller.py` (lines 385-394): Master RNG creation, session seed derivation
- `parallel.py` (lines 200-220): `_generate_session_seeds()` in ParallelExecutor

The current implementation already handles determinism correctly but lacks:
1. Centralized abstraction
2. State serialization for checkpointing
3. Quality validation
4. Cryptographic RNG option

## Tasks

1. [x] Create scratchpad for LIR-24 planning
2. [ ] Create `RNGManager` class in `src/let_it_ride/simulation/rng.py`
   - `__init__(base_seed: int | None = None, use_crypto: bool = False)`
   - `create_rng() -> random.Random` - Create RNG with derived seed
   - `create_worker_rng(worker_id: int) -> random.Random` - Worker-specific RNG
   - `get_state() -> dict[str, Any]` - Serialize for checkpointing
   - `from_state(state: dict) -> RNGManager` - Restore from state
   - `base_seed` property
3. [ ] Implement `validate_rng_quality(rng, sample_size) -> bool`
   - Basic statistical tests (chi-square, runs test)
4. [ ] Add cryptographic RNG option support via `secrets` module
5. [ ] Write comprehensive unit tests
   - Reproducibility (same seed = same results)
   - Worker seed independence
   - State serialization/deserialization
   - Quality validation
6. [ ] Integrate into controller.py and parallel.py
7. [ ] Run tests, linting, type checking

## Key Design Decisions

1. **Seed derivation**: Use `randint(0, 2**31 - 1)` for session seeds (matching current implementation)
2. **Worker seeds**: Include worker_id in seed derivation to guarantee uniqueness
3. **Cryptographic option**: Use `secrets.randbits()` when crypto RNG requested
4. **State format**: JSON-serializable dict with base_seed, seed_counter, use_crypto flag

## Files to Create/Modify

### Create
- `src/let_it_ride/simulation/rng.py`
- `tests/unit/simulation/test_rng.py`

### Modify (integration - lower priority, may defer)
- `src/let_it_ride/simulation/controller.py` - Use RNGManager
- `src/let_it_ride/simulation/parallel.py` - Use RNGManager

## Test Strategy

1. **Reproducibility tests**: Same seed produces identical RNG sequences
2. **Worker isolation tests**: Different worker_ids produce different sequences
3. **State roundtrip tests**: Save/restore state produces identical future sequence
4. **Quality validation tests**: Test passes for good RNG, fails for bad patterns
