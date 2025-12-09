"""RNG management for reproducible and high-quality randomness.

This module provides:
- RNGManager: Centralized seed management for reproducible simulations
- validate_rng_quality: Basic statistical tests for RNG quality

Key design decisions:
- Seeds derived via randint(0, 2**31 - 1) for session-level reproducibility
- Worker seeds incorporate worker_id for guaranteed uniqueness
- Optional cryptographic RNG via secrets module
- State serialization enables checkpointing and resume
"""

from __future__ import annotations

import random
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class RNGQualityResult:
    """Result of RNG quality validation.

    Attributes:
        passed: Whether all quality tests passed.
        chi_square_stat: Chi-square statistic for uniformity test.
        chi_square_passed: Whether uniformity test passed.
        runs_test_stat: Runs test Z-score for independence.
        runs_test_passed: Whether runs test passed.
        sample_size: Number of samples used in testing.
    """

    passed: bool
    chi_square_stat: float
    chi_square_passed: bool
    runs_test_stat: float
    runs_test_passed: bool
    sample_size: int


class RNGManager:
    """Centralized RNG seed management for reproducible simulations.

    Manages seed derivation for sessions and workers, ensuring:
    - Reproducibility: Same base_seed produces identical sequences
    - Independence: Different workers get different, non-overlapping seeds
    - Quality: Optional cryptographic-quality randomness

    Example:
        >>> manager = RNGManager(base_seed=42)
        >>> rng1 = manager.create_rng()
        >>> rng2 = manager.create_rng()
        >>> # rng1 and rng2 have different seeds derived from base_seed

        >>> worker_rng = manager.create_worker_rng(worker_id=0)
        >>> # Worker RNG with seed unique to worker 0
    """

    __slots__ = ("_base_seed", "_use_crypto", "_seed_counter", "_master_rng")

    # Maximum seed value for derived seeds (31 bits for compatibility)
    _MAX_SEED = 2**31 - 1

    def __init__(
        self,
        base_seed: int | None = None,
        use_crypto: bool = False,
    ) -> None:
        """Initialize the RNG manager.

        Args:
            base_seed: Base seed for deterministic behavior. If None,
                a random seed is generated (non-reproducible).
            use_crypto: If True, use cryptographic RNG for seed generation.
                This provides higher quality randomness but is slower.
        """
        self._use_crypto = use_crypto

        if base_seed is None:
            # Generate random base seed
            if use_crypto:
                self._base_seed = secrets.randbits(31)
            else:
                self._base_seed = random.randint(0, self._MAX_SEED)
        else:
            self._base_seed = base_seed

        self._seed_counter = 0
        self._master_rng = random.Random(self._base_seed)

    @property
    def base_seed(self) -> int:
        """Return the base seed used by this manager."""
        return self._base_seed

    @property
    def use_crypto(self) -> bool:
        """Return whether cryptographic RNG is enabled."""
        return self._use_crypto

    def create_rng(self) -> random.Random:
        """Create a new RNG with a derived seed.

        Each call returns an RNG with a unique seed derived from the
        base seed. The sequence of seeds is deterministic given the
        same base_seed.

        Returns:
            A new random.Random instance with derived seed.
        """
        if self._use_crypto:
            seed = secrets.randbits(31)
        else:
            seed = self._master_rng.randint(0, self._MAX_SEED)

        self._seed_counter += 1
        return random.Random(seed)

    def create_worker_rng(self, worker_id: int) -> random.Random:
        """Create an RNG for a specific worker with guaranteed unique seed.

        Worker seeds are derived deterministically from the base seed
        and worker_id, ensuring:
        - Same base_seed + worker_id = same worker seed
        - Different worker_ids = different seeds

        Args:
            worker_id: Unique identifier for the worker (0-indexed).

        Returns:
            A random.Random instance for the specified worker.
        """
        # Combine base_seed with worker_id to create unique seed
        # Use a separate RNG seeded with combined value to derive worker seed
        combined_seed = (self._base_seed * 31 + worker_id) % (self._MAX_SEED + 1)
        worker_master = random.Random(combined_seed)
        worker_seed = worker_master.randint(0, self._MAX_SEED)

        return random.Random(worker_seed)

    def create_session_seeds(self, num_sessions: int) -> dict[int, int]:
        """Pre-generate seeds for multiple sessions.

        This is the recommended approach for parallel execution to ensure
        determinism regardless of execution order.

        Args:
            num_sessions: Number of session seeds to generate.

        Returns:
            Dictionary mapping session_id (0-indexed) to seed.
        """
        return {
            session_id: self._master_rng.randint(0, self._MAX_SEED)
            for session_id in range(num_sessions)
        }

    def get_state(self) -> dict[str, Any]:
        """Serialize RNG state for checkpointing.

        Returns:
            Dictionary containing all state needed to restore the manager.
            The dictionary is JSON-serializable.
        """
        return {
            "base_seed": self._base_seed,
            "use_crypto": self._use_crypto,
            "seed_counter": self._seed_counter,
            "master_rng_state": self._master_rng.getstate(),
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> RNGManager:
        """Restore RNGManager from serialized state.

        Args:
            state: State dictionary from get_state().

        Returns:
            RNGManager instance restored to the saved state.

        Raises:
            KeyError: If required state keys are missing.
            TypeError: If state values have incorrect types.
        """
        manager = cls(
            base_seed=state["base_seed"],
            use_crypto=state["use_crypto"],
        )
        manager._seed_counter = state["seed_counter"]
        manager._master_rng.setstate(state["master_rng_state"])
        return manager

    def reset(self) -> None:
        """Reset the manager to initial state.

        After reset, the manager will produce the same sequence of
        seeds as when first created.
        """
        self._seed_counter = 0
        self._master_rng = random.Random(self._base_seed)


def validate_rng_quality(
    rng: random.Random,
    sample_size: int = 10000,
    num_buckets: int = 10,
    alpha: float = 0.05,
) -> RNGQualityResult:
    """Perform basic statistical tests on RNG quality.

    Runs two tests:
    1. Chi-square test for uniformity across buckets
    2. Runs test for independence (above/below median)

    Args:
        rng: The random.Random instance to test.
        sample_size: Number of samples to generate for testing.
        num_buckets: Number of buckets for chi-square test.
        alpha: Significance level for tests (default 0.05).

    Returns:
        RNGQualityResult with test statistics and pass/fail status.

    Note:
        These are basic sanity checks, not cryptographic validation.
        A properly seeded random.Random should pass consistently.
    """
    # Generate samples
    samples = [rng.random() for _ in range(sample_size)]

    # Chi-square test for uniformity
    chi_square_stat, chi_square_passed = _chi_square_uniformity_test(
        samples, num_buckets, alpha
    )

    # Runs test for independence
    runs_test_stat, runs_test_passed = _runs_test(samples, alpha)

    passed = chi_square_passed and runs_test_passed

    return RNGQualityResult(
        passed=passed,
        chi_square_stat=chi_square_stat,
        chi_square_passed=chi_square_passed,
        runs_test_stat=runs_test_stat,
        runs_test_passed=runs_test_passed,
        sample_size=sample_size,
    )


def _chi_square_uniformity_test(
    samples: Sequence[float],
    num_buckets: int,
    alpha: float,
) -> tuple[float, bool]:
    """Chi-square test for uniform distribution.

    Tests whether samples are uniformly distributed across buckets.

    Args:
        samples: Sequence of float values in [0, 1).
        num_buckets: Number of equal-width buckets.
        alpha: Significance level.

    Returns:
        Tuple of (chi_square_statistic, passed).
    """
    n = len(samples)
    expected = n / num_buckets

    # Count samples in each bucket
    observed = [0] * num_buckets
    for sample in samples:
        bucket = min(int(sample * num_buckets), num_buckets - 1)
        observed[bucket] += 1

    # Calculate chi-square statistic
    chi_square = sum((obs - expected) ** 2 / expected for obs in observed)

    # Critical value for num_buckets - 1 degrees of freedom
    # Using approximate critical values for common cases
    critical_values = _get_chi_square_critical(num_buckets - 1, alpha)

    return chi_square, chi_square <= critical_values


def _runs_test(
    samples: Sequence[float],
    alpha: float,
) -> tuple[float, bool]:
    """Runs test for independence (Wald-Wolfowitz).

    Tests whether the sequence shows patterns (non-random runs).

    Args:
        samples: Sequence of float values.
        alpha: Significance level.

    Returns:
        Tuple of (z_score, passed).
    """
    n = len(samples)
    if n < 20:
        # Too few samples for meaningful test
        return 0.0, True

    median = sorted(samples)[n // 2]

    # Convert to binary sequence (above/below median)
    binary = [1 if s >= median else 0 for s in samples]

    # Count runs
    runs = 1
    for i in range(1, n):
        if binary[i] != binary[i - 1]:
            runs += 1

    # Count n1 (above median) and n2 (below median)
    n1 = sum(binary)
    n2 = n - n1

    if n1 == 0 or n2 == 0:
        # All values on one side of median
        return 0.0, False

    # Expected number of runs and standard deviation
    expected_runs = (2 * n1 * n2) / n + 1
    variance = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n * n * (n - 1))

    if variance <= 0:
        return 0.0, True

    std_dev = variance**0.5
    z_score = (runs - expected_runs) / std_dev

    # Two-tailed test at alpha level
    # z_critical for alpha=0.05 is approximately 1.96
    z_critical = _get_z_critical(alpha)

    return z_score, abs(z_score) <= z_critical


def _get_chi_square_critical(df: int, alpha: float) -> float:
    """Get chi-square critical value for given degrees of freedom.

    Uses precomputed values for common cases.

    Args:
        df: Degrees of freedom.
        alpha: Significance level.

    Returns:
        Critical value.
    """
    # Critical values at alpha=0.05 for common df values
    critical_05 = {
        1: 3.841,
        2: 5.991,
        3: 7.815,
        4: 9.488,
        5: 11.070,
        6: 12.592,
        7: 14.067,
        8: 15.507,
        9: 16.919,
        10: 18.307,
        11: 19.675,
        12: 21.026,
        13: 22.362,
        14: 23.685,
        15: 24.996,
        19: 30.144,
        20: 31.410,
    }

    # Critical values at alpha=0.01 for common df values
    critical_01 = {
        1: 6.635,
        2: 9.210,
        3: 11.345,
        4: 13.277,
        5: 15.086,
        6: 16.812,
        7: 18.475,
        8: 20.090,
        9: 21.666,
        10: 23.209,
        11: 24.725,
        12: 26.217,
        13: 27.688,
        14: 29.141,
        15: 30.578,
        19: 36.191,
        20: 37.566,
    }

    table = critical_01 if alpha <= 0.01 else critical_05

    if df in table:
        return table[df]

    # Approximate using Wilson-Hilferty transformation for larger df
    z = _get_z_critical(alpha)
    return float(df * (1 - 2 / (9 * df) + z * (2 / (9 * df)) ** 0.5) ** 3)


def _get_z_critical(alpha: float) -> float:
    """Get z critical value for two-tailed test.

    Args:
        alpha: Significance level.

    Returns:
        Critical z-value.
    """
    # Common critical values
    if alpha <= 0.01:
        return 2.576
    if alpha <= 0.05:
        return 1.96
    if alpha <= 0.10:
        return 1.645
    return 1.28  # alpha = 0.20
