"""Unit tests for RNG management.

Tests cover:
- RNGManager reproducibility and seed derivation
- Worker seed independence
- State serialization and restoration
- RNG quality validation
"""

from __future__ import annotations

import random

import pytest

from let_it_ride.simulation.rng import (
    RNGManager,
    RNGQualityResult,
    _chi_square_uniformity_test,
    _get_chi_square_critical,
    _get_z_critical,
    _runs_test,
    validate_rng_quality,
)


class TestRNGManagerBasics:
    """Test basic RNGManager functionality."""

    def test_init_with_seed(self) -> None:
        """RNGManager can be initialized with a base seed."""
        manager = RNGManager(base_seed=42)
        assert manager.base_seed == 42
        assert manager.use_crypto is False

    def test_init_without_seed_generates_random(self) -> None:
        """RNGManager generates a random seed when none provided."""
        manager = RNGManager()
        assert isinstance(manager.base_seed, int)
        assert 0 <= manager.base_seed <= 2**31 - 1

    def test_init_with_crypto_flag(self) -> None:
        """RNGManager respects use_crypto flag."""
        manager = RNGManager(base_seed=42, use_crypto=True)
        assert manager.use_crypto is True

    def test_create_rng_returns_random_instance(self) -> None:
        """create_rng returns a random.Random instance."""
        manager = RNGManager(base_seed=42)
        rng = manager.create_rng()
        assert isinstance(rng, random.Random)

    def test_create_rng_returns_different_instances(self) -> None:
        """Each call to create_rng returns a different RNG."""
        manager = RNGManager(base_seed=42)
        rng1 = manager.create_rng()
        rng2 = manager.create_rng()

        # Generate values from each
        val1 = rng1.random()
        val2 = rng2.random()

        # Values should differ because seeds differ
        assert val1 != val2

    def test_reset_restores_initial_state(self) -> None:
        """reset() restores the manager to initial state."""
        manager = RNGManager(base_seed=42)

        # Generate some RNGs
        seeds_before = [manager.create_rng().random() for _ in range(5)]

        # Reset
        manager.reset()

        # Generate again - should produce same sequence
        seeds_after = [manager.create_rng().random() for _ in range(5)]

        assert seeds_before == seeds_after


class TestRNGManagerReproducibility:
    """Test reproducibility guarantees."""

    def test_same_seed_produces_same_sequence(self) -> None:
        """Same base_seed produces identical RNG sequences."""
        manager1 = RNGManager(base_seed=42)
        manager2 = RNGManager(base_seed=42)

        # Create 10 RNGs from each and verify identical sequences
        for _ in range(10):
            rng1 = manager1.create_rng()
            rng2 = manager2.create_rng()

            # First value from each RNG should match
            assert rng1.random() == rng2.random()

    def test_different_seeds_produce_different_sequences(self) -> None:
        """Different base_seeds produce different RNG sequences."""
        manager1 = RNGManager(base_seed=42)
        manager2 = RNGManager(base_seed=43)

        rng1 = manager1.create_rng()
        rng2 = manager2.create_rng()

        # First values should differ
        assert rng1.random() != rng2.random()

    def test_create_session_seeds_reproducible(self) -> None:
        """create_session_seeds produces reproducible results."""
        manager1 = RNGManager(base_seed=42)
        manager2 = RNGManager(base_seed=42)

        seeds1 = manager1.create_session_seeds(100)
        seeds2 = manager2.create_session_seeds(100)

        assert seeds1 == seeds2

    def test_create_session_seeds_coverage(self) -> None:
        """create_session_seeds returns expected number of seeds."""
        manager = RNGManager(base_seed=42)
        seeds = manager.create_session_seeds(50)

        assert len(seeds) == 50
        assert all(0 <= seed <= 2**31 - 1 for seed in seeds.values())
        assert list(seeds.keys()) == list(range(50))


