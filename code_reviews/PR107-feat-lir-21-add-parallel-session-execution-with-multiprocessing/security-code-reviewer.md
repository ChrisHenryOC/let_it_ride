# Security Code Review: PR #107 - Parallel Session Execution

**Reviewer**: Security Code Reviewer
**PR**: #107 - feat: LIR-21 Add parallel session execution with multiprocessing
**Date**: 2025-12-07

## Summary

This PR introduces parallel execution support using Python's `multiprocessing.Pool` to distribute simulation sessions across worker processes. The implementation is generally well-designed from a security perspective, with proper process isolation and deterministic seeding. However, there are some areas that warrant attention regarding error information exposure, resource exhaustion potential, and implicit pickle serialization.

## Findings by Severity

### Medium Severity

#### 1. Potential Error Information Leakage in Worker Exceptions (CWE-209)

**Location**: `src/let_it_ride/simulation/parallel.py`, lines 262-268 (in the diff, function `run_worker_sessions`)

**Description**: The worker function catches all exceptions and includes the full exception message in the `WorkerResult.error` field, which is then propagated and potentially exposed in error messages:

```python
except Exception as e:
    return WorkerResult(
        worker_id=task.worker_id,
        session_results=[],
        error=str(e),
    )
```

And later in `_merge_results`:

```python
errors = [f"Worker {wr.worker_id}: {wr.error}" for wr in failed_workers]
raise RuntimeError(f"Worker failures: {'; '.join(errors)}")
```

**Impact**: In production environments, detailed exception messages could leak sensitive information about file paths, system configuration, or internal application state. While this is a simulation tool, adopting secure patterns is good practice.

**Remediation**: Consider logging the full exception details while returning a sanitized error message:

```python
import logging

logger = logging.getLogger(__name__)

except Exception as e:
    logger.exception(f"Worker {task.worker_id} failed")
    return WorkerResult(
        worker_id=task.worker_id,
        session_results=[],
        error="Worker execution failed",  # Generic message
    )
```

**References**: CWE-209 (Generation of Error Message Containing Sensitive Information)

---

#### 2. No Upper Bound on Worker Count (CWE-400)

**Location**: `src/let_it_ride/simulation/parallel.py`, lines 285-289 (in the diff, `__init__` method)

**Description**: The `ParallelExecutor` accepts any positive integer for `num_workers` without an upper bound:

```python
if num_workers == "auto":
    self._num_workers = os.cpu_count() or 1
else:
    self._num_workers = max(1, num_workers)
```

**Impact**: A misconfigured or malicious configuration could specify an extremely high worker count (e.g., 10,000), potentially exhausting system resources (file descriptors, memory, process table entries) and causing denial of service.

**Remediation**: Add a sensible upper bound, perhaps based on CPU count:

```python
MAX_WORKERS = 64  # Or use os.cpu_count() * 4 as a ceiling

if num_workers == "auto":
    self._num_workers = os.cpu_count() or 1
else:
    cpu_count = os.cpu_count() or 1
    max_allowed = min(MAX_WORKERS, cpu_count * 4)
    self._num_workers = min(max(1, num_workers), max_allowed)
```

**References**: CWE-400 (Uncontrolled Resource Consumption)

---

### Low Severity

#### 3. Implicit Pickle Serialization of Configuration Objects (CWE-502)

**Location**: `src/let_it_ride/simulation/parallel.py`, line 310 (`config` attribute in `WorkerTask`)

**Description**: Python's `multiprocessing.Pool.map()` uses pickle to serialize arguments passed to worker functions. The `WorkerTask` dataclass contains a `FullConfig` (Pydantic model) that gets pickled and sent to workers.

```python
@dataclass(frozen=True, slots=True)
class WorkerTask:
    ...
    config: FullConfig  # This gets pickled
```

**Impact**: In this context, the risk is minimal because:
1. Configuration objects are created internally, not from untrusted sources
2. The data flows from the main process to workers, not from external sources
3. Pydantic models are generally safe to pickle

However, if the configuration were ever to include user-controllable data that could influence the pickle deserialization (e.g., custom class references), this could become a security issue.

**Remediation**: No immediate action required, but consider:
1. Documenting that configuration objects must be trustworthy
2. If future requirements involve external configuration loading, ensure validation occurs before parallelization
3. For defense in depth, consider using JSON serialization for cross-process communication instead of pickle

**References**: CWE-502 (Deserialization of Untrusted Data)

---

#### 4. Seed Range Limitation May Reduce Entropy

**Location**: `src/let_it_ride/simulation/parallel.py`, lines 312-315 (in the diff, `_generate_session_seeds`)

**Description**: Session seeds are generated within a limited range:

```python
return {
    session_id: master_rng.randint(0, 2**31 - 1)
    for session_id in range(num_sessions)
}
```

**Impact**: Using 31-bit seeds (approximately 2.1 billion values) provides adequate entropy for simulation reproducibility purposes but is less than the full 64-bit seed space that `random.Random` can utilize. This is not a security vulnerability per se, but could theoretically reduce the randomness space for very large-scale simulations.

**Remediation**: For simulations, 31-bit seeds are typically sufficient. If enhanced randomness is needed:

```python
master_rng.randint(0, 2**63 - 1)
```

---

### Informational

#### 5. Good Practice: Process Isolation

The design correctly creates fresh Strategy, Paytables, and BettingSystem instances in each worker process rather than attempting to share state across processes. This eliminates race condition risks and ensures proper isolation.

#### 6. Good Practice: Deterministic RNG Pre-seeding

The approach of pre-generating all session seeds before parallel execution is a sound design that ensures reproducibility regardless of worker assignment. This is the correct way to handle RNG in parallel simulations.

#### 7. Good Practice: Using `frozen=True` for Dataclasses

The `WorkerTask` and `WorkerResult` dataclasses use `frozen=True`, making them immutable. This is a good security practice that prevents accidental or malicious modification of task data.

## Recommendations Summary

| Priority | Finding | Recommendation |
|----------|---------|----------------|
| Medium | Error info leakage | Log detailed errors, return generic messages |
| Medium | Unbounded worker count | Add MAX_WORKERS ceiling |
| Low | Pickle serialization | Document trust assumptions, consider JSON for future |
| Low | Seed range | Consider 64-bit seeds for enhanced entropy (optional) |

## Positive Security Observations

1. **No subprocess or shell execution**: The code uses only multiprocessing.Pool, not subprocess with shell=True
2. **No eval/exec usage**: No dynamic code execution with user input
3. **No file path manipulation**: No path traversal risks in the parallel execution code
4. **Proper input validation**: Configuration is validated via Pydantic models before reaching parallel execution
5. **Immutable task objects**: Using frozen dataclasses prevents state mutation bugs

## Conclusion

This PR introduces parallel execution in a security-conscious manner. The main recommendations are to add bounds on worker count to prevent resource exhaustion and to sanitize error messages to avoid information leakage. The pickle serialization concern is low-risk given the current architecture where all data originates from trusted internal sources.

The overall security posture of this change is **Acceptable with Minor Improvements Recommended**.
