"""Tests for the progressive jackpot side bet."""

import pytest

from let_it_ride.config.models import (
    ProgressivePayoutEntryConfig,
    ProgressiveSideBetConfig,
)
from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.progressive_jackpot import (
    ProgressiveJackpot,
    ProgressivePaytable,
    create_progressive_jackpot,
    standard_progressive_paytable,
)


@pytest.fixture
def standard_paytable() -> ProgressivePaytable:
    """Return the standard progressive paytable."""
    return standard_progressive_paytable()


@pytest.fixture
def jackpot(standard_paytable: ProgressivePaytable) -> ProgressiveJackpot:
    """Return a standard progressive jackpot with $10,000 pool."""
    return ProgressiveJackpot(
        seed_amount=10000.0,
        starting_pool=10000.0,
        contribution_rate=0.71,
        paytable=standard_paytable,
    )


class TestProgressiveJackpotProperties:
    """Tests for ProgressiveJackpot read-only properties."""

    def test_seed_amount_returns_configured_value(
        self, jackpot: ProgressiveJackpot
    ) -> None:
        """seed_amount property returns the value set at construction."""
        assert jackpot.seed_amount == pytest.approx(10000.0)

    def test_seed_amount_unchanged_after_contributions(
        self, jackpot: ProgressiveJackpot
    ) -> None:
        """seed_amount remains constant regardless of pool changes."""
        jackpot.contribute(100.0)
        assert jackpot.seed_amount == pytest.approx(10000.0)


class TestProgressiveJackpotContribution:
    """Tests for pool contribution mechanics."""

    def test_contribute_adds_correct_amount(self, jackpot: ProgressiveJackpot) -> None:
        """Contribute adds contribution_rate * bet_amount to pool."""
        initial_pool = jackpot.current_pool
        jackpot.contribute(1.0)
        assert jackpot.current_pool == pytest.approx(initial_pool + 0.71)

    def test_multiple_contributions_grow_pool(
        self, jackpot: ProgressiveJackpot
    ) -> None:
        """Multiple contributions accumulate correctly."""
        initial_pool = jackpot.current_pool
        for _ in range(100):
            jackpot.contribute(1.0)
        assert jackpot.current_pool == pytest.approx(initial_pool + 100 * 0.71)

    def test_contribute_with_different_bet_amounts(
        self, jackpot: ProgressiveJackpot
    ) -> None:
        """Contribution scales with bet amount."""
        initial_pool = jackpot.current_pool
        jackpot.contribute(5.0)
        assert jackpot.current_pool == pytest.approx(initial_pool + 5.0 * 0.71)


class TestProgressiveJackpotFixedPayout:
    """Tests for fixed dollar payouts."""

    def test_four_of_a_kind_pays_500(self, jackpot: ProgressiveJackpot) -> None:
        """Four of a kind pays $500 fixed."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.FOUR_OF_A_KIND)
        assert payout == 500.0

    def test_full_house_pays_100(self, jackpot: ProgressiveJackpot) -> None:
        """Full house pays $100 fixed."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.FULL_HOUSE)
        assert payout == 100.0

    def test_flush_pays_75(self, jackpot: ProgressiveJackpot) -> None:
        """Flush pays $75 fixed."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.FLUSH)
        assert payout == 75.0

    def test_straight_pays_50(self, jackpot: ProgressiveJackpot) -> None:
        """Straight pays $50 fixed."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.STRAIGHT)
        assert payout == 50.0

    def test_fixed_payout_does_not_change_pool(
        self, jackpot: ProgressiveJackpot
    ) -> None:
        """Fixed payouts do not deduct from the pool."""
        initial_pool = jackpot.current_pool
        jackpot.evaluate_payout(FiveCardHandRank.FOUR_OF_A_KIND)
        assert jackpot.current_pool == initial_pool