class TestWorkerRNGIndependence:
    """Test worker RNG seed independence."""

    def test_worker_rng_reproducible_with_same_id(self) -> None:
        """Same base_seed + worker_id produces same RNG."""
        manager1 = RNGManager(base_seed=42)
        manager2 = RNGManager(base_seed=42)

        rng1 = manager1.create_worker_rng(worker_id=0)
        rng2 = manager2.create_worker_rng(worker_id=0)

        # Should produce identical values
        assert rng1.random() == rng2.random()
        assert rng1.random() == rng2.random()

    def test_different_worker_ids_produce_different_rngs(self) -> None:
        """Different worker_ids produce different RNGs."""
        manager = RNGManager(base_seed=42)

        rng0 = manager.create_worker_rng(worker_id=0)
        rng1 = manager.create_worker_rng(worker_id=1)
        rng2 = manager.create_worker_rng(worker_id=2)

        # Collect first values
        vals = [rng0.random(), rng1.random(), rng2.random()]

        # All should be different
        assert len(set(vals)) == 3

    def test_worker_rng_independent_of_create_rng_calls(self) -> None:
        """Worker RNG is independent of prior create_rng calls."""
        manager1 = RNGManager(base_seed=42)
        manager2 = RNGManager(base_seed=42)

        # Advance manager1's counter
        for _ in range(10):
            manager1.create_rng()

        # Worker RNGs should still match
        rng1 = manager1.create_worker_rng(worker_id=5)
        rng2 = manager2.create_worker_rng(worker_id=5)

        assert rng1.random() == rng2.random()

    def test_many_workers_all_unique(self) -> None:
        """Large number of workers all get unique seeds."""
        manager = RNGManager(base_seed=42)

        # Create 100 worker RNGs
        first_values = []
        for worker_id in range(100):
            rng = manager.create_worker_rng(worker_id)
            first_values.append(rng.random())

        # All first values should be unique
        assert len(set(first_values)) == 100


class TestStateSerializationDeserialization:
    """Test RNG state serialization and restoration."""

    def test_get_state_returns_serializable_dict(self) -> None:
        """get_state returns a dictionary with expected keys."""
        manager = RNGManager(base_seed=42)
        state = manager.get_state()

        assert isinstance(state, dict)
        assert "base_seed" in state
        assert "use_crypto" in state
        assert "seed_counter" in state
        assert "master_rng_state" in state

    def test_from_state_restores_manager(self) -> None:
        """from_state restores manager to exact state."""
        manager = RNGManager(base_seed=42)

        # Advance state
        for _ in range(5):
            manager.create_rng()

        # Save state
        state = manager.get_state()

        # Generate more values
        expected_values = [manager.create_rng().random() for _ in range(5)]

        # Restore to saved state
        restored = RNGManager.from_state(state)

        # Should produce same values
        restored_values = [restored.create_rng().random() for _ in range(5)]

        assert expected_values == restored_values

    def test_state_roundtrip_preserves_base_seed(self) -> None:
        """State roundtrip preserves base_seed."""
        manager = RNGManager(base_seed=12345)
        state = manager.get_state()
        restored = RNGManager.from_state(state)

        assert restored.base_seed == 12345

    def test_state_roundtrip_preserves_crypto_flag(self) -> None:
        """State roundtrip preserves use_crypto flag."""
        manager = RNGManager(base_seed=42, use_crypto=True)
        state = manager.get_state()
        restored = RNGManager.from_state(state)

        assert restored.use_crypto is True

    def test_state_roundtrip_preserves_counter(self) -> None:
        """State roundtrip preserves internal counter."""
        manager = RNGManager(base_seed=42)

        # Create some RNGs to advance counter
        for _ in range(7):
            manager.create_rng()

        state = manager.get_state()
        assert state["seed_counter"] == 7

        restored = RNGManager.from_state(state)
        # Counter should be preserved (accessible via state)
        assert restored.get_state()["seed_counter"] == 7


class TestCryptoRNG:
    """Test cryptographic RNG option."""

    def test_crypto_rng_generates_values(self) -> None:
        """Crypto RNG mode still produces valid RNGs."""
        manager = RNGManager(use_crypto=True)
        rng = manager.create_rng()

        # Should produce values in [0, 1)
        val = rng.random()
        assert 0 <= val < 1

    def test_crypto_rng_different_seeds_each_call(self) -> None:
        """Crypto mode produces different seeds each call."""
        manager = RNGManager(use_crypto=True)

        values = []
        for _ in range(10):
            rng = manager.create_rng()
            values.append(rng.random())

        # All should be different (very high probability)
        assert len(set(values)) == 10

    def test_crypto_rng_not_reproducible(self) -> None:
        """Crypto mode is not reproducible even with same base_seed."""
        manager1 = RNGManager(base_seed=42, use_crypto=True)
        manager2 = RNGManager(base_seed=42, use_crypto=True)

        rng1 = manager1.create_rng()
        rng2 = manager2.create_rng()

        # Should differ because crypto seeds are random
        # (This test has infinitesimal probability of false failure)
        assert rng1.random() != rng2.random()


