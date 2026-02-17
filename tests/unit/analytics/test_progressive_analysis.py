"""Tests for progressive jackpot EV and breakeven analysis."""

import pytest

from let_it_ride.analytics.progressive_analysis import (
    BreakevenResult,
    HouseEdgeResult,
    _hand_rank_probability,
    calculate_breakeven_jackpot,
    calculate_expected_payout,
    calculate_house_edge,
)
from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.progressive_jackpot import (
    ProgressivePayout,
    ProgressivePaytable,
    standard_progressive_paytable,
)


class TestHandRankProbability:
    """Tests for _hand_rank_probability mapping."""

    def test_royal_flush_probability(self) -> None:
        """Royal flush probability should match theoretical value."""
        prob = _hand_rank_probability(FiveCardHandRank.ROYAL_FLUSH)
        assert prob == pytest.approx(4 / 2598960)

    def test_straight_flush_probability(self) -> None:
        """Straight flush probability should match theoretical value."""
        prob = _hand_rank_probability(FiveCardHandRank.STRAIGHT_FLUSH)
        assert prob == pytest.approx(36 / 2598960)

    def test_high_card_returns_zero(self) -> None:
        """HIGH_CARD is not in the rank mapping and should return 0."""
        prob = _hand_rank_probability(FiveCardHandRank.HIGH_CARD)
        assert prob == 0.0

    def test_pair_below_tens_returns_zero(self) -> None:
        """PAIR_BELOW_TENS is not in the rank mapping and should return 0."""
        prob = _hand_rank_probability(FiveCardHandRank.PAIR_BELOW_TENS)
        assert prob == 0.0

    def test_pair_tens_or_better_returns_zero(self) -> None:
        """PAIR_TENS_OR_BETTER is not in the rank mapping and should return 0."""
        prob = _hand_rank_probability(FiveCardHandRank.PAIR_TENS_OR_BETTER)
        assert prob == 0.0


class TestCalculateExpectedPayout:
    """Tests for calculate_expected_payout."""

    def test_standard_paytable_at_zero_jackpot(self) -> None:
        """At jackpot=0, only fixed payouts contribute."""
        paytable = standard_progressive_paytable()
        expected = calculate_expected_payout(paytable, jackpot_amount=0.0)

        # Only fixed payouts: 4oK=$500, FH=$100, Flush=$75, Straight=$50
        four_of_kind_prob = 624 / 2598960
        full_house_prob = 3744 / 2598960
        flush_prob = 5108 / 2598960
        straight_prob = 10200 / 2598960

        expected_fixed = (
            four_of_kind_prob * 500
            + full_house_prob * 100
            + flush_prob * 75
            + straight_prob * 50
        )
        assert expected == pytest.approx(expected_fixed)

    def test_standard_paytable_at_large_jackpot(self) -> None:
        """At large jackpot, percentage payouts dominate."""
        paytable = standard_progressive_paytable()
        expected = calculate_expected_payout(paytable, jackpot_amount=1_000_000.0)

        # Should be positive and significantly larger than at zero
        assert expected > calculate_expected_payout(paytable, jackpot_amount=0.0)

    def test_empty_paytable(self) -> None:
        """Empty paytable should return 0 expected payout."""
        paytable = ProgressivePaytable(name="empty", payouts={})
        expected = calculate_expected_payout(paytable, jackpot_amount=100_000.0)
        assert expected == 0.0

    def test_all_fixed_paytable(self) -> None:
        """All-fixed paytable should be independent of jackpot amount."""
        paytable = ProgressivePaytable(
            name="all_fixed",
            payouts={
                FiveCardHandRank.ROYAL_FLUSH: ProgressivePayout(
                    type="fixed", value=10000.0
                ),
                FiveCardHandRank.FLUSH: ProgressivePayout(type="fixed", value=50.0),
            },
        )
        at_low = calculate_expected_payout(paytable, jackpot_amount=1000.0)
        at_high = calculate_expected_payout(paytable, jackpot_amount=1_000_000.0)
        assert at_low == pytest.approx(at_high)


