# Security Code Review: PR #115 - LIR-24 RNG Quality and Seeding

**Reviewer:** Security Code Reviewer
**Date:** 2025-12-09
**PR:** #115 (feat: LIR-24 RNG Quality and Seeding)

## Summary

This PR introduces an `RNGManager` class for centralized random number generation and seed management with optional cryptographic seed generation. The implementation is appropriate for a poker simulation where statistical quality matters more than cryptographic security. Two medium-severity findings exist regarding input validation and documentation clarity, plus several low-severity items for defense-in-depth.

## Findings by Severity

### Critical

None.

### High

None.

### Medium

#### M1: Insufficient Input Validation in `from_state()` (CWE-20)

**Location:** `src/let_it_ride/simulation/rng.py:177-197`

**Description:** The `from_state()` class method deserializes state from a dictionary without validating the types or ranges of input values. While the docstring mentions `KeyError` and `TypeError` exceptions, malicious or corrupted state data could cause unexpected behavior.

**Code:**
```python
@classmethod
def from_state(cls, state: dict[str, Any]) -> RNGManager:
    manager = cls(
        base_seed=state["base_seed"],
        use_crypto=state["use_crypto"],
    )
    manager._seed_counter = state["seed_counter"]
    manager._master_rng.setstate(state["master_rng_state"])  # Direct setstate without validation
    return manager
```

**Impact:** If state data comes from an untrusted source (e.g., a checkpoint file that could be tampered with), invalid values could:
- Cause integer overflow with extremely large `seed_counter` values
- Corrupt RNG state via malformed `master_rng_state` tuple
- Lead to denial of service or undefined behavior

**Remediation:** Add explicit validation before restoring state:

```python
@classmethod
def from_state(cls, state: dict[str, Any]) -> RNGManager:
    # Validate required keys exist
    required = {"base_seed", "use_crypto", "seed_counter", "master_rng_state"}
    if not required.issubset(state.keys()):
        raise ValueError(f"State missing required keys: {required - state.keys()}")

    # Validate types and ranges
    if not isinstance(state["base_seed"], int):
        raise TypeError("base_seed must be an integer")
    if not (0 <= state["base_seed"] <= cls._MAX_SEED):
        raise ValueError(f"base_seed must be between 0 and {cls._MAX_SEED}")
    if not isinstance(state["use_crypto"], bool):
        raise TypeError("use_crypto must be a boolean")
    if not isinstance(state["seed_counter"], int) or state["seed_counter"] < 0:
        raise ValueError("seed_counter must be a non-negative integer")
    if not isinstance(state["master_rng_state"], tuple):
        raise TypeError("master_rng_state must be a tuple")

    manager = cls(
        base_seed=state["base_seed"],
        use_crypto=state["use_crypto"],
    )
    manager._seed_counter = state["seed_counter"]
    manager._master_rng.setstate(state["master_rng_state"])
    return manager
```

**References:** CWE-20 (Improper Input Validation)

---

#### M2: Cryptographic RNG Mode Does Not Provide Full Cryptographic Guarantees

**Location:** `src/let_it_ride/simulation/rng.py:116-122`

**Description:** When `use_crypto=True`, the `create_rng()` method uses `secrets.randbits(31)` to generate a seed, but then passes that seed to `random.Random()`. The resulting RNG instance is NOT cryptographically secure - it merely has a cryptographically-generated seed. The Mersenne Twister PRNG used by `random.Random` is deterministic and predictable once any portion of its internal state is known.

**Code:**
```python
def create_rng(self) -> random.Random:
    if self._use_crypto:
        seed = secrets.randbits(31)
    else:
        seed = self._master_rng.randint(0, self._MAX_SEED)

    self._seed_counter += 1
    return random.Random(seed)  # NOT cryptographically secure
```

**Impact:** Users enabling `use_crypto=True` might incorrectly assume the returned RNG provides cryptographic-level randomness. For this poker simulator, this is acceptable since cryptographic security is not required. However, the naming and documentation could mislead future developers.

**Remediation:** The docstring at lines 78-80 notes "higher quality randomness" which is appropriate. Consider adding a more explicit warning:

```python
"""
Note: use_crypto=True provides cryptographic-quality seed generation,
but the returned random.Random instances use Mersenne Twister and are
NOT suitable for cryptographic purposes. This option is useful for
non-reproducible simulations with higher-entropy seeds.
"""
```

**References:** CWE-338 (Use of Cryptographically Weak Pseudo-Random Number Generator)

---

### Low

#### L1: No Bounds Checking on `worker_id` Parameter (CWE-20)

**Location:** `src/let_it_ride/simulation/rng.py:124-144`

**Description:** The `create_worker_rng()` method accepts any integer `worker_id` without validation. While negative values or extremely large values will produce valid seeds due to the modulo operation, this could mask bugs in calling code.

**Code:**
```python
def create_worker_rng(self, worker_id: int) -> random.Random:
    combined_seed = (self._base_seed * 31 + worker_id) % (self._MAX_SEED + 1)
    # ...
```

**Impact:** Low - negative worker IDs could indicate bugs in calling code that go undetected. No security vulnerability, but defense-in-depth suggests validation.