class TestProgressiveJackpotPercentagePayout:
    """Tests for jackpot percentage payouts."""

    def test_royal_flush_pays_100_percent(self, jackpot: ProgressiveJackpot) -> None:
        """Royal flush pays 100% of the jackpot pool."""
        pool_before = jackpot.current_pool
        payout = jackpot.evaluate_payout(FiveCardHandRank.ROYAL_FLUSH)
        assert payout == pytest.approx(pool_before)

    def test_royal_flush_resets_pool_to_seed(self, jackpot: ProgressiveJackpot) -> None:
        """Royal flush resets pool to seed amount."""
        # Grow the pool first
        for _ in range(1000):
            jackpot.contribute(1.0)
        jackpot.evaluate_payout(FiveCardHandRank.ROYAL_FLUSH)
        assert jackpot.current_pool == pytest.approx(10000.0)

    def test_straight_flush_pays_10_percent(self, jackpot: ProgressiveJackpot) -> None:
        """Straight flush pays 10% of the jackpot pool."""
        pool_before = jackpot.current_pool
        payout = jackpot.evaluate_payout(FiveCardHandRank.STRAIGHT_FLUSH)
        assert payout == pytest.approx(pool_before * 0.10)

    def test_straight_flush_deducts_from_pool(
        self, jackpot: ProgressiveJackpot
    ) -> None:
        """Straight flush deducts 10% from pool (pool continues)."""
        pool_before = jackpot.current_pool
        jackpot.evaluate_payout(FiveCardHandRank.STRAIGHT_FLUSH)
        assert jackpot.current_pool == pytest.approx(pool_before * 0.90)


class TestProgressiveJackpotNonQualifying:
    """Tests for non-qualifying hands."""

    def test_high_card_returns_zero(self, jackpot: ProgressiveJackpot) -> None:
        """High card returns 0 payout."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.HIGH_CARD)
        assert payout == 0.0

    def test_pair_below_tens_returns_zero(self, jackpot: ProgressiveJackpot) -> None:
        """Pair below tens returns 0 payout."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.PAIR_BELOW_TENS)
        assert payout == 0.0

    def test_pair_tens_or_better_returns_zero(
        self, jackpot: ProgressiveJackpot
    ) -> None:
        """Pair of tens or better returns 0 payout (not in progressive paytable)."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.PAIR_TENS_OR_BETTER)
        assert payout == 0.0

    def test_two_pair_returns_zero(self, jackpot: ProgressiveJackpot) -> None:
        """Two pair returns 0 payout (not in progressive paytable)."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.TWO_PAIR)
        assert payout == 0.0

    def test_three_of_a_kind_returns_zero(self, jackpot: ProgressiveJackpot) -> None:
        """Three of a kind returns 0 payout (not in progressive paytable)."""
        payout = jackpot.evaluate_payout(FiveCardHandRank.THREE_OF_A_KIND)
        assert payout == 0.0

    def test_non_qualifying_does_not_change_pool(
        self, jackpot: ProgressiveJackpot
    ) -> None:
        """Non-qualifying hands don't affect the pool."""
        initial_pool = jackpot.current_pool
        jackpot.evaluate_payout(FiveCardHandRank.HIGH_CARD)
        assert jackpot.current_pool == initial_pool


class TestProgressiveJackpotReset:
    """Tests for pool reset mechanics."""

    def test_reset_restores_seed_amount(self, jackpot: ProgressiveJackpot) -> None:
        """Reset restores pool to seed amount."""
        for _ in range(100):
            jackpot.contribute(1.0)
        jackpot.reset()
        assert jackpot.current_pool == pytest.approx(10000.0)

    def test_reset_to_seed_false(self, standard_paytable: ProgressivePaytable) -> None:
        """When reset_to_seed=False, royal flush zeroes pool."""
        jackpot = ProgressiveJackpot(
            seed_amount=10000.0,
            starting_pool=10000.0,
            contribution_rate=0.71,
            paytable=standard_paytable,
            reset_to_seed=False,
        )
        jackpot.evaluate_payout(FiveCardHandRank.ROYAL_FLUSH)
        assert jackpot.current_pool == pytest.approx(0.0)


