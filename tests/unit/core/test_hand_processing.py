"""Unit tests for shared hand processing logic.

This module provides direct unit tests for the hand_processing module,
which contains the core logic shared between GameEngine and Table for
processing hands through strategy decisions and payout calculations.
"""

from typing import TYPE_CHECKING

import pytest

from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_b,
    standard_main_paytable,
)
from let_it_ride.core.card import Card, Rank, Suit
from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.hand_processing import (
    HandProcessingResult,
    process_hand_decisions_and_payouts,
)
from let_it_ride.core.three_card_evaluator import ThreeCardHandRank
from let_it_ride.strategy.base import Decision, StrategyContext

if TYPE_CHECKING:
    from let_it_ride.core.hand_analysis import HandAnalysis


# Test strategy implementations for controlled testing


class AlwaysRideStrategy:
    """Strategy that always rides both bets."""

    def decide_bet1(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis, context  # Unused
        return Decision.RIDE

    def decide_bet2(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis, context  # Unused
        return Decision.RIDE


class AlwaysPullStrategy:
    """Strategy that always pulls both bets."""

    def decide_bet1(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis, context  # Unused
        return Decision.PULL

    def decide_bet2(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis, context  # Unused
        return Decision.PULL


class RidePullStrategy:
    """Strategy that rides bet 1 and pulls bet 2."""

    def decide_bet1(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis, context  # Unused
        return Decision.RIDE

    def decide_bet2(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis, context  # Unused
        return Decision.PULL


class PullRideStrategy:
    """Strategy that pulls bet 1 and rides bet 2."""

    def decide_bet1(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis, context  # Unused
        return Decision.PULL

    def decide_bet2(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis, context  # Unused
        return Decision.RIDE


class ContextCapturingStrategy:
    """Strategy that captures the context passed to it for verification."""

    def __init__(self) -> None:
        self.bet1_context: StrategyContext | None = None
        self.bet2_context: StrategyContext | None = None

    def decide_bet1(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis  # Unused
        self.bet1_context = context
        return Decision.RIDE

    def decide_bet2(
        self, analysis: "HandAnalysis", context: StrategyContext
    ) -> Decision:
        del analysis  # Unused
        self.bet2_context = context
        return Decision.RIDE


# Fixtures


@pytest.fixture
def default_context() -> StrategyContext:
    """Provide a default strategy context for tests."""
    return StrategyContext(
        session_profit=0.0,
        hands_played=0,
        streak=0,
        bankroll=100.0,
    )


@pytest.fixture
def main_paytable() -> MainGamePaytable:
    """Provide the standard main game paytable."""
    return standard_main_paytable()


@pytest.fixture
def bonus_paytable() -> BonusPaytable:
    """Provide the standard bonus paytable."""
    return bonus_paytable_b()


# Card sets for deterministic testing


def high_card_hand() -> tuple[tuple[Card, Card, Card], tuple[Card, Card]]:
    """Return cards that form a high card hand (no pairs, no flush, no straight).

    Player cards: 2c, 5d, 9h
    Community cards: Jc, Kd
    Final hand: 2c, 5d, 9h, Jc, Kd - High Card (King high)
    """
    player_cards = (
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.FIVE, Suit.DIAMONDS),
        Card(Rank.NINE, Suit.HEARTS),
    )
    community_cards = (
        Card(Rank.JACK, Suit.CLUBS),
        Card(Rank.KING, Suit.DIAMONDS),
    )
    return player_cards, community_cards


def pair_tens_hand() -> tuple[tuple[Card, Card, Card], tuple[Card, Card]]:
    """Return cards that form a pair of tens (paying hand).

    Player cards: Tc, Td, 3h
    Community cards: 7s, 2c
    Final hand: Tc, Td, 3h, 7s, 2c - Pair of Tens (pays 1:1)
    """
    player_cards = (
        Card(Rank.TEN, Suit.CLUBS),
        Card(Rank.TEN, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.HEARTS),
    )
    community_cards = (
        Card(Rank.SEVEN, Suit.SPADES),
        Card(Rank.TWO, Suit.CLUBS),
    )
    return player_cards, community_cards


def three_of_a_kind_hand() -> tuple[tuple[Card, Card, Card], tuple[Card, Card]]:
    """Return cards that form three of a kind.

    Player cards: Ac, Ad, Ah
    Community cards: 5s, 2c
    Final hand: Ac, Ad, Ah, 5s, 2c - Three of a Kind (pays 3:1)
    Three aces in player hand also pays 30:1 bonus.
    """
    player_cards = (
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.ACE, Suit.HEARTS),
    )
    community_cards = (
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.TWO, Suit.CLUBS),
    )
    return player_cards, community_cards


def flush_hand() -> tuple[tuple[Card, Card, Card], tuple[Card, Card]]:
    """Return cards that form a flush.

    Player cards: 2h, 5h, 9h
    Community cards: Jh, Kh
    Final hand: 2h, 5h, 9h, Jh, Kh - Flush (pays 8:1)
    Player's 3-card hand is also a flush (pays 4:1 bonus).
    """
    player_cards = (
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.NINE, Suit.HEARTS),
    )
    community_cards = (
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS),
    )
    return player_cards, community_cards


class TestHandProcessingResultDataclass:
    """Tests for HandProcessingResult dataclass properties."""

    def test_is_frozen(self) -> None:
        """Verify HandProcessingResult is immutable (frozen=True)."""
        result = HandProcessingResult(
            decision_bet1=Decision.RIDE,
            decision_bet2=Decision.RIDE,
            final_hand_rank=FiveCardHandRank.HIGH_CARD,
            bets_at_risk=15.0,
            main_payout=0.0,
            bonus_hand_rank=None,
            bonus_payout=0.0,
            net_result=-15.0,
        )
        with pytest.raises(AttributeError):
            result.net_result = 100.0  # type: ignore[misc]

    def test_has_slots(self) -> None:
        """Verify HandProcessingResult uses slots for memory efficiency."""
        result = HandProcessingResult(
            decision_bet1=Decision.RIDE,
            decision_bet2=Decision.RIDE,
            final_hand_rank=FiveCardHandRank.HIGH_CARD,
            bets_at_risk=15.0,
            main_payout=0.0,
            bonus_hand_rank=None,
            bonus_payout=0.0,
            net_result=-15.0,
        )
        # slots=True means __dict__ doesn't exist
        assert not hasattr(result, "__dict__")

    def test_all_fields_accessible(self) -> None:
        """Verify all fields are correctly stored and accessible."""
        result = HandProcessingResult(
            decision_bet1=Decision.RIDE,
            decision_bet2=Decision.PULL,
            final_hand_rank=FiveCardHandRank.PAIR_TENS_OR_BETTER,
            bets_at_risk=10.0,
            main_payout=10.0,
            bonus_hand_rank=ThreeCardHandRank.PAIR,
            bonus_payout=1.0,
            net_result=11.0,
        )
        assert result.decision_bet1 == Decision.RIDE
        assert result.decision_bet2 == Decision.PULL
        assert result.final_hand_rank == FiveCardHandRank.PAIR_TENS_OR_BETTER
        assert result.bets_at_risk == 10.0
        assert result.main_payout == 10.0
        assert result.bonus_hand_rank == ThreeCardHandRank.PAIR
        assert result.bonus_payout == 1.0
        assert result.net_result == 11.0

    def test_bonus_hand_rank_can_be_none(self) -> None:
        """Verify bonus_hand_rank can be None (no bonus bet)."""
        result = HandProcessingResult(
            decision_bet1=Decision.RIDE,
            decision_bet2=Decision.RIDE,
            final_hand_rank=FiveCardHandRank.HIGH_CARD,
            bets_at_risk=15.0,
            main_payout=0.0,
            bonus_hand_rank=None,
            bonus_payout=0.0,
            net_result=-15.0,
        )
        assert result.bonus_hand_rank is None


class TestBetsAtRiskCalculation:
    """Tests for bets_at_risk calculation based on pull/ride decisions."""

    def test_all_ride_three_bets_at_risk(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """RIDE/RIDE = 3 bets at risk (bet 1 + bet 2 + bet 3)."""
        player_cards, community_cards = high_card_hand()
        strategy = AlwaysRideStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        assert result.decision_bet1 == Decision.RIDE
        assert result.decision_bet2 == Decision.RIDE
        assert result.bets_at_risk == base_bet * 3  # 15.0

    def test_all_pull_one_bet_at_risk(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """PULL/PULL = 1 bet at risk (only bet 3 is always active)."""
        player_cards, community_cards = high_card_hand()
        strategy = AlwaysPullStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        assert result.decision_bet1 == Decision.PULL
        assert result.decision_bet2 == Decision.PULL
        assert result.bets_at_risk == base_bet * 1  # 5.0

    def test_ride_pull_two_bets_at_risk(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """RIDE/PULL = 2 bets at risk (bet 1 + bet 3)."""
        player_cards, community_cards = high_card_hand()
        strategy = RidePullStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        assert result.decision_bet1 == Decision.RIDE
        assert result.decision_bet2 == Decision.PULL
        assert result.bets_at_risk == base_bet * 2  # 10.0

    def test_pull_ride_two_bets_at_risk(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """PULL/RIDE = 2 bets at risk (bet 2 + bet 3)."""
        player_cards, community_cards = high_card_hand()
        strategy = PullRideStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        assert result.decision_bet1 == Decision.PULL
        assert result.decision_bet2 == Decision.RIDE
        assert result.bets_at_risk == base_bet * 2  # 10.0


class TestMainGamePayout:
    """Tests for main game payout calculations."""

    def test_losing_hand_zero_payout(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """High card hand should have zero payout."""
        player_cards, community_cards = high_card_hand()
        strategy = AlwaysRideStrategy()

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=5.0,
            bonus_bet=0.0,
            context=default_context,
        )

        assert result.final_hand_rank == FiveCardHandRank.HIGH_CARD
        assert result.main_payout == 0.0

    def test_pair_tens_pays_one_to_one(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """Pair of tens should pay 1:1."""
        player_cards, community_cards = pair_tens_hand()
        strategy = AlwaysRideStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        assert result.final_hand_rank == FiveCardHandRank.PAIR_TENS_OR_BETTER
        # 3 bets at risk * base_bet * 1:1 payout = 15.0
        assert result.main_payout == result.bets_at_risk * 1
        assert result.main_payout == 15.0

    def test_three_of_a_kind_pays_three_to_one(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """Three of a kind should pay 3:1."""
        player_cards, community_cards = three_of_a_kind_hand()
        strategy = AlwaysRideStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        assert result.final_hand_rank == FiveCardHandRank.THREE_OF_A_KIND
        # 3 bets at risk * base_bet * 3:1 payout = 45.0
        assert result.main_payout == result.bets_at_risk * 3
        assert result.main_payout == 45.0

    def test_flush_pays_eight_to_one(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """Flush should pay 8:1."""
        player_cards, community_cards = flush_hand()
        strategy = AlwaysRideStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        assert result.final_hand_rank == FiveCardHandRank.FLUSH
        # 3 bets at risk * base_bet * 8:1 payout = 120.0
        assert result.main_payout == result.bets_at_risk * 8
        assert result.main_payout == 120.0


class TestNetResultCalculation:
    """Tests for net result (profit/loss) calculations."""

    def test_losing_hand_net_is_negative_bets_at_risk(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """Losing hand net result should be negative bets at risk."""
        player_cards, community_cards = high_card_hand()
        strategy = AlwaysRideStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        # Lost 3 bets at risk
        assert result.net_result == -15.0

    def test_winning_hand_net_is_payout(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """Winning hand net result should be the payout."""
        player_cards, community_cards = pair_tens_hand()
        strategy = AlwaysRideStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        # Won 15.0 (1:1 on 15 bet)
        assert result.net_result == 15.0

    def test_net_result_with_pull_decisions_losing(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """Net result with PULL/PULL on losing hand should be -1 bet."""
        player_cards, community_cards = high_card_hand()
        strategy = AlwaysPullStrategy()
        base_bet = 5.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=base_bet,
            bonus_bet=0.0,
            context=default_context,
        )

        # Lost only 1 bet at risk
        assert result.net_result == -5.0


class TestBonusBetHandling:
    """Tests for bonus bet edge cases."""

    def test_zero_bonus_bet_no_bonus_evaluation(
        self,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        default_context: StrategyContext,
    ) -> None:
        """bonus_bet=0 should not evaluate bonus hand even with paytable."""
        player_cards, community_cards = three_of_a_kind_hand()
        strategy = AlwaysRideStrategy()

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            base_bet=5.0,
            bonus_bet=0.0,  # No bonus bet
            context=default_context,
        )

        # Even though we have a bonus paytable, no bonus bet means no evaluation
        assert result.bonus_hand_rank is None
        assert result.bonus_payout == 0.0

    def test_positive_bonus_bet_evaluates_three_card_hand(
        self,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        default_context: StrategyContext,
    ) -> None:
        """bonus_bet > 0 should evaluate the 3-card hand for bonus."""
        player_cards, community_cards = three_of_a_kind_hand()
        strategy = AlwaysRideStrategy()
        bonus_bet = 1.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            base_bet=5.0,
            bonus_bet=bonus_bet,
            context=default_context,
        )

        # Three aces in player hand should evaluate as THREE_OF_A_KIND
        assert result.bonus_hand_rank == ThreeCardHandRank.THREE_OF_A_KIND
        # Three of a kind pays 30:1 in bonus_paytable_b
        assert result.bonus_payout == bonus_bet * 30

    def test_bonus_bet_without_paytable_no_evaluation(
        self,
        main_paytable: MainGamePaytable,
        default_context: StrategyContext,
    ) -> None:
        """bonus_bet > 0 without paytable should not crash (guarded)."""
        player_cards, community_cards = three_of_a_kind_hand()
        strategy = AlwaysRideStrategy()

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,  # No paytable
            base_bet=5.0,
            bonus_bet=1.0,  # Has bonus bet but no paytable
            context=default_context,
        )

        # No paytable means no bonus evaluation even with bonus_bet
        assert result.bonus_hand_rank is None
        assert result.bonus_payout == 0.0

    def test_losing_bonus_hand_net_includes_bonus_loss(
        self,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        default_context: StrategyContext,
    ) -> None:
        """Losing bonus hand should subtract bonus_bet from net result."""
        player_cards, community_cards = high_card_hand()
        strategy = AlwaysRideStrategy()
        base_bet = 5.0
        bonus_bet = 1.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            base_bet=base_bet,
            bonus_bet=bonus_bet,
            context=default_context,
        )

        # High card loses both main game and bonus
        assert result.bonus_hand_rank == ThreeCardHandRank.HIGH_CARD
        assert result.bonus_payout == 0.0
        # Net = -15 (main) + -1 (bonus) = -16
        assert result.net_result == -16.0

    def test_winning_bonus_hand_net_includes_bonus_win(
        self,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        default_context: StrategyContext,
    ) -> None:
        """Winning bonus hand should add bonus payout to net result."""
        player_cards, community_cards = flush_hand()  # Player's 3 cards are flush
        strategy = AlwaysRideStrategy()
        base_bet = 5.0
        bonus_bet = 1.0

        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            base_bet=base_bet,
            bonus_bet=bonus_bet,
            context=default_context,
        )

        # Flush pays 8:1 on main (120), flush pays 4:1 on bonus (4)
        assert result.bonus_hand_rank == ThreeCardHandRank.FLUSH
        assert result.bonus_payout == 4.0  # 1 * 4
        # Net = 120 (main) + 4 (bonus) = 124
        assert result.net_result == 124.0


class TestStrategyContextPropagation:
    """Tests for strategy context being correctly passed to strategy."""

    def test_context_passed_to_decide_bet1(
        self,
        main_paytable: MainGamePaytable,
    ) -> None:
        """Verify context is passed to strategy.decide_bet1()."""
        player_cards, community_cards = high_card_hand()
        strategy = ContextCapturingStrategy()
        context = StrategyContext(
            session_profit=50.0,
            hands_played=10,
            streak=2,
            bankroll=150.0,
        )

        process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=5.0,
            bonus_bet=0.0,
            context=context,
        )

        assert strategy.bet1_context is context

    def test_context_passed_to_decide_bet2(
        self,
        main_paytable: MainGamePaytable,
    ) -> None:
        """Verify context is passed to strategy.decide_bet2()."""
        player_cards, community_cards = high_card_hand()
        strategy = ContextCapturingStrategy()
        context = StrategyContext(
            session_profit=-20.0,
            hands_played=5,
            streak=-1,
            bankroll=80.0,
        )

        process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            base_bet=5.0,
            bonus_bet=0.0,
            context=context,
        )

        assert strategy.bet2_context is context
