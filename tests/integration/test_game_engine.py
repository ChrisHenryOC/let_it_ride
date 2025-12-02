"""Integration tests for the GameEngine.

These tests verify the complete hand flow from dealing through payout
calculation, including strategy decisions and bonus bet handling.
"""

import random

import pytest

from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_b,
    standard_main_paytable,
)
from let_it_ride.core.deck import Deck
from let_it_ride.core.game_engine import GameEngine, GameHandResult
from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.three_card_evaluator import ThreeCardHandRank
from let_it_ride.strategy.base import Decision, StrategyContext
from let_it_ride.strategy.basic import BasicStrategy


class AlwaysRideStrategy:
    """Test strategy that always rides on both decisions."""

    def decide_bet1(
        self,
        analysis: object,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        return Decision.RIDE

    def decide_bet2(
        self,
        analysis: object,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        return Decision.RIDE


class AlwaysPullStrategy:
    """Test strategy that always pulls on both decisions."""

    def decide_bet1(
        self,
        analysis: object,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        return Decision.PULL

    def decide_bet2(
        self,
        analysis: object,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        return Decision.PULL


class PullBet1OnlyStrategy:
    """Test strategy that pulls bet 1 but rides bet 2."""

    def decide_bet1(
        self,
        analysis: object,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        return Decision.PULL

    def decide_bet2(
        self,
        analysis: object,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        return Decision.RIDE


class PullBet2OnlyStrategy:
    """Test strategy that rides bet 1 but pulls bet 2."""

    def decide_bet1(
        self,
        analysis: object,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        return Decision.RIDE

    def decide_bet2(
        self,
        analysis: object,  # noqa: ARG002
        context: StrategyContext,  # noqa: ARG002
    ) -> Decision:
        return Decision.PULL


@pytest.fixture
def deck() -> Deck:
    """Create a fresh deck for testing."""
    return Deck()


@pytest.fixture
def main_paytable() -> MainGamePaytable:
    """Standard main game paytable."""
    return standard_main_paytable()


@pytest.fixture
def bonus_paytable() -> BonusPaytable:
    """Standard bonus paytable (variant B)."""
    return bonus_paytable_b()


@pytest.fixture
def rng() -> random.Random:
    """Seeded RNG for reproducible tests."""
    return random.Random(42)


class TestBetValidation:
    """Test input validation for bet amounts."""

    def test_zero_base_bet_raises_error(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """Zero base_bet raises ValueError."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        with pytest.raises(ValueError, match="base_bet must be positive"):
            engine.play_hand(hand_id=1, base_bet=0.0)

    def test_negative_base_bet_raises_error(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """Negative base_bet raises ValueError."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        with pytest.raises(ValueError, match="base_bet must be positive"):
            engine.play_hand(hand_id=1, base_bet=-5.0)

    def test_negative_bonus_bet_raises_error(
        self,
        deck: Deck,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        rng: random.Random,
    ) -> None:
        """Negative bonus_bet raises ValueError."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            rng=rng,
        )

        with pytest.raises(ValueError, match="bonus_bet cannot be negative"):
            engine.play_hand(hand_id=1, base_bet=5.0, bonus_bet=-1.0)

    def test_zero_bonus_bet_is_valid(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """Zero bonus_bet is valid (no bonus bet placed)."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0, bonus_bet=0.0)
        assert result.bonus_bet == 0.0


class TestGameEngineBasicFlow:
    """Test basic game engine functionality."""

    def test_play_hand_returns_game_hand_result(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """GameEngine.play_hand returns a GameHandResult."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0)

        assert isinstance(result, GameHandResult)
        assert result.hand_id == 1
        assert result.base_bet == 5.0

    def test_play_hand_deals_correct_cards(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """GameEngine deals 3 player cards and 2 community cards."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0)

        assert len(result.player_cards) == 3
        assert len(result.community_cards) == 2
        # All cards should be unique
        all_cards = list(result.player_cards) + list(result.community_cards)
        assert len(set(all_cards)) == 5

    def test_play_hand_records_decisions(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """GameEngine records bet 1 and bet 2 decisions."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0)

        assert result.decision_bet1 == Decision.RIDE
        assert result.decision_bet2 == Decision.RIDE

    def test_play_hand_evaluates_final_hand(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """GameEngine evaluates the 5-card final hand."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0)

        assert isinstance(result.final_hand_rank, FiveCardHandRank)


class TestBetsAtRisk:
    """Test bets_at_risk calculation based on pull/ride decisions."""

    def test_all_ride_three_bets_at_risk(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """All RIDE = 3 bets at risk."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0)

        assert result.bets_at_risk == 15.0  # 3 * 5.0

    def test_all_pull_one_bet_at_risk(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """All PULL = 1 bet at risk (bet 3 always active)."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysPullStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0)

        assert result.bets_at_risk == 5.0  # 1 * 5.0

    def test_pull_bet1_two_bets_at_risk(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """PULL bet 1, RIDE bet 2 = 2 bets at risk."""
        engine = GameEngine(
            deck=deck,
            strategy=PullBet1OnlyStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0)

        assert result.decision_bet1 == Decision.PULL
        assert result.decision_bet2 == Decision.RIDE
        assert result.bets_at_risk == 10.0  # 2 * 5.0

    def test_pull_bet2_two_bets_at_risk(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """RIDE bet 1, PULL bet 2 = 2 bets at risk."""
        engine = GameEngine(
            deck=deck,
            strategy=PullBet2OnlyStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0)

        assert result.decision_bet1 == Decision.RIDE
        assert result.decision_bet2 == Decision.PULL
        assert result.bets_at_risk == 10.0  # 2 * 5.0


class TestMainGamePayout:
    """Test main game payout calculation."""

    def test_losing_hand_zero_payout(
        self, main_paytable: MainGamePaytable
    ) -> None:
        """Losing hands (high card, low pair) have zero payout."""
        # Play many hands to find a losing one
        for seed in range(100):
            engine = GameEngine(
                deck=Deck(),
                strategy=AlwaysRideStrategy(),
                main_paytable=main_paytable,
                bonus_paytable=None,
                rng=random.Random(seed),
            )
            result = engine.play_hand(hand_id=1, base_bet=5.0)

            if result.final_hand_rank in (
                FiveCardHandRank.HIGH_CARD,
                FiveCardHandRank.PAIR_BELOW_TENS,
            ):
                assert result.main_payout == 0.0
                assert result.net_result < 0  # Lost their bets
                return

        # If no losing hand found in 100 tries, that's statistically unlikely but ok
        pytest.skip("Could not find a losing hand in test runs")

    def test_paying_hand_positive_payout(
        self, main_paytable: MainGamePaytable
    ) -> None:
        """Paying hands have positive payout."""
        # Play many hands to find a paying one
        for seed in range(200):
            engine = GameEngine(
                deck=Deck(),
                strategy=AlwaysRideStrategy(),
                main_paytable=main_paytable,
                bonus_paytable=None,
                rng=random.Random(seed),
            )
            result = engine.play_hand(hand_id=1, base_bet=5.0)

            if result.final_hand_rank.value >= FiveCardHandRank.PAIR_TENS_OR_BETTER.value:
                assert result.main_payout > 0
                return

        pytest.skip("Could not find a paying hand in test runs")


class TestNetResult:
    """Test net result calculation."""

    def test_losing_hand_negative_net(
        self, main_paytable: MainGamePaytable
    ) -> None:
        """Losing hand has negative net result equal to bets at risk."""
        for seed in range(100):
            engine = GameEngine(
                deck=Deck(),
                strategy=AlwaysRideStrategy(),
                main_paytable=main_paytable,
                bonus_paytable=None,
                rng=random.Random(seed),
            )
            result = engine.play_hand(hand_id=1, base_bet=5.0)

            if result.main_payout == 0:
                assert result.net_result == -result.bets_at_risk
                return

        pytest.skip("Could not find a losing hand in test runs")

    def test_winning_hand_positive_net(
        self, main_paytable: MainGamePaytable
    ) -> None:
        """Winning hand has positive net result equal to payout."""
        for seed in range(200):
            engine = GameEngine(
                deck=Deck(),
                strategy=AlwaysRideStrategy(),
                main_paytable=main_paytable,
                bonus_paytable=None,
                rng=random.Random(seed),
            )
            result = engine.play_hand(hand_id=1, base_bet=5.0)

            if result.main_payout > 0:
                # Net = payout (bonus_bet is 0)
                assert result.net_result == result.main_payout
                return

        pytest.skip("Could not find a winning hand in test runs")


class TestBonusBet:
    """Test bonus bet handling."""

    def test_no_bonus_bet_no_bonus_result(
        self,
        deck: Deck,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        rng: random.Random,
    ) -> None:
        """No bonus bet means no bonus evaluation."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0, bonus_bet=0.0)

        assert result.bonus_bet == 0.0
        assert result.bonus_hand_rank is None
        assert result.bonus_payout == 0.0

    def test_bonus_bet_evaluates_three_card_hand(
        self,
        deck: Deck,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        rng: random.Random,
    ) -> None:
        """Bonus bet causes 3-card hand evaluation."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            rng=rng,
        )

        result = engine.play_hand(hand_id=1, base_bet=5.0, bonus_bet=1.0)

        assert result.bonus_bet == 1.0
        assert result.bonus_hand_rank is not None
        assert isinstance(result.bonus_hand_rank, ThreeCardHandRank)

    def test_bonus_bet_without_paytable_raises_error(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """Bonus bet without paytable raises ValueError."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,  # No bonus paytable
            rng=rng,
        )

        with pytest.raises(ValueError, match="bonus_bet > 0 requires a bonus_paytable"):
            engine.play_hand(hand_id=1, base_bet=5.0, bonus_bet=1.0)

    def test_losing_bonus_negative_contribution(
        self,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
    ) -> None:
        """Losing bonus bet contributes negatively to net result."""
        for seed in range(100):
            engine = GameEngine(
                deck=Deck(),
                strategy=AlwaysRideStrategy(),
                main_paytable=main_paytable,
                bonus_paytable=bonus_paytable,
                rng=random.Random(seed),
            )
            result = engine.play_hand(hand_id=1, base_bet=5.0, bonus_bet=1.0)

            # Most hands have HIGH_CARD bonus (loses)
            if result.bonus_hand_rank == ThreeCardHandRank.HIGH_CARD:
                assert result.bonus_payout == 0.0
                # Net includes -1.0 for lost bonus
                main_net = (
                    result.main_payout
                    if result.main_payout > 0
                    else -result.bets_at_risk
                )
                expected_net = main_net - 1.0  # Bonus bet lost
                assert result.net_result == expected_net
                return

        pytest.skip("Could not find a losing bonus hand in test runs")


class TestDeckManagement:
    """Test deck reset and shuffle behavior."""

    def test_deck_reset_between_hands(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """Deck is reset before each hand."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        # Play multiple hands
        for i in range(10):
            result = engine.play_hand(hand_id=i, base_bet=5.0)
            # Each hand should have 5 unique cards
            all_cards = list(result.player_cards) + list(result.community_cards)
            assert len(set(all_cards)) == 5

    def test_same_seed_same_hand(
        self, main_paytable: MainGamePaytable
    ) -> None:
        """Same RNG seed produces identical hands."""
        engine1 = GameEngine(
            deck=Deck(),
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=random.Random(12345),
        )
        engine2 = GameEngine(
            deck=Deck(),
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=random.Random(12345),
        )

        result1 = engine1.play_hand(hand_id=1, base_bet=5.0)
        result2 = engine2.play_hand(hand_id=1, base_bet=5.0)

        assert result1.player_cards == result2.player_cards
        assert result1.community_cards == result2.community_cards
        assert result1.final_hand_rank == result2.final_hand_rank


class TestStrategyContext:
    """Test strategy context handling."""

    def test_default_context_used_when_none(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """Default context is created when None passed."""
        engine = GameEngine(
            deck=deck,
            strategy=AlwaysRideStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        # Should not raise
        result = engine.play_hand(hand_id=1, base_bet=5.0, context=None)
        assert result is not None

    def test_custom_context_passed_to_strategy(
        self, deck: Deck, main_paytable: MainGamePaytable, rng: random.Random
    ) -> None:
        """Custom context is passed to strategy."""

        class ContextCapturingStrategy:
            """Strategy that captures the context for inspection."""

            captured_contexts: list[StrategyContext]

            def __init__(self) -> None:
                self.captured_contexts = []

            def decide_bet1(
                self,
                analysis: object,  # noqa: ARG002
                context: StrategyContext,
            ) -> Decision:
                self.captured_contexts.append(context)
                return Decision.RIDE

            def decide_bet2(
                self,
                analysis: object,  # noqa: ARG002
                context: StrategyContext,
            ) -> Decision:
                self.captured_contexts.append(context)
                return Decision.RIDE

        strategy = ContextCapturingStrategy()
        engine = GameEngine(
            deck=deck,
            strategy=strategy,
            main_paytable=main_paytable,
            bonus_paytable=None,
            rng=rng,
        )

        custom_context = StrategyContext(
            session_profit=100.0,
            hands_played=50,
            streak=3,
            bankroll=500.0,
        )

        engine.play_hand(hand_id=1, base_bet=5.0, context=custom_context)

        # Strategy should have received the context twice (bet1 and bet2)
        assert len(strategy.captured_contexts) == 2
        for ctx in strategy.captured_contexts:
            assert ctx.session_profit == 100.0
            assert ctx.hands_played == 50
            assert ctx.streak == 3
            assert ctx.bankroll == 500.0


class TestBasicStrategyIntegration:
    """Integration tests with the actual BasicStrategy."""

    def test_basic_strategy_makes_decisions(
        self,
        deck: Deck,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        rng: random.Random,
    ) -> None:
        """BasicStrategy integrates correctly with GameEngine."""
        engine = GameEngine(
            deck=deck,
            strategy=BasicStrategy(),
            main_paytable=main_paytable,
            bonus_paytable=bonus_paytable,
            rng=rng,
        )

        # Play multiple hands with basic strategy
        for i in range(20):
            result = engine.play_hand(hand_id=i, base_bet=5.0, bonus_bet=1.0)

            # Should have valid decisions
            assert result.decision_bet1 in (Decision.RIDE, Decision.PULL)
            assert result.decision_bet2 in (Decision.RIDE, Decision.PULL)

            # Should have valid hand rank
            assert isinstance(result.final_hand_rank, FiveCardHandRank)

            # Net result should be calculated correctly
            main_net = (
                result.main_payout
                if result.main_payout > 0
                else -result.bets_at_risk
            )
            bonus_net = (
                result.bonus_payout if result.bonus_payout > 0 else -result.bonus_bet
            )
            assert result.net_result == main_net + bonus_net
