"""Tests for package initialization and version."""

import let_it_ride


def test_version_exists() -> None:
    """Test that version is defined."""
    assert hasattr(let_it_ride, "__version__")
    assert let_it_ride.__version__ == "0.1.0"


def test_author_exists() -> None:
    """Test that author is defined."""
    assert hasattr(let_it_ride, "__author__")
    assert let_it_ride.__author__ == "ChrisHenryOC"