class TestValidateRNGQuality:
    """Test RNG quality validation function."""

    def test_returns_quality_result(self) -> None:
        """validate_rng_quality returns RNGQualityResult."""
        rng = random.Random(42)
        result = validate_rng_quality(rng)

        assert isinstance(result, RNGQualityResult)

    def test_standard_rng_passes(self) -> None:
        """Standard random.Random passes quality tests."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=10000)

        assert result.passed is True
        assert result.chi_square_passed is True
        assert result.runs_test_passed is True

    def test_result_contains_statistics(self) -> None:
        """Result contains test statistics."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=5000)

        assert isinstance(result.chi_square_stat, float)
        assert isinstance(result.runs_test_stat, float)
        assert result.sample_size == 5000

    def test_different_seeds_all_pass(self) -> None:
        """Various seeds all produce passing results."""
        for seed in [1, 42, 12345, 999999]:
            rng = random.Random(seed)
            result = validate_rng_quality(rng, sample_size=5000)
            assert result.passed is True, f"Seed {seed} failed quality test"

    def test_larger_sample_size_more_accurate(self) -> None:
        """Larger sample sizes produce valid results."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=50000)

        assert result.passed is True
        assert result.sample_size == 50000

    def test_custom_num_buckets(self) -> None:
        """Custom bucket count works correctly."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=10000, num_buckets=20)

        assert result.passed is True


class TestRNGQualityWithBadRNG:
    """Test that quality validation detects poor RNG patterns."""

    def test_detects_biased_rng(self) -> None:
        """Quality test detects heavily biased distribution."""

        class BiasedRandom(random.Random):
            """RNG that produces biased values."""

            def random(self) -> float:
                # Always return values in [0, 0.3)
                return super().random() * 0.3

        rng = BiasedRandom(42)
        result = validate_rng_quality(rng, sample_size=10000)

        # Chi-square should fail due to non-uniform distribution
        assert result.chi_square_passed is False

    def test_detects_patterned_rng(self) -> None:
        """Quality test detects patterned sequences."""

        class PatternedRandom(random.Random):
            """RNG that produces alternating high/low values."""

            def __init__(self, seed: int) -> None:
                super().__init__(seed)
                self._counter = 0

            def random(self) -> float:
                self._counter += 1
                # Alternate between high and low values
                if self._counter % 2 == 0:
                    return 0.25
                return 0.75

        rng = PatternedRandom(42)
        result = validate_rng_quality(rng, sample_size=10000)

        # Should fail chi-square (only 2 values) or runs test (alternating)
        assert result.passed is False


class TestRNGManagerIntegration:
    """Integration tests for RNGManager with simulation-like usage."""

    def test_parallel_simulation_pattern(self) -> None:
        """Test pattern used in parallel simulation."""
        base_seed = 42
        num_sessions = 100
        num_workers = 4

        # Create manager and pre-generate all session seeds
        manager = RNGManager(base_seed=base_seed)
        session_seeds = manager.create_session_seeds(num_sessions)

        # Simulate worker execution (out of order)
        worker_results: dict[int, list[float]] = {}

        for worker_id in range(num_workers):
            start = worker_id * 25
            end = start + 25

            for session_id in range(start, end):
                seed = session_seeds[session_id]
                session_rng = random.Random(seed)
                first_val = session_rng.random()

                if worker_id not in worker_results:
                    worker_results[worker_id] = []
                worker_results[worker_id].append(first_val)

        # Verify reproducibility by recreating
        manager2 = RNGManager(base_seed=base_seed)
        session_seeds2 = manager2.create_session_seeds(num_sessions)

        # Run "workers" in different order
        for worker_id in [3, 1, 0, 2]:  # Different order
            start = worker_id * 25
            end = start + 25

            for i, session_id in enumerate(range(start, end)):
                seed = session_seeds2[session_id]
                session_rng = random.Random(seed)
                first_val = session_rng.random()

                # Should match regardless of execution order
                assert first_val == worker_results[worker_id][i]

    def test_checkpoint_resume_pattern(self) -> None:
        """Test checkpoint and resume pattern."""
        manager = RNGManager(base_seed=42)

        # Run first half of "simulation"
        first_half_values = []
        for _ in range(50):
            rng = manager.create_rng()
            first_half_values.append(rng.random())

        # Checkpoint
        checkpoint = manager.get_state()

        # Continue simulation
        second_half_values = []
        for _ in range(50):
            rng = manager.create_rng()
            second_half_values.append(rng.random())

        # Restore from checkpoint
        restored = RNGManager.from_state(checkpoint)

        # Should produce same second half
        restored_second_half = []
        for _ in range(50):
            rng = restored.create_rng()
            restored_second_half.append(rng.random())

        assert second_half_values == restored_second_half


