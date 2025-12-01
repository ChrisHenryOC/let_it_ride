"""Unit tests for paytable configuration."""

from collections.abc import Callable

import pytest

from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    PaytableValidationError,
    bonus_paytable_a,
    bonus_paytable_b,
    bonus_paytable_c,
    standard_main_paytable,
)
from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.three_card_evaluator import ThreeCardHandRank


class TestMainGamePaytable:
    """Tests for MainGamePaytable."""

    def test_standard_paytable_has_correct_name(self) -> None:
        """Standard paytable should have the name 'standard'."""
        paytable = standard_main_paytable()
        assert paytable.name == "standard"

    def test_standard_paytable_covers_all_ranks(self) -> None:
        """Standard paytable should have payouts for all hand ranks."""
        paytable = standard_main_paytable()
        for rank in FiveCardHandRank:
            assert rank in paytable.payouts

    def test_standard_paytable_validates_successfully(self) -> None:
        """Standard paytable should pass validation."""
        paytable = standard_main_paytable()
        paytable.validate()  # Should not raise

    @pytest.mark.parametrize(
        "rank,expected_ratio",
        [
            (FiveCardHandRank.ROYAL_FLUSH, 1000),
            (FiveCardHandRank.STRAIGHT_FLUSH, 200),
            (FiveCardHandRank.FOUR_OF_A_KIND, 50),
            (FiveCardHandRank.FULL_HOUSE, 11),
            (FiveCardHandRank.FLUSH, 8),
            (FiveCardHandRank.STRAIGHT, 5),
            (FiveCardHandRank.THREE_OF_A_KIND, 3),
            (FiveCardHandRank.TWO_PAIR, 2),
            (FiveCardHandRank.PAIR_TENS_OR_BETTER, 1),
            (FiveCardHandRank.PAIR_BELOW_TENS, 0),
            (FiveCardHandRank.HIGH_CARD, 0),
        ],
    )
    def test_standard_paytable_has_correct_ratios(
        self, rank: FiveCardHandRank, expected_ratio: int
    ) -> None:
        """Standard paytable should have correct payout ratios."""
        paytable = standard_main_paytable()
        assert paytable.payouts[rank] == expected_ratio

    @pytest.mark.parametrize(
        "rank,bet,expected_payout",
        [
            (FiveCardHandRank.ROYAL_FLUSH, 5.0, 5000.0),
            (FiveCardHandRank.STRAIGHT_FLUSH, 10.0, 2000.0),
            (FiveCardHandRank.FOUR_OF_A_KIND, 5.0, 250.0),
            (FiveCardHandRank.FULL_HOUSE, 5.0, 55.0),
            (FiveCardHandRank.FLUSH, 5.0, 40.0),
            (FiveCardHandRank.STRAIGHT, 5.0, 25.0),
            (FiveCardHandRank.THREE_OF_A_KIND, 5.0, 15.0),
            (FiveCardHandRank.TWO_PAIR, 5.0, 10.0),
            (FiveCardHandRank.PAIR_TENS_OR_BETTER, 5.0, 5.0),
            (FiveCardHandRank.PAIR_BELOW_TENS, 5.0, 0.0),
            (FiveCardHandRank.HIGH_CARD, 5.0, 0.0),
        ],
    )
    def test_calculate_payout_returns_correct_amount(
        self, rank: FiveCardHandRank, bet: float, expected_payout: float
    ) -> None:
        """calculate_payout should return bet * ratio."""
        paytable = standard_main_paytable()
        payout = paytable.calculate_payout(rank, bet)
        assert payout == expected_payout

    def test_calculate_payout_with_zero_bet(self) -> None:
        """calculate_payout should return 0 for zero bet."""
        paytable = standard_main_paytable()
        payout = paytable.calculate_payout(FiveCardHandRank.ROYAL_FLUSH, 0.0)
        assert payout == 0.0

    def test_calculate_payout_with_large_bet(self) -> None:
        """calculate_payout should handle large bet amounts."""
        paytable = standard_main_paytable()
        payout = paytable.calculate_payout(FiveCardHandRank.ROYAL_FLUSH, 100.0)
        assert payout == 100000.0

    def test_validation_fails_with_missing_rank(self) -> None:
        """validate() should raise error if a rank is missing."""
        incomplete_payouts = {
            FiveCardHandRank.ROYAL_FLUSH: 1000,
            FiveCardHandRank.STRAIGHT_FLUSH: 200,
            # Missing other ranks
        }
        paytable = MainGamePaytable(name="incomplete", payouts=incomplete_payouts)

        with pytest.raises(PaytableValidationError) as exc_info:
            paytable.validate()
        assert "missing ranks" in str(exc_info.value)

    def test_validation_fails_with_negative_payout(self) -> None:
        """validate() should raise error for negative payouts."""
        payouts = {rank: 0 for rank in FiveCardHandRank}
        payouts[FiveCardHandRank.ROYAL_FLUSH] = -1  # Invalid

        paytable = MainGamePaytable(name="negative", payouts=payouts)

        with pytest.raises(PaytableValidationError) as exc_info:
            paytable.validate()
        assert "negative payout" in str(exc_info.value)

    def test_custom_paytable_creation(self) -> None:
        """Custom paytable should be creatable with arbitrary payouts."""
        custom_payouts = {
            FiveCardHandRank.ROYAL_FLUSH: 500,
            FiveCardHandRank.STRAIGHT_FLUSH: 100,
            FiveCardHandRank.FOUR_OF_A_KIND: 25,
            FiveCardHandRank.FULL_HOUSE: 8,
            FiveCardHandRank.FLUSH: 6,
            FiveCardHandRank.STRAIGHT: 4,
            FiveCardHandRank.THREE_OF_A_KIND: 2,
            FiveCardHandRank.TWO_PAIR: 1,
            FiveCardHandRank.PAIR_TENS_OR_BETTER: 1,
            FiveCardHandRank.PAIR_BELOW_TENS: 0,
            FiveCardHandRank.HIGH_CARD: 0,
        }
        paytable = MainGamePaytable(name="custom", payouts=custom_payouts)
        paytable.validate()  # Should not raise

        assert paytable.calculate_payout(FiveCardHandRank.ROYAL_FLUSH, 10.0) == 5000.0


