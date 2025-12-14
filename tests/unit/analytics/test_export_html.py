"""Unit tests for HTML export helper functions."""

from let_it_ride.analytics.export_html import (
    _format_currency,
    _format_number,
    _format_percentage,
)


class TestFormatNumber:
    """Tests for _format_number helper function."""

    def test_basic_formatting(self) -> None:
        """Verify basic number formatting with default decimals."""
        assert _format_number(1234.567) == "1,234.57"

    def test_zero(self) -> None:
        """Verify zero formatting."""
        assert _format_number(0.0) == "0.00"

    def test_negative_number(self) -> None:
        """Verify negative number formatting."""
        assert _format_number(-1234.567) == "-1,234.57"

    def test_large_number(self) -> None:
        """Verify large number with thousand separators."""
        assert _format_number(1234567.89) == "1,234,567.89"

    def test_custom_decimals(self) -> None:
        """Verify custom decimal places."""
        assert _format_number(1234.5678, decimals=3) == "1,234.568"
        assert _format_number(1234.5678, decimals=0) == "1,235"
        assert _format_number(1234.5678, decimals=4) == "1,234.5678"

    def test_small_number(self) -> None:
        """Verify small number formatting."""
        assert _format_number(0.001234) == "0.00"
        assert _format_number(0.001234, decimals=4) == "0.0012"


class TestFormatPercentage:
    """Tests for _format_percentage helper function."""

    def test_basic_formatting(self) -> None:
        """Verify basic percentage formatting."""
        assert _format_percentage(0.5) == "50.00%"
        assert _format_percentage(0.25) == "25.00%"

    def test_zero(self) -> None:
        """Verify zero percentage."""
        assert _format_percentage(0.0) == "0.00%"

    def test_one_hundred_percent(self) -> None:
        """Verify 100% formatting."""
        assert _format_percentage(1.0) == "100.00%"

    def test_small_percentage(self) -> None:
        """Verify small percentage formatting."""
        assert _format_percentage(0.001) == "0.10%"
        assert _format_percentage(0.0001) == "0.01%"

    def test_custom_decimals(self) -> None:
        """Verify custom decimal places."""
        assert _format_percentage(0.5, decimals=0) == "50%"
        assert _format_percentage(0.5, decimals=3) == "50.000%"
        assert _format_percentage(0.12345, decimals=1) == "12.3%"

    def test_over_one_hundred(self) -> None:
        """Verify over 100% formatting (edge case)."""
        assert _format_percentage(1.5) == "150.00%"


class TestFormatCurrency:
    """Tests for _format_currency helper function."""

    def test_positive_value(self) -> None:
        """Verify positive currency formatting."""
        assert _format_currency(1234.56) == "$1,234.56"

    def test_zero(self) -> None:
        """Verify zero currency formatting."""
        assert _format_currency(0.0) == "$0.00"

    def test_negative_value(self) -> None:
        """Verify negative currency formatting with leading minus."""
        assert _format_currency(-1234.56) == "-$1,234.56"

    def test_large_value(self) -> None:
        """Verify large currency with thousand separators."""
        assert _format_currency(1234567.89) == "$1,234,567.89"

    def test_small_value(self) -> None:
        """Verify small currency value."""
        assert _format_currency(0.01) == "$0.01"
        assert _format_currency(0.99) == "$0.99"

    def test_rounding(self) -> None:
        """Verify currency rounding to two decimals."""
        assert _format_currency(1.234) == "$1.23"
        assert _format_currency(1.235) == "$1.24"
        assert _format_currency(-1.235) == "-$1.24"

    def test_negative_small_value(self) -> None:
        """Verify small negative values."""
        assert _format_currency(-0.01) == "-$0.01"
        assert _format_currency(-0.50) == "-$0.50"