class TestCalculateBreakevenJackpot:
    """Tests for calculate_breakeven_jackpot."""

    def test_standard_paytable_breakeven_range(self) -> None:
        """Standard paytable breakeven should be in ~$200K-$250K range."""
        paytable = standard_progressive_paytable()
        result = calculate_breakeven_jackpot(paytable)

        assert isinstance(result, BreakevenResult)
        # Breakeven should be roughly in the $100K-$200K range for $1 bet
        assert 100_000 < result.breakeven_jackpot < 200_000

    def test_breakeven_payout_equals_bet(self) -> None:
        """At breakeven jackpot, expected payout should equal bet amount."""
        paytable = standard_progressive_paytable()
        result = calculate_breakeven_jackpot(paytable, bet_amount=1.0)

        expected_payout = calculate_expected_payout(paytable, result.breakeven_jackpot)
        assert expected_payout == pytest.approx(result.bet_amount, rel=1e-10)

    def test_breakeven_with_different_bet_amount(self) -> None:
        """Breakeven jackpot should scale with bet amount."""
        paytable = standard_progressive_paytable()
        result_1 = calculate_breakeven_jackpot(paytable, bet_amount=1.0)
        result_5 = calculate_breakeven_jackpot(paytable, bet_amount=5.0)

        # With larger bet, breakeven jackpot should be proportionally larger
        assert result_5.breakeven_jackpot > result_1.breakeven_jackpot

    def test_breakeven_result_fields(self) -> None:
        """BreakevenResult should have all expected fields."""
        paytable = standard_progressive_paytable()
        result = calculate_breakeven_jackpot(paytable, bet_amount=1.0)

        assert result.bet_amount == 1.0
        assert result.contribution_rate == 0.71
        assert result.fixed_ev > 0.0
        assert result.percentage_ev_coefficient > 0.0
        assert result.paytable_name == "standard_progressive"

    def test_all_fixed_paytable_raises(self) -> None:
        """All-fixed paytable should raise ValueError."""
        paytable = ProgressivePaytable(
            name="all_fixed",
            payouts={
                FiveCardHandRank.ROYAL_FLUSH: ProgressivePayout(
                    type="fixed", value=10000.0
                ),
            },
        )
        with pytest.raises(ValueError, match="no percentage-based payouts"):
            calculate_breakeven_jackpot(paytable)

    def test_empty_paytable_raises(self) -> None:
        """Empty paytable should raise ValueError."""
        paytable = ProgressivePaytable(name="empty", payouts={})
        with pytest.raises(ValueError, match="no percentage-based payouts"):
            calculate_breakeven_jackpot(paytable)

    def test_single_percentage_entry(self) -> None:
        """Paytable with single percentage entry should compute breakeven."""
        paytable = ProgressivePaytable(
            name="single",
            payouts={
                FiveCardHandRank.ROYAL_FLUSH: ProgressivePayout(
                    type="jackpot_percentage", value=1.0
                ),
            },
        )
        result = calculate_breakeven_jackpot(paytable, bet_amount=1.0)

        # breakeven = bet / (prob * 1.0) = 1 / (4/2598960)
        expected_breakeven = 1.0 / (4 / 2598960)
        assert result.breakeven_jackpot == pytest.approx(expected_breakeven)

    def test_custom_contribution_rate_stored(self) -> None:
        """Custom contribution rate should be stored in result."""
        paytable = standard_progressive_paytable()
        result = calculate_breakeven_jackpot(paytable, contribution_rate=0.50)
        assert result.contribution_rate == 0.50


class TestCalculateHouseEdge:
    """Tests for calculate_house_edge."""

    def test_high_house_edge_at_low_jackpot(self) -> None:
        """At seed amount, house edge should be very high."""
        paytable = standard_progressive_paytable()
        result = calculate_house_edge(paytable, jackpot_amount=10_000.0)

        assert isinstance(result, HouseEdgeResult)
        # House edge should be positive (house advantage) at low jackpot
        assert result.house_edge > 0.0
        assert result.player_return < 1.0

    def test_negative_house_edge_above_breakeven(self) -> None:
        """Above breakeven, house edge should be negative (player advantage)."""
        paytable = standard_progressive_paytable()
        breakeven = calculate_breakeven_jackpot(paytable)

        result = calculate_house_edge(
            paytable, jackpot_amount=breakeven.breakeven_jackpot * 2
        )
        assert result.house_edge < 0.0
        assert result.player_return > 1.0

    def test_zero_house_edge_at_breakeven(self) -> None:
        """At breakeven jackpot, house edge should be approximately 0."""
        paytable = standard_progressive_paytable()
        breakeven = calculate_breakeven_jackpot(paytable, bet_amount=1.0)

        result = calculate_house_edge(
            paytable, jackpot_amount=breakeven.breakeven_jackpot, bet_amount=1.0
        )
        assert result.house_edge == pytest.approx(0.0, abs=1e-10)
        assert result.player_return == pytest.approx(1.0, abs=1e-10)

    def test_result_fields(self) -> None:
        """HouseEdgeResult should have all expected fields."""
        paytable = standard_progressive_paytable()
        result = calculate_house_edge(paytable, jackpot_amount=50_000.0, bet_amount=1.0)

        assert result.jackpot_amount == 50_000.0
        assert result.bet_amount == 1.0
        assert result.expected_payout >= 0.0
        assert result.contribution_rate == 0.71

    def test_house_edge_decreases_with_jackpot(self) -> None:
        """House edge should decrease as jackpot grows."""
        paytable = standard_progressive_paytable()
        result_low = calculate_house_edge(paytable, jackpot_amount=10_000.0)
        result_high = calculate_house_edge(paytable, jackpot_amount=100_000.0)

        assert result_high.house_edge < result_low.house_edge

    def test_custom_bet_amount(self) -> None:
        """House edge should work with non-default bet amount."""
        paytable = standard_progressive_paytable()
        result = calculate_house_edge(paytable, jackpot_amount=50_000.0, bet_amount=5.0)
        # House edge is relative to bet: 1 - (payout/bet)
        assert result.player_return == pytest.approx(
            result.expected_payout / result.bet_amount
        )


class TestDataclassProperties:
    """Tests for dataclass frozen/slots properties."""

    def test_breakeven_result_is_frozen(self) -> None:
        """BreakevenResult should be immutable."""
        paytable = standard_progressive_paytable()
        result = calculate_breakeven_jackpot(paytable)

        with pytest.raises(AttributeError):
            result.breakeven_jackpot = 999.0  # type: ignore[misc]

    def test_house_edge_result_is_frozen(self) -> None:
        """HouseEdgeResult should be immutable."""
        paytable = standard_progressive_paytable()
        result = calculate_house_edge(paytable, jackpot_amount=50_000.0)

        with pytest.raises(AttributeError):
            result.house_edge = 999.0  # type: ignore[misc]
