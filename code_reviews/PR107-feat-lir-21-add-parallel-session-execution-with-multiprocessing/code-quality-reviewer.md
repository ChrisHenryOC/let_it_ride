# Code Quality Review: PR #107 - LIR-21 Parallel Session Execution

## Summary

This PR adds parallel execution support using Python's `multiprocessing.Pool`. The implementation is well-structured with clear separation between the `ParallelExecutor` class and worker functions. The code demonstrates good practices for deterministic seeding and result aggregation. However, there are several code quality issues including significant code duplication between `parallel.py` and `controller.py`, potential improvements to error handling, and some API design considerations.

## Findings by Severity

### High Severity

#### H1: Significant Code Duplication - Paytable and Bonus Logic

**Files:** `src/let_it_ride/simulation/parallel.py` (lines 81-151)

The functions `_get_main_paytable`, `_get_bonus_paytable`, and `_calculate_bonus_bet` in `parallel.py` are essentially duplicates of the corresponding functions in `controller.py`. This violates the DRY principle and creates maintenance burden.

**Location:** Lines 81-151 (parallel.py)

**Impact:** If paytable logic changes in one location, the other must be updated manually, creating a risk of divergence and bugs.

**Recommendation:** Extract these functions to a shared utility module (e.g., `simulation/utils.py`) and import them in both `controller.py` and `parallel.py`:

```python
# simulation/utils.py
from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_a,
    bonus_paytable_b,
    bonus_paytable_c,
    standard_main_paytable,
)

def get_main_paytable(config: FullConfig) -> MainGamePaytable:
    """Get the main game paytable from configuration."""
    ...

def get_bonus_paytable(config: FullConfig) -> BonusPaytable | None:
    """Get the bonus paytable from configuration."""
    ...

def calculate_bonus_bet(config: FullConfig) -> float:
    """Calculate the bonus bet amount from configuration."""
    ...
```

---

#### H2: `_create_session_config` Duplicates Controller Logic

**File:** `src/let_it_ride/simulation/parallel.py` (lines 154-175)

The `_create_session_config` function duplicates the session configuration logic found in `SimulationController._create_session`. This is the same DRY violation pattern.

**Recommendation:** Extract session configuration creation to a shared utility function.

---

### Medium Severity

#### M1: Missing Export in `__init__.py`

**File:** `src/let_it_ride/simulation/__init__.py`

The `ParallelExecutor` class and related types (`WorkerTask`, `WorkerResult`, `get_effective_worker_count`) are not exported from the simulation module. While they may be internal implementation details, `get_effective_worker_count` is imported from `controller.py`, suggesting some level of public API.

**Recommendation:** Either:
1. Add exports to `__init__.py` if these are intended to be public
2. Or, move `get_effective_worker_count` to the controller module to avoid the circular import workaround entirely

---

#### M2: Bare Exception Catching in Worker Function

**File:** `src/let_it_ride/simulation/parallel.py` (lines 263-268)

```python
except Exception as e:
    return WorkerResult(
        worker_id=task.worker_id,
        session_results=[],
        error=str(e),
    )
```

Catching bare `Exception` loses the exception type and traceback information. While this is necessary to prevent worker crashes from killing the pool, the error handling could be more informative.

**Recommendation:** Consider including the exception type in the error message:

```python
except Exception as e:
    return WorkerResult(
        worker_id=task.worker_id,
        session_results=[],
        error=f"{type(e).__name__}: {e}",
    )
```

---

#### M3: Duplicated `get_effective_worker_count` Logic

**File:** `src/let_it_ride/simulation/parallel.py` (lines 435-447)

The logic in `get_effective_worker_count` duplicates the logic in `ParallelExecutor.__init__`:

```python
# In ParallelExecutor.__init__
if num_workers == "auto":
    self._num_workers = os.cpu_count() or 1
else:
    self._num_workers = max(1, num_workers)

# In get_effective_worker_count
if workers == "auto":
    return os.cpu_count() or 1
return max(1, workers)
```

**Recommendation:** Have `ParallelExecutor.__init__` use `get_effective_worker_count`:

```python
def __init__(self, num_workers: int | Literal["auto"]) -> None:
    self._num_workers = get_effective_worker_count(num_workers)
```

