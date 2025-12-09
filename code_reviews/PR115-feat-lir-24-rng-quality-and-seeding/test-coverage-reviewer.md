# Test Coverage Review: PR #115 - LIR-24 RNG Quality and Seeding

## Summary

The RNG module (`src/let_it_ride/simulation/rng.py`) has comprehensive unit test coverage in `tests/unit/simulation/test_rng.py` with 455 lines of tests covering the core functionality. The test suite demonstrates good quality with clear organization, appropriate use of test classes, and strong reproducibility testing. However, there are notable gaps in edge case coverage for statistical validation functions, error handling paths, and boundary conditions that should be addressed.

## Findings by Severity

### High Priority

#### 1. Missing Tests for `from_state` Error Handling
**File:** `src/let_it_ride/simulation/rng.py:178-196`
**Issue:** The `from_state` method documents raising `KeyError` and `TypeError` for invalid state dictionaries, but no tests verify this behavior.

```python
# rng.py:186-189
"""
Raises:
    KeyError: If required state keys are missing.
    TypeError: If state values have incorrect types.
"""
```

**Recommendation:** Add tests for:
- Missing required keys (`base_seed`, `use_crypto`, `seed_counter`, `master_rng_state`)
- Invalid types for state values (e.g., string instead of int for `base_seed`)
- Empty state dictionary
- Partial state dictionary

#### 2. No Tests for `validate_rng_quality` Edge Cases
**File:** `src/let_it_ride/simulation/rng.py:209-254`
**Issue:** The `validate_rng_quality` function has multiple edge cases that lack test coverage.

**Missing test scenarios:**
- Small sample sizes (< 20 samples triggers early return in `_runs_test`)
- Custom alpha values (0.01, 0.10, 0.20)
- Boundary case where `num_buckets=1`
- Large number of buckets (e.g., 100)
- Samples exactly on bucket boundaries

#### 3. Private Helper Functions Untested
**File:** `src/let_it_ride/simulation/rng.py:257-429`
**Issue:** The private helper functions `_chi_square_uniformity_test`, `_runs_test`, `_get_chi_square_critical`, and `_get_z_critical` have no direct tests, relying solely on integration through `validate_rng_quality`.

**Key untested paths:**
- `_get_chi_square_critical` with df values not in the lookup tables (triggers Wilson-Hilferty approximation)
- `_runs_test` with exactly 20 samples (boundary)
- `_runs_test` with all values above median (n2=0, should return `(0.0, False)`)
- `_runs_test` with negative variance (should return `(0.0, True)`)

### Medium Priority

#### 4. Insufficient Coverage of Crypto Mode Behavior
**File:** `src/let_it_ride/simulation/rng.py:116-122`
**Issue:** While crypto mode is tested for basic functionality, specific behaviors are not verified.

**Missing tests:**
- Verify `secrets.randbits(31)` is called when `use_crypto=True` in `__init__` without a base_seed
- Verify `secrets.randbits(31)` is called in `create_rng()` when crypto mode is enabled
- Test that `create_worker_rng` is NOT affected by crypto mode (it uses deterministic derivation regardless)

#### 5. Missing Boundary Tests for Worker ID
**File:** `src/let_it_ride/simulation/rng.py:124-144`
**Issue:** `create_worker_rng` lacks boundary testing for worker_id values.

**Missing tests:**
- Very large worker_id values (e.g., `2**30`)
- Negative worker_id (not validated, may produce unexpected seeds)
- Zero vs non-zero worker_id collision testing

#### 6. No Property-Based Testing
**File:** `tests/unit/simulation/test_rng.py`
**Issue:** For a simulation-critical RNG module, property-based testing with hypothesis would strengthen confidence in the implementation.

**Recommendations:**
- Use hypothesis to verify seed uniqueness properties
- Generate random worker_id sequences and verify no collisions
- Property test that chi-square and runs tests pass for well-seeded RNGs

### Low Priority

#### 7. Test for `create_session_seeds` with Zero Sessions
**File:** `src/let_it_ride/simulation/rng.py:146-161`
**Issue:** No test for `create_session_seeds(0)` - should return empty dict.

#### 8. Missing Integration Test for RNG in Parallel Execution
**File:** `tests/integration/test_parallel.py`
**Issue:** While parallel reproducibility is tested, there is no test specifically verifying that RNGManager integration works correctly when restored from checkpoint during parallel execution.

#### 9. Test Assertion Specificity
**File:** `tests/unit/simulation/test_rng.py:300-303`
**Issue:** Some tests could have more specific assertions.

```python
def test_standard_rng_passes(self) -> None:
    """Standard random.Random passes quality tests."""
    rng = random.Random(42)
    result = validate_rng_quality(rng, sample_size=10000)

    assert result.passed is True
    # Could also verify chi_square_stat and runs_test_stat are within expected ranges
```

## Specific Recommendations

### 1. Add Error Handling Tests for `from_state`

