"""Tests for progressive side bet configuration models."""

import pytest
from pydantic import ValidationError

from let_it_ride.config.models import (
    FullConfig,
    ProgressivePayoutEntryConfig,
    ProgressiveSideBetConfig,
)


class TestProgressivePayoutEntryConfig:
    """Tests for ProgressivePayoutEntryConfig validation."""

    def test_fixed_type_valid(self) -> None:
        """Fixed type with positive value is valid."""
        entry = ProgressivePayoutEntryConfig(type="fixed", value=500.0)
        assert entry.type == "fixed"
        assert entry.value == 500.0

    def test_jackpot_percentage_type_valid(self) -> None:
        """Jackpot percentage type with fraction is valid."""
        entry = ProgressivePayoutEntryConfig(type="jackpot_percentage", value=0.10)
        assert entry.type == "jackpot_percentage"
        assert entry.value == 0.10

    def test_zero_value_valid(self) -> None:
        """Zero value is valid (ge=0)."""
        entry = ProgressivePayoutEntryConfig(type="fixed", value=0.0)
        assert entry.value == 0.0

    def test_negative_value_rejected(self) -> None:
        """Negative value is rejected."""
        with pytest.raises(ValidationError):
            ProgressivePayoutEntryConfig(type="fixed", value=-1.0)

    def test_invalid_type_rejected(self) -> None:
        """Invalid type string is rejected."""
        with pytest.raises(ValidationError):
            ProgressivePayoutEntryConfig(type="invalid", value=100.0)  # type: ignore[arg-type]

    def test_jackpot_percentage_over_one_rejected(self) -> None:
        """Jackpot percentage value > 1.0 is rejected."""
        with pytest.raises(ValidationError, match="jackpot_percentage"):
            ProgressivePayoutEntryConfig(type="jackpot_percentage", value=1.5)

    def test_jackpot_percentage_exactly_one_valid(self) -> None:
        """Jackpot percentage value of exactly 1.0 is valid (100% of pool)."""
        entry = ProgressivePayoutEntryConfig(type="jackpot_percentage", value=1.0)
        assert entry.value == 1.0

    def test_fixed_large_value_valid(self) -> None:
        """Fixed type with large value is valid (no upper bound for fixed)."""
        entry = ProgressivePayoutEntryConfig(type="fixed", value=50000.0)
        assert entry.value == 50000.0


class TestProgressiveSideBetConfig:
    """Tests for ProgressiveSideBetConfig validation."""

    def test_defaults(self) -> None:
        """Default values are correct."""
        config = ProgressiveSideBetConfig()
        assert config.enabled is False
        assert config.bet_amount == 1.0
        assert config.seed_amount == 10000.0
        assert config.starting_jackpot == 10000.0
        assert config.contribution_rate == 0.71
        assert config.reset_to_seed is True
        assert config.paytable == {}

    def test_enabled_config(self) -> None:
        """Enabled config with custom values is valid."""
        config = ProgressiveSideBetConfig(
            enabled=True,
            bet_amount=2.0,
            seed_amount=5000.0,
            starting_jackpot=15000.0,
            contribution_rate=0.50,
        )
        assert config.enabled is True
        assert config.bet_amount == 2.0
        assert config.starting_jackpot == 15000.0

    def test_zero_bet_amount_rejected(self) -> None:
        """Zero bet amount is rejected (gt=0)."""
        with pytest.raises(ValidationError):
            ProgressiveSideBetConfig(bet_amount=0.0)

    def test_negative_seed_amount_rejected(self) -> None:
        """Negative seed amount is rejected."""
        with pytest.raises(ValidationError):
            ProgressiveSideBetConfig(seed_amount=-100.0)

    def test_contribution_rate_over_one_rejected(self) -> None:
        """Contribution rate over 1.0 is rejected."""
        with pytest.raises(ValidationError):
            ProgressiveSideBetConfig(contribution_rate=1.5)

    def test_zero_contribution_rate_rejected(self) -> None:
        """Zero contribution rate is rejected (gt=0)."""
        with pytest.raises(ValidationError):
            ProgressiveSideBetConfig(contribution_rate=0.0)

    def test_custom_paytable(self) -> None:
        """Custom paytable entries are parsed correctly."""
        config = ProgressiveSideBetConfig(
            paytable={
                "ROYAL_FLUSH": ProgressivePayoutEntryConfig(
                    type="jackpot_percentage", value=1.0
                ),
                "FLUSH": ProgressivePayoutEntryConfig(type="fixed", value=75.0),
            }
        )
        assert len(config.paytable) == 2
        assert config.paytable["ROYAL_FLUSH"].type == "jackpot_percentage"
        assert config.paytable["FLUSH"].value == 75.0

    def test_extra_fields_rejected(self) -> None:
        """Extra fields are rejected (extra=forbid)."""
        with pytest.raises(ValidationError):
            ProgressiveSideBetConfig(unknown_field="value")  # type: ignore[call-arg]


class TestFullConfigWithProgressive:
    """Tests for progressive integration with FullConfig."""

    def test_default_progressive_disabled(self) -> None:
        """Default FullConfig has progressive disabled."""
        config = FullConfig()
        assert config.progressive.enabled is False

    def test_progressive_enabled_in_full_config(self) -> None:
        """Progressive can be enabled in FullConfig."""
        config = FullConfig(
            progressive=ProgressiveSideBetConfig(enabled=True, bet_amount=1.0)
        )
        assert config.progressive.enabled is True
        assert config.progressive.bet_amount == 1.0

    def test_full_config_extra_fields_on_progressive_rejected(self) -> None:
        """Extra fields on progressive section rejected."""
        with pytest.raises(ValidationError):
            FullConfig(
                progressive={"enabled": True, "invalid_field": 42}  # type: ignore[arg-type]
            )