---

#### M4: Progress Callback Only Called at Completion

**File:** `src/let_it_ride/simulation/parallel.py` (lines 428-429)

The progress callback is only invoked once at the end of parallel execution:

```python
if progress_callback is not None:
    progress_callback(num_sessions, num_sessions)
```

This differs significantly from sequential mode where progress is reported per session. The docstring in `controller.py` mentions "at completion (parallel)" but this is a significant behavior difference that could surprise users expecting incremental progress.

**Recommendation:** Consider using `multiprocessing.Queue` to aggregate progress from workers (as mentioned in the scratchpad design but not implemented). At minimum, document this limitation clearly in the public API.

---

#### M5: Inconsistent Type Annotation Style

**File:** `tests/integration/test_parallel.py` (lines 47-48)

```python
workers: int | str = 2,
```

The type annotation uses `int | str` when it should be `int | Literal["auto"]` to match the actual API contract.

**Recommendation:** Update to use the precise type:

```python
from typing import Literal

def create_test_config(
    ...
    workers: int | Literal["auto"] = 2,
) -> FullConfig:
```

---

### Low Severity

#### L1: Unused `config` Parameter

**File:** `src/let_it_ride/simulation/parallel.py` (line 178)

In `_run_single_session`, the `config` parameter is passed but only used for `dealer_config`:

```python
def _run_single_session(
    seed: int,
    config: FullConfig,  # Only used for config.dealer
    ...
)
```

**Recommendation:** Consider passing only `dealer_config: DealerConfig | None` instead of the entire `FullConfig` to make the dependency explicit.

---

#### L2: Magic Number for Seed Range

**File:** `src/let_it_ride/simulation/parallel.py` (line 314)

```python
master_rng.randint(0, 2**31 - 1)
```

This magic number appears in both `parallel.py` and `controller.py`.

**Recommendation:** Define a constant:

```python
_MAX_SEED = 2**31 - 1  # Maximum seed value for reproducibility
```

---

#### L3: Test Helper Could Use More Precise Return Type

**File:** `tests/integration/test_parallel.py` (line 227)

The `type: ignore[list-item]` comment in the test indicates a type mismatch:

```python
WorkerResult(worker_id=0, session_results=[(0, None)], error=None),  # type: ignore[list-item]
```

While acceptable in tests, this could be avoided by creating a proper mock SessionResult.

---

## Positive Observations

1. **Clear Module Documentation**: The module docstring clearly explains the purpose and key design decisions.

2. **Good Use of `__slots__`**: Both `WorkerTask`, `WorkerResult`, and `ParallelExecutor` use `__slots__` for memory efficiency, consistent with project standards.

3. **Frozen Dataclasses**: `WorkerTask` and `WorkerResult` are properly marked as `frozen=True` for immutability.

4. **Deterministic Seeding Strategy**: The pre-generation of all session seeds before parallel execution is the correct approach for reproducibility.

5. **Comprehensive Test Coverage**: The test file covers many edge cases including:
   - Worker count handling (zero, negative, auto)
   - Session distribution (even, uneven, fewer sessions than workers)
   - Parallel vs sequential equivalence
   - Error handling

6. **Well-Structured Test Classes**: Tests are organized into logical groups by functionality.

7. **Type Annotations**: Functions have proper type annotations with return types.

---

## Actionable Recommendations (Prioritized)

1. **[High]** Extract duplicated paytable/bonus logic to a shared `simulation/utils.py` module
2. **[High]** Extract session config creation to a shared utility function
3. **[Medium]** Use `get_effective_worker_count` in `ParallelExecutor.__init__`
4. **[Medium]** Include exception type in worker error messages
5. **[Medium]** Fix the type annotation for `workers` parameter in test helper
6. **[Low]** Define a constant for the max seed value
7. **[Low]** Consider implementing incremental progress reporting for parallel mode

---

## Files Reviewed

- `src/let_it_ride/simulation/parallel.py` (new file, 446 lines)
- `src/let_it_ride/simulation/controller.py` (modified, 40 lines added)
- `tests/integration/test_parallel.py` (new file, 553 lines)
- `scratchpads/issue-24-parallel-execution.md` (new file, documentation)