class TestFromStateValidation:
    """Test error handling in from_state()."""

    def test_from_state_missing_key_raises_key_error(self) -> None:
        """from_state raises KeyError when required keys are missing."""
        # Missing base_seed
        state = {
            "use_crypto": False,
            "seed_counter": 0,
            "master_rng_state": random.Random(42).getstate(),
        }
        with pytest.raises(KeyError, match="base_seed"):
            RNGManager.from_state(state)

    def test_from_state_empty_dict_raises_key_error(self) -> None:
        """from_state raises KeyError for empty state dict."""
        with pytest.raises(KeyError):
            RNGManager.from_state({})

    def test_from_state_invalid_base_seed_type_raises_type_error(self) -> None:
        """from_state raises TypeError for invalid base_seed type."""
        state = {
            "base_seed": "not_an_int",
            "use_crypto": False,
            "seed_counter": 0,
            "master_rng_state": random.Random(42).getstate(),
        }
        with pytest.raises(TypeError, match="base_seed must be an int"):
            RNGManager.from_state(state)

    def test_from_state_invalid_use_crypto_type_raises_type_error(self) -> None:
        """from_state raises TypeError for invalid use_crypto type."""
        state = {
            "base_seed": 42,
            "use_crypto": "not_a_bool",
            "seed_counter": 0,
            "master_rng_state": random.Random(42).getstate(),
        }
        with pytest.raises(TypeError, match="use_crypto must be a bool"):
            RNGManager.from_state(state)

    def test_from_state_invalid_seed_counter_type_raises_type_error(self) -> None:
        """from_state raises TypeError for invalid seed_counter type."""
        state = {
            "base_seed": 42,
            "use_crypto": False,
            "seed_counter": "not_an_int",
            "master_rng_state": random.Random(42).getstate(),
        }
        with pytest.raises(TypeError, match="seed_counter must be an int"):
            RNGManager.from_state(state)

    def test_from_state_invalid_master_rng_state_type_raises_type_error(self) -> None:
        """from_state raises TypeError for invalid master_rng_state type."""
        state = {
            "base_seed": 42,
            "use_crypto": False,
            "seed_counter": 0,
            "master_rng_state": "not_a_tuple",
        }
        with pytest.raises(TypeError, match="master_rng_state must be a tuple"):
            RNGManager.from_state(state)

    def test_from_state_base_seed_out_of_range_raises_value_error(self) -> None:
        """from_state raises ValueError for out-of-range base_seed."""
        state = {
            "base_seed": -1,
            "use_crypto": False,
            "seed_counter": 0,
            "master_rng_state": random.Random(42).getstate(),
        }
        with pytest.raises(ValueError, match="base_seed must be between"):
            RNGManager.from_state(state)

    def test_from_state_negative_seed_counter_raises_value_error(self) -> None:
        """from_state raises ValueError for negative seed_counter."""
        state = {
            "base_seed": 42,
            "use_crypto": False,
            "seed_counter": -1,
            "master_rng_state": random.Random(42).getstate(),
        }
        with pytest.raises(ValueError, match="seed_counter must be non-negative"):
            RNGManager.from_state(state)