class TestBonusPaytable:
    """Tests for BonusPaytable."""

    def test_paytable_a_has_correct_name(self) -> None:
        """Paytable A should have the name 'paytable_a'."""
        paytable = bonus_paytable_a()
        assert paytable.name == "paytable_a"

    def test_paytable_b_has_correct_name(self) -> None:
        """Paytable B should have the name 'paytable_b'."""
        paytable = bonus_paytable_b()
        assert paytable.name == "paytable_b"

    def test_paytable_c_has_correct_name(self) -> None:
        """Paytable C should have the name 'paytable_c'."""
        paytable = bonus_paytable_c()
        assert paytable.name == "paytable_c"

    @pytest.mark.parametrize(
        "factory", [bonus_paytable_a, bonus_paytable_b, bonus_paytable_c]
    )
    def test_bonus_paytables_cover_all_ranks(
        self, factory: Callable[[], BonusPaytable]
    ) -> None:
        """All bonus paytables should have payouts for all hand ranks."""
        paytable = factory()
        for rank in ThreeCardHandRank:
            assert rank in paytable.payouts

    @pytest.mark.parametrize(
        "factory", [bonus_paytable_a, bonus_paytable_b, bonus_paytable_c]
    )
    def test_bonus_paytables_validate_successfully(
        self, factory: Callable[[], BonusPaytable]
    ) -> None:
        """All bonus paytables should pass validation."""
        paytable = factory()
        paytable.validate()  # Should not raise

    @pytest.mark.parametrize(
        "rank,expected_ratio",
        [
            (ThreeCardHandRank.MINI_ROYAL, 50),
            (ThreeCardHandRank.STRAIGHT_FLUSH, 40),
            (ThreeCardHandRank.THREE_OF_A_KIND, 30),
            (ThreeCardHandRank.STRAIGHT, 6),
            (ThreeCardHandRank.FLUSH, 3),
            (ThreeCardHandRank.PAIR, 1),
            (ThreeCardHandRank.HIGH_CARD, 0),
        ],
    )
    def test_paytable_a_has_correct_ratios(
        self, rank: ThreeCardHandRank, expected_ratio: int
    ) -> None:
        """Paytable A should have correct payout ratios."""
        paytable = bonus_paytable_a()
        assert paytable.payouts[rank] == expected_ratio

    @pytest.mark.parametrize(
        "rank,expected_ratio",
        [
            (ThreeCardHandRank.MINI_ROYAL, 100),
            (ThreeCardHandRank.STRAIGHT_FLUSH, 40),
            (ThreeCardHandRank.THREE_OF_A_KIND, 30),
            (ThreeCardHandRank.STRAIGHT, 5),
            (ThreeCardHandRank.FLUSH, 4),
            (ThreeCardHandRank.PAIR, 1),
            (ThreeCardHandRank.HIGH_CARD, 0),
        ],
    )
    def test_paytable_b_has_correct_ratios(
        self, rank: ThreeCardHandRank, expected_ratio: int
    ) -> None:
        """Paytable B should have correct payout ratios."""
        paytable = bonus_paytable_b()
        assert paytable.payouts[rank] == expected_ratio

    @pytest.mark.parametrize(
        "rank,expected_ratio",
        [
            (ThreeCardHandRank.MINI_ROYAL, 1000),  # Default progressive
            (ThreeCardHandRank.STRAIGHT_FLUSH, 200),
            (ThreeCardHandRank.THREE_OF_A_KIND, 30),
            (ThreeCardHandRank.STRAIGHT, 6),
            (ThreeCardHandRank.FLUSH, 4),
            (ThreeCardHandRank.PAIR, 1),
            (ThreeCardHandRank.HIGH_CARD, 0),
        ],
    )
    def test_paytable_c_has_correct_ratios(
        self, rank: ThreeCardHandRank, expected_ratio: int
    ) -> None:
        """Paytable C should have correct payout ratios (default progressive)."""
        paytable = bonus_paytable_c()
        assert paytable.payouts[rank] == expected_ratio

    def test_paytable_c_custom_progressive_payout(self) -> None:
        """Paytable C should accept custom progressive payout."""
        paytable = bonus_paytable_c(progressive_payout=5000)
        assert paytable.payouts[ThreeCardHandRank.MINI_ROYAL] == 5000

    @pytest.mark.parametrize(
        "rank,bet,expected_payout",
        [
            (ThreeCardHandRank.MINI_ROYAL, 1.0, 100.0),
            (ThreeCardHandRank.STRAIGHT_FLUSH, 1.0, 40.0),
            (ThreeCardHandRank.THREE_OF_A_KIND, 5.0, 150.0),
            (ThreeCardHandRank.STRAIGHT, 5.0, 25.0),
            (ThreeCardHandRank.FLUSH, 5.0, 20.0),
            (ThreeCardHandRank.PAIR, 5.0, 5.0),
            (ThreeCardHandRank.HIGH_CARD, 5.0, 0.0),
        ],
    )
    def test_calculate_payout_returns_correct_amount(
        self, rank: ThreeCardHandRank, bet: float, expected_payout: float
    ) -> None:
        """calculate_payout should return bet * ratio."""
        paytable = bonus_paytable_b()
        payout = paytable.calculate_payout(rank, bet)
        assert payout == expected_payout

    def test_calculate_payout_with_zero_bet(self) -> None:
        """calculate_payout should return 0 for zero bet."""
        paytable = bonus_paytable_b()
        payout = paytable.calculate_payout(ThreeCardHandRank.MINI_ROYAL, 0.0)
        assert payout == 0.0

    def test_calculate_payout_with_large_bet(self) -> None:
        """calculate_payout should handle large bet amounts."""
        paytable = bonus_paytable_b()
        payout = paytable.calculate_payout(ThreeCardHandRank.MINI_ROYAL, 25.0)
        assert payout == 2500.0

    def test_validation_fails_with_missing_rank(self) -> None:
        """validate() should raise error if a rank is missing."""
        incomplete_payouts = {
            ThreeCardHandRank.MINI_ROYAL: 100,
            ThreeCardHandRank.STRAIGHT_FLUSH: 40,
            # Missing other ranks
        }
        paytable = BonusPaytable(name="incomplete", payouts=incomplete_payouts)

        with pytest.raises(PaytableValidationError) as exc_info:
            paytable.validate()
        assert "missing ranks" in str(exc_info.value)

    def test_validation_fails_with_negative_payout(self) -> None:
        """validate() should raise error for negative payouts."""
        payouts = {rank: 0 for rank in ThreeCardHandRank}
        payouts[ThreeCardHandRank.MINI_ROYAL] = -1  # Invalid

        paytable = BonusPaytable(name="negative", payouts=payouts)

        with pytest.raises(PaytableValidationError) as exc_info:
            paytable.validate()
        assert "negative payout" in str(exc_info.value)

    def test_custom_paytable_creation(self) -> None:
        """Custom paytable should be creatable with arbitrary payouts."""
        custom_payouts = {
            ThreeCardHandRank.MINI_ROYAL: 200,
            ThreeCardHandRank.STRAIGHT_FLUSH: 50,
            ThreeCardHandRank.THREE_OF_A_KIND: 25,
            ThreeCardHandRank.STRAIGHT: 10,
            ThreeCardHandRank.FLUSH: 8,
            ThreeCardHandRank.PAIR: 2,
            ThreeCardHandRank.HIGH_CARD: 0,
        }
        paytable = BonusPaytable(name="custom", payouts=custom_payouts)
        paytable.validate()  # Should not raise

        assert paytable.calculate_payout(ThreeCardHandRank.MINI_ROYAL, 5.0) == 1000.0


class TestPaytableImmutability:
    """Tests for paytable immutability."""

    def test_main_paytable_is_frozen(self) -> None:
        """MainGamePaytable should be immutable (frozen dataclass)."""
        paytable = standard_main_paytable()

        with pytest.raises(AttributeError):
            # Use setattr via exec to bypass mypy's static type checking
            # while still testing runtime immutability (avoids B010 lint error)
            attr_name = "name"
            setattr(paytable, attr_name, "modified")

    def test_bonus_paytable_is_frozen(self) -> None:
        """BonusPaytable should be immutable (frozen dataclass)."""
        paytable = bonus_paytable_b()

        with pytest.raises(AttributeError):
            # Use setattr via variable to bypass mypy's static type checking
            # while still testing runtime immutability (avoids B010 lint error)
            attr_name = "name"
            setattr(paytable, attr_name, "modified")