```python
class TestStateSerializationErrors:
    """Test error handling in state restoration."""

    def test_from_state_missing_base_seed_raises_key_error(self) -> None:
        """from_state raises KeyError when base_seed is missing."""
        state = {
            "use_crypto": False,
            "seed_counter": 0,
            "master_rng_state": random.Random(42).getstate(),
        }
        with pytest.raises(KeyError):
            RNGManager.from_state(state)

    def test_from_state_empty_dict_raises_key_error(self) -> None:
        """from_state raises KeyError for empty state dict."""
        with pytest.raises(KeyError):
            RNGManager.from_state({})

    def test_from_state_invalid_type_raises_type_error(self) -> None:
        """from_state raises TypeError for invalid state value types."""
        state = {
            "base_seed": "not_an_int",  # Should be int
            "use_crypto": False,
            "seed_counter": 0,
            "master_rng_state": random.Random(42).getstate(),
        }
        with pytest.raises(TypeError):
            RNGManager.from_state(state)
```

### 2. Add Edge Case Tests for `validate_rng_quality`

```python
class TestValidateRNGQualityEdgeCases:
    """Test edge cases in RNG quality validation."""

    def test_small_sample_size_passes_runs_test(self) -> None:
        """Runs test passes with < 20 samples (insufficient data)."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=15)
        assert result.runs_test_passed is True
        assert result.runs_test_stat == 0.0  # Early return value

    def test_custom_alpha_values(self) -> None:
        """Test with different alpha significance levels."""
        rng = random.Random(42)
        for alpha in [0.01, 0.05, 0.10]:
            result = validate_rng_quality(rng, sample_size=5000, alpha=alpha)
            assert result.passed is True

    def test_single_bucket_chi_square(self) -> None:
        """Chi-square with single bucket should always pass."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=1000, num_buckets=1)
        assert result.chi_square_passed is True
```

### 3. Add Worker ID Boundary Tests

```python
class TestWorkerRNGBoundaries:
    """Test worker RNG with boundary values."""

    def test_large_worker_id(self) -> None:
        """Large worker_id produces valid RNG."""
        manager = RNGManager(base_seed=42)
        rng = manager.create_worker_rng(worker_id=2**30)
        assert isinstance(rng, random.Random)
        assert 0 <= rng.random() < 1

    def test_negative_worker_id(self) -> None:
        """Negative worker_id produces valid (though unusual) RNG."""
        manager = RNGManager(base_seed=42)
        rng = manager.create_worker_rng(worker_id=-1)
        # This is valid but produces potentially unexpected behavior
        assert isinstance(rng, random.Random)

    def test_adjacent_worker_ids_different(self) -> None:
        """Adjacent worker_ids produce different seeds."""
        manager = RNGManager(base_seed=42)
        rng1 = manager.create_worker_rng(worker_id=999)
        rng2 = manager.create_worker_rng(worker_id=1000)
        assert rng1.random() != rng2.random()
```

### 4. Consider Property-Based Testing

```python
from hypothesis import given, strategies as st

class TestRNGManagerProperties:
    """Property-based tests for RNGManager."""

    @given(st.integers(min_value=0, max_value=2**31-1), st.integers(min_value=1, max_value=100))
    def test_session_seeds_unique(self, base_seed: int, num_sessions: int) -> None:
        """All generated session seeds should be unique."""
        manager = RNGManager(base_seed=base_seed)
        seeds = manager.create_session_seeds(num_sessions)
        assert len(set(seeds.values())) == num_sessions

    @given(st.integers(min_value=0, max_value=2**31-1), st.lists(st.integers(min_value=0, max_value=1000), min_size=2, max_size=50, unique=True))
    def test_worker_seeds_unique(self, base_seed: int, worker_ids: list[int]) -> None:
        """Different worker_ids should produce different first random values."""
        manager = RNGManager(base_seed=base_seed)
        values = [manager.create_worker_rng(wid).random() for wid in worker_ids]
        assert len(set(values)) == len(worker_ids)
```

## Test Quality Assessment

### Strengths
1. **Clear organization**: Tests are well-organized into logical test classes
2. **Good naming**: Test names clearly describe the behavior being tested
3. **Reproducibility focus**: Strong emphasis on testing deterministic behavior
4. **Integration coverage**: The parallel tests (`test_parallel.py`) provide good integration coverage for RNG usage
5. **Bad RNG detection**: Tests for `BiasedRandom` and `PatternedRandom` verify quality validation works

### Areas for Improvement
1. **Error path coverage**: Minimal testing of error conditions and invalid inputs
2. **Boundary conditions**: Several edge cases around sample sizes, bucket counts, and IDs are untested
3. **Private function coverage**: Helper functions rely on integration testing only
4. **Statistical test accuracy**: No tests verify the statistical correctness of chi-square/runs test implementations
5. **Mock usage**: Could use mocks for `secrets` module to test crypto path deterministically

## Summary Statistics

| Metric | Value |
|--------|-------|
| Production Lines (rng.py) | ~430 |
| Test Lines (test_rng.py) | ~455 |
| Test:Code Ratio | ~1.06:1 |
| Test Classes | 11 |
| Individual Tests | 35 |
| Estimated Line Coverage | ~85% |
| Branch Coverage (estimated) | ~70% |

## Conclusion

The test suite provides solid coverage of the happy path and core functionality. The primary gaps are in error handling, boundary conditions, and edge cases for the statistical validation functions. Adding the recommended tests would bring estimated branch coverage to 90%+ and provide stronger guarantees for this simulation-critical module.
