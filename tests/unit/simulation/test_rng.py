"""Unit tests for RNG management.

Tests cover:
- RNGManager reproducibility and seed derivation
- Worker seed independence
- State serialization and restoration
- RNG quality validation
"""

from __future__ import annotations

import random

from let_it_ride.simulation.rng import (
    RNGManager,
    RNGQualityResult,
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