class TestStandardProgressivePaytable:
    """Tests for the standard paytable factory."""

    def test_standard_paytable_has_six_entries(self) -> None:
        """Standard paytable has 6 qualifying hand ranks."""
        paytable = standard_progressive_paytable()
        assert len(paytable.payouts) == 6

    def test_standard_paytable_name(self) -> None:
        """Standard paytable has expected name."""
        paytable = standard_progressive_paytable()
        assert paytable.name == "standard_progressive"

    def test_royal_flush_is_jackpot_percentage(self) -> None:
        """Royal flush uses jackpot_percentage type."""
        paytable = standard_progressive_paytable()
        assert (
            paytable.payouts[FiveCardHandRank.ROYAL_FLUSH].type == "jackpot_percentage"
        )
        assert paytable.payouts[FiveCardHandRank.ROYAL_FLUSH].value == 1.0


class TestCreateProgressiveJackpotFromConfig:
    """Tests for create_progressive_jackpot factory."""

    def test_default_config_uses_standard_paytable(self) -> None:
        """Default config with no paytable uses standard paytable."""
        config = ProgressiveSideBetConfig(enabled=True)
        jackpot = create_progressive_jackpot(config)
        # Royal flush should pay 100% of pool (standard paytable)
        payout = jackpot.evaluate_payout(FiveCardHandRank.ROYAL_FLUSH)
        assert payout == pytest.approx(10000.0)

    def test_custom_paytable_from_config(self) -> None:
        """Custom paytable from config is applied correctly."""
        config = ProgressiveSideBetConfig(
            enabled=True,
            starting_jackpot=5000.0,
            seed_amount=5000.0,
            paytable={
                "ROYAL_FLUSH": ProgressivePayoutEntryConfig(
                    type="jackpot_percentage", value=1.0
                ),
                "FLUSH": ProgressivePayoutEntryConfig(type="fixed", value=25.0),
            },
        )
        jackpot = create_progressive_jackpot(config)
        assert jackpot.evaluate_payout(FiveCardHandRank.FLUSH) == 25.0
        assert jackpot.evaluate_payout(FiveCardHandRank.STRAIGHT) == 0.0

    def test_config_starting_jackpot_used(self) -> None:
        """Starting jackpot from config is used as initial pool."""
        config = ProgressiveSideBetConfig(
            enabled=True, starting_jackpot=25000.0, seed_amount=10000.0
        )
        jackpot = create_progressive_jackpot(config)
        assert jackpot.current_pool == pytest.approx(25000.0)

    def test_config_contribution_rate_used(self) -> None:
        """Contribution rate from config is used."""
        config = ProgressiveSideBetConfig(enabled=True, contribution_rate=0.50)
        jackpot = create_progressive_jackpot(config)
        initial = jackpot.current_pool
        jackpot.contribute(1.0)
        assert jackpot.current_pool == pytest.approx(initial + 0.50)

    def test_invalid_hand_rank_raises_value_error(self) -> None:
        """Invalid hand rank name in custom paytable raises ValueError."""
        config = ProgressiveSideBetConfig(
            enabled=True,
            paytable={
                "ROYAL_FLUSHH": ProgressivePayoutEntryConfig(
                    type="jackpot_percentage", value=1.0
                ),
            },
        )
        with pytest.raises(ValueError, match="Invalid hand rank name 'ROYAL_FLUSHH'"):
            create_progressive_jackpot(config)


class TestProgressiveJackpotContributeValidation:
    """Tests for contribute() input validation."""

    def test_negative_bet_raises_value_error(self) -> None:
        """Negative bet amount raises ValueError."""
        paytable = standard_progressive_paytable()
        jackpot = ProgressiveJackpot(
            seed_amount=10000.0,
            starting_pool=10000.0,
            contribution_rate=0.71,
            paytable=paytable,
        )
        with pytest.raises(ValueError, match="non-negative"):
            jackpot.contribute(-1.0)

    def test_zero_bet_accepted(self) -> None:
        """Zero bet amount is accepted (no contribution)."""
        paytable = standard_progressive_paytable()
        jackpot = ProgressiveJackpot(
            seed_amount=10000.0,
            starting_pool=10000.0,
            contribution_rate=0.71,
            paytable=paytable,
        )
        initial = jackpot.current_pool
        jackpot.contribute(0.0)
        assert jackpot.current_pool == pytest.approx(initial)