**Remediation:** Consider adding a bounds check:
```python
def create_worker_rng(self, worker_id: int) -> random.Random:
    if worker_id < 0:
        raise ValueError(f"worker_id must be non-negative, got {worker_id}")
    # ... rest of implementation
```

**References:** CWE-20 (Improper Input Validation)

---

#### L2: No Bounds Checking on `num_sessions` Parameter (CWE-789)

**Location:** `src/let_it_ride/simulation/rng.py:146-161`

**Description:** The `create_session_seeds()` method accepts `num_sessions` without validation. A very large value could cause excessive memory allocation.

**Code:**
```python
def create_session_seeds(self, num_sessions: int) -> dict[int, int]:
    return {
        session_id: self._master_rng.randint(0, self._MAX_SEED)
        for session_id in range(num_sessions)
    }
```

**Impact:** Low - calling code would likely fail elsewhere first, but a malformed configuration could potentially cause memory exhaustion.

**Remediation:** Add a reasonable upper bound or validation:
```python
def create_session_seeds(self, num_sessions: int) -> dict[int, int]:
    if num_sessions < 0:
        raise ValueError("num_sessions must be non-negative")
    # ... rest of implementation
```

**References:** CWE-789 (Memory Allocation with Excessive Size Value)

---

#### L3: Resource Consumption in `validate_rng_quality()` (CWE-400)

**Location:** `src/let_it_ride/simulation/rng.py:209-235`

**Description:** The `validate_rng_quality()` function accepts an unbounded `sample_size` parameter. A very large value could cause excessive CPU and memory usage.

**Code:**
```python
def validate_rng_quality(
    rng: random.Random,
    sample_size: int = 10000,
    # ...
) -> RNGQualityResult:
    samples = [rng.random() for _ in range(sample_size)]  # Unbounded allocation
```

**Impact:** Low - primarily an availability concern. Very large sample sizes (e.g., billions) would consume excessive memory.

**Remediation:** Add an upper bound:
```python
_MAX_SAMPLE_SIZE = 10_000_000  # 10M should be sufficient for any quality test

def validate_rng_quality(
    rng: random.Random,
    sample_size: int = 10000,
    # ...
) -> RNGQualityResult:
    if sample_size < 1 or sample_size > _MAX_SAMPLE_SIZE:
        raise ValueError(f"sample_size must be between 1 and {_MAX_SAMPLE_SIZE}")
    # ... rest of implementation
```

**References:** CWE-400 (Uncontrolled Resource Consumption)

---

### Informational

#### I1: Appropriate Use of Non-Cryptographic RNG

**Observation:** The implementation correctly uses Python's `random.Random` (Mersenne Twister) for simulation purposes. This is appropriate because:
- The poker simulator requires statistical quality, not cryptographic security
- Reproducibility via seeding is a feature requirement
- Performance is important (100,000+ hands/second target)

The optional `use_crypto=True` mode using the `secrets` module is a good addition for scenarios where non-reproducible randomness is desired.

#### I2: Seed Space Considerations

**Location:** `src/let_it_ride/simulation/rng.py:67`

**Observation:** The implementation uses 31-bit seeds (`2**31 - 1`). This provides approximately 2.1 billion unique seeds, which is sufficient for the simulation's requirements. For very large simulations (>100M sessions), the Birthday Paradox suggests collision probability approaches 0.2%, which may be acceptable depending on use case.

#### I3: State Serialization Contains RNG Internal State

**Location:** `src/let_it_ride/simulation/rng.py:163-175`

**Observation:** The `get_state()` method exposes the internal Mersenne Twister state via `random.Random.getstate()`. This is intentional for checkpointing but should not be logged or exposed externally, as it would allow prediction of future random values.

---

## Positive Security Practices Observed

1. **No use of dangerous functions:** The code does not use `eval()`, `exec()`, `pickle`, or `subprocess` with untrusted input.

2. **Frozen dataclass:** `RNGQualityResult` uses `frozen=True` and `slots=True`, preventing accidental mutation.

3. **Type hints throughout:** Full type annotations improve code clarity and catch errors early.

4. **Clear separation of concerns:** The cryptographic seed generation is isolated to specific code paths.

5. **No external network calls:** The module is entirely self-contained with no network or file I/O.

6. **No path traversal risk:** The module does not perform any file operations.

7. **Use of `__slots__`:** Both `RNGQualityResult` and `RNGManager` use slots, reducing memory footprint.

---

## Recommendations Summary

| Priority | Issue | File:Line | Action |
|----------|-------|-----------|--------|
| Medium | Add validation to `from_state()` | rng.py:177-197 | Validate types, ranges, and structure |
| Medium | Clarify crypto mode limitations | rng.py:78-80 | Add explicit docstring warning |
| Low | Validate `worker_id` bounds | rng.py:124 | Add non-negative check |
| Low | Validate `num_sessions` bounds | rng.py:146 | Add non-negative check |
| Low | Limit `sample_size` in quality validation | rng.py:209 | Add maximum bound |

---

## Conclusion

The RNG implementation is well-designed for its intended purpose (poker simulation). The medium-severity findings should be considered for defense-in-depth, particularly the input validation in `from_state()` if checkpoint files could ever come from untrusted sources. The low-severity items would improve code robustness but are not blocking issues.

**Review Status:** Approved with minor recommendations
