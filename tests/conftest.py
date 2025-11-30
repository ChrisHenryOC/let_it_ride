"""Pytest configuration and shared fixtures.

This module contains shared fixtures and configuration for all tests.
"""

import random

import pytest


@pytest.fixture
def rng() -> random.Random:
    """Provide a seeded random number generator for reproducible tests."""
    return random.Random(42)


@pytest.fixture
def sample_seed() -> int:
    """Provide a consistent seed for reproducible tests."""
    return 42