class TestWorkerRNGBoundaries:
    """Test worker RNG with boundary values."""

    def test_large_worker_id_produces_valid_rng(self) -> None:
        """Large worker_id produces valid RNG."""
        manager = RNGManager(base_seed=42)
        rng = manager.create_worker_rng(worker_id=2**20)
        assert isinstance(rng, random.Random)
        assert 0 <= rng.random() < 1

    def test_negative_worker_id_raises_value_error(self) -> None:
        """Negative worker_id raises ValueError."""
        manager = RNGManager(base_seed=42)
        with pytest.raises(ValueError, match="worker_id must be non-negative"):
            manager.create_worker_rng(worker_id=-1)

    def test_zero_worker_id_works(self) -> None:
        """Worker ID 0 works correctly."""
        manager = RNGManager(base_seed=42)
        rng = manager.create_worker_rng(worker_id=0)
        assert isinstance(rng, random.Random)

    def test_adjacent_worker_ids_produce_different_rngs(self) -> None:
        """Adjacent worker_ids produce different first values."""
        manager = RNGManager(base_seed=42)
        rng1 = manager.create_worker_rng(worker_id=999)
        rng2 = manager.create_worker_rng(worker_id=1000)
        assert rng1.random() != rng2.random()


class TestValidateRNGQualityEdgeCases:
    """Test edge cases in RNG quality validation."""

    def test_small_sample_size_passes_runs_test(self) -> None:
        """Runs test passes with < 20 samples (insufficient data)."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=15)
        # Runs test returns (0.0, True) for n < 20
        assert result.runs_test_passed is True

    def test_custom_alpha_value_0_01(self) -> None:
        """Test with alpha=0.01 significance level."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=5000, alpha=0.01)
        assert result.passed is True

    def test_custom_alpha_value_0_10(self) -> None:
        """Test with alpha=0.10 significance level."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=5000, alpha=0.10)
        assert result.passed is True

    def test_many_buckets(self) -> None:
        """Test with larger number of buckets."""
        rng = random.Random(42)
        result = validate_rng_quality(rng, sample_size=10000, num_buckets=50)
        assert result.passed is True


class TestCryptoRNGBehavior:
    """Test specific crypto mode behaviors."""

    def test_crypto_mode_init_without_base_seed_uses_secrets(self) -> None:
        """Crypto mode with no base_seed generates using secrets."""
        # Can't directly test secrets.randbits is called, but can verify
        # that two managers get different base seeds
        manager1 = RNGManager(use_crypto=True)
        manager2 = RNGManager(use_crypto=True)

        # Very unlikely to be equal if using cryptographic randomness
        assert manager1.base_seed != manager2.base_seed

    def test_worker_rng_deterministic_regardless_of_crypto_mode(self) -> None:
        """Worker RNGs are deterministic even when crypto mode is enabled."""
        # Worker RNG derivation is based on base_seed, not crypto
        manager1 = RNGManager(base_seed=42, use_crypto=True)
        manager2 = RNGManager(base_seed=42, use_crypto=True)

        rng1 = manager1.create_worker_rng(worker_id=5)
        rng2 = manager2.create_worker_rng(worker_id=5)

        # Worker RNGs should be identical despite crypto mode
        assert rng1.random() == rng2.random()


class TestChiSquareUniformityTest:
    """Direct tests for _chi_square_uniformity_test helper function."""

    def test_uniform_samples_pass(self) -> None:
        """Uniform distribution passes chi-square test."""
        # Generate samples uniformly distributed across buckets
        rng = random.Random(42)
        samples = [rng.random() for _ in range(10000)]

        stat, passed = _chi_square_uniformity_test(samples, num_buckets=10, alpha=0.05)

        assert passed is True
        assert isinstance(stat, float)
        assert stat >= 0  # Chi-square is always non-negative

    def test_heavily_skewed_samples_fail(self) -> None:
        """Non-uniform distribution fails chi-square test."""
        # All samples in first bucket
        samples = [0.05] * 1000

        stat, passed = _chi_square_uniformity_test(samples, num_buckets=10, alpha=0.05)

        assert passed is False
        assert stat > 100  # Very high chi-square for completely skewed data

    def test_two_buckets_uniform(self) -> None:
        """Two buckets with uniform distribution passes."""
        # Half in each bucket
        samples = [0.25] * 500 + [0.75] * 500

        stat, passed = _chi_square_uniformity_test(samples, num_buckets=2, alpha=0.05)

        assert passed is True
        assert stat == 0.0  # Perfect 50/50 split

    def test_boundary_sample_handled_correctly(self) -> None:
        """Sample value 1.0 (edge case) maps to last bucket."""
        # Values at exactly 1.0 should go to last bucket (index num_buckets-1)
        samples = [0.999999] * 100

        stat, passed = _chi_square_uniformity_test(samples, num_buckets=10, alpha=0.05)

        # All in last bucket - should fail uniformity
        assert passed is False


class TestRunsTest:
    """Direct tests for _runs_test helper function."""

    def test_too_few_samples_returns_early(self) -> None:
        """Runs test returns (0.0, True) for n < 20."""
        samples = [0.1, 0.2, 0.3, 0.4, 0.5]  # Only 5 samples

        z_score, passed = _runs_test(samples, alpha=0.05)

        assert z_score == 0.0
        assert passed is True

    def test_exactly_20_samples_runs_test(self) -> None:
        """Runs test executes with exactly 20 samples."""
        rng = random.Random(42)
        samples = [rng.random() for _ in range(20)]

        z_score, passed = _runs_test(samples, alpha=0.05)

        assert isinstance(z_score, float)
        assert isinstance(passed, bool)

    def test_all_same_value_fails(self) -> None:
        """All identical values fail (all on one side of median)."""
        samples = [0.5] * 100

        z_score, passed = _runs_test(samples, alpha=0.05)

        # All values equal median, so n2 = 0
        assert z_score == 0.0
        assert passed is False

    def test_alternating_pattern_detected(self) -> None:
        """Perfectly alternating pattern has many runs."""
        # Alternating high/low values - too many runs indicates pattern
        samples = [0.25 if i % 2 == 0 else 0.75 for i in range(100)]

        z_score, passed = _runs_test(samples, alpha=0.05)

        # Alternating pattern creates excessive runs
        # z_score should be very high (positive)
        assert abs(z_score) > 1.96  # Beyond 95% confidence interval
        assert passed is False

    def test_uniform_random_passes(self) -> None:
        """Properly random sequence passes runs test."""
        rng = random.Random(42)
        samples = [rng.random() for _ in range(1000)]

        z_score, passed = _runs_test(samples, alpha=0.05)

        assert passed is True
        assert abs(z_score) <= 1.96


class TestGetChiSquareCritical:
    """Direct tests for _get_chi_square_critical helper function."""

    def test_table_lookup_df_9(self) -> None:
        """Known critical value from table for df=9, alpha=0.05."""
        critical = _get_chi_square_critical(df=9, alpha=0.05)
        assert critical == 16.919

    def test_table_lookup_df_9_alpha_01(self) -> None:
        """Known critical value from table for df=9, alpha=0.01."""
        critical = _get_chi_square_critical(df=9, alpha=0.01)
        assert critical == 21.666

    def test_wilson_hilferty_approximation_large_df(self) -> None:
        """Wilson-Hilferty approximation used for df not in table."""
        # df=50 is not in the lookup table
        critical = _get_chi_square_critical(df=50, alpha=0.05)

        # Wilson-Hilferty approximation - verify it returns a reasonable value
        # Expected chi-square(50, 0.05) ~ 67.5-72
        assert 65 < critical < 75
        assert isinstance(critical, float)

    def test_wilson_hilferty_approximation_df_100(self) -> None:
        """Wilson-Hilferty for large df=100."""
        critical = _get_chi_square_critical(df=100, alpha=0.05)

        # Expected ~ 124
        assert 120 < critical < 130


class TestGetZCritical:
    """Direct tests for _get_z_critical helper function."""

    def test_alpha_0_01(self) -> None:
        """Z critical for alpha=0.01 is 2.576."""
        assert _get_z_critical(0.01) == 2.576

    def test_alpha_0_05(self) -> None:
        """Z critical for alpha=0.05 is 1.96."""
        assert _get_z_critical(0.05) == 1.96

    def test_alpha_0_10(self) -> None:
        """Z critical for alpha=0.10 is 1.645."""
        assert _get_z_critical(0.10) == 1.645

    def test_alpha_0_20(self) -> None:
        """Z critical for alpha=0.20 is 1.28."""
        assert _get_z_critical(0.20) == 1.28

    def test_alpha_between_01_and_05(self) -> None:
        """Alpha between 0.01 and 0.05 uses 0.05 threshold (1.96)."""
        assert _get_z_critical(0.03) == 1.96

    def test_alpha_very_small(self) -> None:
        """Very small alpha uses 0.01 threshold (2.576)."""
        assert _get_z_critical(0.001) == 2.576
