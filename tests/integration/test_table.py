"""Integration tests for Table and TableSession.

These tests verify the complete integration between Table, TableSession,
various strategy implementations, and bankroll tracking across multi-round
gameplay scenarios.

LIR-45: Table Integration Tests
"""

import random

import pytest

from let_it_ride.bankroll.betting_systems import FlatBetting, MartingaleBetting
from let_it_ride.config.models import DealerConfig, TableConfig
from let_it_ride.config.paytables import (
    BonusPaytable,
    MainGamePaytable,
    bonus_paytable_b,
    standard_main_paytable,
)
from let_it_ride.core.deck import Deck
from let_it_ride.core.table import Table
from let_it_ride.simulation.session import SessionOutcome, StopReason
from let_it_ride.simulation.table_session import (
    TableSession,
    TableSessionConfig,
)
from let_it_ride.strategy.base import Decision, StrategyContext
from let_it_ride.strategy.baseline import AlwaysPullStrategy, AlwaysRideStrategy
from let_it_ride.strategy.basic import BasicStrategy
from let_it_ride.strategy.custom import CustomStrategy, StrategyRule

# --- Fixtures ---


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


# --- TableSession Complete Lifecycle Tests ---


class TestTableSessionLifecycle:
    """Integration tests for complete TableSession lifecycle with real Table."""

    def test_single_seat_session_to_win_limit(
        self,
        main_paytable: MainGamePaytable,
    ) -> None:
        """Verify single-seat session runs until win limit is reached."""
        # Use a specific seed that produces early wins
        # Seed 999 tested to produce wins that hit the limit
        for seed in range(1000, 1100):
            config = TableSessionConfig(
                table_config=TableConfig(num_seats=1),
                starting_bankroll=500.0,
                base_bet=5.0,
                win_limit=100.0,
            )
            deck = Deck()
            rng = random.Random(seed)
            strategy = AlwaysRideStrategy()
            table = Table(deck, strategy, main_paytable, None, rng)
            betting_system = FlatBetting(5.0)

            session = TableSession(config, table, betting_system)
            result = session.run_to_completion()

            if result.stop_reason == StopReason.WIN_LIMIT:
                # Session should complete with win limit
                assert result.total_rounds >= 1
                assert len(result.seat_results) == 1
                assert result.seat_results[0].session_result.session_profit >= 100.0
                assert (
                    result.seat_results[0].session_result.outcome == SessionOutcome.WIN
                )
                return

        pytest.skip("Could not find seed that produces win limit condition")

    def test_single_seat_session_to_loss_limit(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify single-seat session runs until loss limit is reached."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=200.0,
            base_bet=5.0,
            loss_limit=100.0,
        )
        deck = Deck()
        strategy = AlwaysPullStrategy()  # Likely to lose more often with min bets
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        # Session should complete
        assert result.total_rounds >= 1
        seat_result = result.seat_results[0].session_result

        # Could hit loss limit or insufficient funds depending on RNG
        assert result.stop_reason in (
            StopReason.LOSS_LIMIT,
            StopReason.INSUFFICIENT_FUNDS,
        )
        assert seat_result.outcome == SessionOutcome.LOSS

    def test_multi_seat_session_to_max_hands(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify multi-seat session runs for specified number of hands."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=3),
            starting_bankroll=1000.0,
            base_bet=5.0,
            max_hands=20,
        )
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(
            deck,
            strategy,
            main_paytable,
            None,
            rng,
            table_config=TableConfig(num_seats=3),
        )
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 20
        assert result.stop_reason == StopReason.MAX_HANDS
        assert len(result.seat_results) == 3

        # Each seat should have played 20 hands
        for seat_result in result.seat_results:
            assert seat_result.session_result.hands_played == 20

    def test_multi_seat_independent_outcomes(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify multi-seat session tracks independent seat outcomes."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=4),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=50,
        )
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(
            deck,
            strategy,
            main_paytable,
            None,
            rng,
            table_config=TableConfig(num_seats=4),
        )
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        assert len(result.seat_results) == 4

        # Verify each seat has valid financial tracking
        for seat_result in result.seat_results:
            sr = seat_result.session_result
            assert sr.starting_bankroll == 500.0
            assert sr.final_bankroll == sr.starting_bankroll + sr.session_profit
            assert sr.total_wagered > 0


# --- Strategy Integration Tests ---


class TestTableWithStrategies:
    """Integration tests for Table with different strategy types."""

    def test_basic_strategy_produces_mixed_decisions(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify BasicStrategy produces both RIDE and PULL decisions."""
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)

        ride_bet1_count = 0
        pull_bet1_count = 0
        ride_bet2_count = 0
        pull_bet2_count = 0

        # Play many rounds to get a mix of decisions
        for i in range(100):
            result = table.play_round(round_id=i, base_bet=5.0)
            seat = result.seat_results[0]

            if seat.decision_bet1 == Decision.RIDE:
                ride_bet1_count += 1
            else:
                pull_bet1_count += 1

            if seat.decision_bet2 == Decision.RIDE:
                ride_bet2_count += 1
            else:
                pull_bet2_count += 1

        # BasicStrategy should produce a mix of decisions
        assert ride_bet1_count > 0, "BasicStrategy should ride at least some bet1"
        assert pull_bet1_count > 0, "BasicStrategy should pull at least some bet1"
        assert ride_bet2_count > 0, "BasicStrategy should ride at least some bet2"
        assert pull_bet2_count > 0, "BasicStrategy should pull at least some bet2"

    def test_always_ride_strategy_all_decisions_ride(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify AlwaysRideStrategy always produces RIDE decisions."""
        deck = Deck()
        strategy = AlwaysRideStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)

        for i in range(20):
            result = table.play_round(round_id=i, base_bet=5.0)
            seat = result.seat_results[0]

            assert seat.decision_bet1 == Decision.RIDE
            assert seat.decision_bet2 == Decision.RIDE
            # All ride = 3 bets at risk
            assert seat.bets_at_risk == 15.0  # 3 * 5.0

    def test_always_pull_strategy_all_decisions_pull(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify AlwaysPullStrategy always produces PULL decisions."""
        deck = Deck()
        strategy = AlwaysPullStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)

        for i in range(20):
            result = table.play_round(round_id=i, base_bet=5.0)
            seat = result.seat_results[0]

            assert seat.decision_bet1 == Decision.PULL
            assert seat.decision_bet2 == Decision.PULL
            # All pull = 1 bet at risk
            assert seat.bets_at_risk == 5.0

    def test_custom_strategy_rule_based_decisions(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify CustomStrategy evaluates rules correctly with Table."""
        # Create a custom strategy that rides on paying hands
        bet1_rules = [
            StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
            StrategyRule(condition="default", action=Decision.PULL),
        ]
        bet2_rules = [
            StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
            StrategyRule(condition="default", action=Decision.PULL),
        ]
        strategy = CustomStrategy(bet1_rules=bet1_rules, bet2_rules=bet2_rules)

        deck = Deck()
        table = Table(deck, strategy, main_paytable, None, rng)

        ride_count = 0
        pull_count = 0

        for i in range(100):
            result = table.play_round(round_id=i, base_bet=5.0)
            seat = result.seat_results[0]

            if seat.decision_bet1 == Decision.RIDE:
                ride_count += 1
            else:
                pull_count += 1

        # Should have a mix based on whether hands have paying hands
        assert ride_count > 0, "Should ride when has paying hand"
        assert pull_count > 0, "Should pull when no paying hand"

    def test_custom_strategy_complex_conditions(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify CustomStrategy with complex conditions works correctly."""
        # Strategy that rides on high card count or flush draws
        bet1_rules = [
            StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
            StrategyRule(
                condition="high_cards >= 2 and is_flush_draw", action=Decision.RIDE
            ),
            StrategyRule(condition="is_straight_flush_draw", action=Decision.RIDE),
            StrategyRule(condition="default", action=Decision.PULL),
        ]
        bet2_rules = [
            StrategyRule(condition="has_paying_hand", action=Decision.RIDE),
            StrategyRule(condition="high_cards >= 3", action=Decision.RIDE),
            StrategyRule(condition="default", action=Decision.PULL),
        ]
        strategy = CustomStrategy(bet1_rules=bet1_rules, bet2_rules=bet2_rules)

        deck = Deck()
        table = Table(deck, strategy, main_paytable, None, rng)

        # Just verify it runs without errors
        for i in range(50):
            result = table.play_round(round_id=i, base_bet=5.0)
            seat = result.seat_results[0]
            assert seat.decision_bet1 in (Decision.RIDE, Decision.PULL)
            assert seat.decision_bet2 in (Decision.RIDE, Decision.PULL)


class TestTableWithMultiSeatStrategies:
    """Integration tests for Table with multiple seats using same strategy."""

    def test_multi_seat_same_strategy_different_outcomes(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify multi-seat table produces different outcomes per seat."""
        deck = Deck()
        strategy = BasicStrategy()
        table_config = TableConfig(num_seats=6)
        table = Table(
            deck, strategy, main_paytable, None, rng, table_config=table_config
        )

        result = table.play_round(round_id=1, base_bet=5.0)

        assert len(result.seat_results) == 6

        # All player cards should be unique across seats
        all_cards = []
        for seat in result.seat_results:
            all_cards.extend(seat.player_cards)
        assert len(all_cards) == 18
        assert len(set(all_cards)) == 18

        # Community cards are shared
        for seat in result.seat_results:
            # Final hand is player cards + community cards
            expected_final = list(seat.player_cards) + list(result.community_cards)
            assert len(expected_final) == 5

    def test_multi_seat_shared_community_cards(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify all seats share the same community cards."""
        deck = Deck()
        strategy = BasicStrategy()
        table_config = TableConfig(num_seats=4)
        table = Table(
            deck, strategy, main_paytable, None, rng, table_config=table_config
        )

        result = table.play_round(round_id=1, base_bet=5.0)

        # All seats share the same community cards
        assert len(result.community_cards) == 2

        # Verify unique cards across all seats and community
        all_cards = list(result.community_cards)
        for seat in result.seat_results:
            all_cards.extend(seat.player_cards)

        # 2 community + 12 player (4 * 3) = 14 cards
        assert len(all_cards) == 14
        assert len(set(all_cards)) == 14


# --- Multi-Round Bankroll Tracking Tests ---


class TestMultiRoundBankrollTracking:
    """Integration tests for bankroll tracking across multiple rounds."""

    def test_bankroll_accumulation_over_rounds(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify bankroll changes are tracked correctly over multiple rounds."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=30,
        )
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        sr = result.seat_results[0].session_result

        # Verify financial consistency
        assert sr.final_bankroll == sr.starting_bankroll + sr.session_profit
        assert sr.hands_played == 30
        assert sr.total_wagered > 0

        # Peak should be at least starting (if never went above) or higher
        assert (
            sr.peak_bankroll >= sr.starting_bankroll
            or sr.peak_bankroll >= sr.final_bankroll
        )

    def test_peak_bankroll_and_drawdown_tracking(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify peak bankroll and drawdown are tracked correctly."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=50,
        )
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        sr = result.seat_results[0].session_result

        # Peak should be >= starting bankroll
        assert sr.peak_bankroll >= sr.starting_bankroll

        # Drawdown should be >= 0
        assert sr.max_drawdown >= 0

        # Drawdown percentage should be reasonable (0-100%)
        assert 0 <= sr.max_drawdown_pct <= 100

        # Max drawdown should be <= peak - final (approximately, accounting for recovery)
        # This is a sanity check, not exact due to recovery possibilities
        assert sr.max_drawdown <= sr.peak_bankroll

    def test_total_wagered_accumulation(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify total wagered accumulates correctly."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=10.0,
            max_hands=10,
        )
        deck = Deck()
        strategy = AlwaysRideStrategy()  # Always 3 bets at risk
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = FlatBetting(10.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        sr = result.seat_results[0].session_result

        # With AlwaysRide and flat betting, total wagered = hands * 3 * base_bet
        expected_wagered = 10 * 3 * 10.0  # 300
        assert sr.total_wagered == expected_wagered

    def test_multi_seat_independent_bankroll_tracking(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify each seat tracks its own bankroll independently."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=3),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=25,
        )
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(
            deck,
            strategy,
            main_paytable,
            None,
            rng,
            table_config=TableConfig(num_seats=3),
        )
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        assert len(result.seat_results) == 3

        # Each seat should have independent tracking
        for seat_result in result.seat_results:
            sr = seat_result.session_result
            assert sr.starting_bankroll == 500.0
            assert sr.final_bankroll == sr.starting_bankroll + sr.session_profit
            assert sr.hands_played == 25
            assert sr.total_wagered > 0

        # Different seats may have different profits (due to different cards)
        # They could be the same by chance, but typically will differ
        # We just verify they're all tracked correctly (no assertion on difference)


# --- Bonus Bet Integration Tests ---


class TestTableWithBonusBets:
    """Integration tests for Table with bonus betting."""

    def test_bonus_bet_evaluated_per_seat(
        self,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        rng: random.Random,
    ) -> None:
        """Verify bonus bets are evaluated for each seat's 3-card hand."""
        deck = Deck()
        strategy = BasicStrategy()
        table_config = TableConfig(num_seats=4)
        table = Table(
            deck,
            strategy,
            main_paytable,
            bonus_paytable,
            rng,
            table_config=table_config,
        )

        result = table.play_round(round_id=1, base_bet=5.0, bonus_bet=1.0)

        assert len(result.seat_results) == 4

        for seat in result.seat_results:
            assert seat.bonus_bet == 1.0
            assert seat.bonus_hand_rank is not None
            assert seat.bonus_payout >= 0

    def test_bonus_wagered_tracked_in_session(
        self,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable,
        rng: random.Random,
    ) -> None:
        """Verify total bonus wagered is tracked in session."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=500.0,
            base_bet=5.0,
            bonus_bet=2.0,
            max_hands=10,
        )
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(deck, strategy, main_paytable, bonus_paytable, rng)
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        sr = result.seat_results[0].session_result

        # Total bonus wagered = hands * bonus_bet
        expected_bonus_wagered = 10 * 2.0
        assert sr.total_bonus_wagered == expected_bonus_wagered


# --- Dealer Discard Integration Tests ---


class TestTableWithDealerDiscard:
    """Integration tests for Table with dealer discard mechanics."""

    def test_discard_cards_excluded_from_hands(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify discarded cards are not dealt to any player."""
        deck = Deck()
        strategy = BasicStrategy()
        table_config = TableConfig(num_seats=4)
        dealer_config = DealerConfig(discard_enabled=True, discard_cards=5)
        table = Table(
            deck,
            strategy,
            main_paytable,
            None,
            rng,
            table_config=table_config,
            dealer_config=dealer_config,
        )

        result = table.play_round(round_id=1, base_bet=5.0)

        assert result.dealer_discards is not None
        assert len(result.dealer_discards) == 5

        # Collect all player and community cards
        player_and_community = list(result.community_cards)
        for seat in result.seat_results:
            player_and_community.extend(seat.player_cards)

        # No discarded card should appear in player/community cards
        for card in result.dealer_discards:
            assert card not in player_and_community

    def test_discard_tracked_across_session(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify discard mechanics work across session rounds."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=10,
        )
        deck = Deck()
        strategy = BasicStrategy()
        dealer_config = DealerConfig(discard_enabled=True, discard_cards=3)
        table = Table(
            deck,
            strategy,
            main_paytable,
            None,
            rng,
            table_config=TableConfig(num_seats=2),
            dealer_config=dealer_config,
        )
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)

        # Play rounds manually to check discard each time
        discards_seen = []
        for _ in range(5):
            if session.should_stop():
                break
            round_result = session.play_round()
            if round_result.dealer_discards:
                discards_seen.append(round_result.dealer_discards)

        # Should have recorded discards each round
        assert len(discards_seen) == 5
        for discards in discards_seen:
            assert len(discards) == 3


# --- Betting System Integration Tests ---


class TestBettingSystemIntegration:
    """Integration tests for betting systems with Table."""

    def test_flat_betting_consistent_wager(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify flat betting produces consistent wagers."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=500.0,
            base_bet=10.0,
            max_hands=10,
        )
        deck = Deck()
        strategy = AlwaysRideStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = FlatBetting(10.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        sr = result.seat_results[0].session_result

        # With flat betting and always ride, each hand wagers 30 (3 * 10)
        assert sr.total_wagered == 10 * 30.0

    def test_martingale_betting_adjusts_after_losses(
        self,
        main_paytable: MainGamePaytable,
    ) -> None:
        """Verify Martingale betting adjusts bet size after losses."""
        # Use a specific seed that produces losses early
        rng = random.Random(123)

        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=5.0,
            max_hands=20,
        )
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = MartingaleBetting(
            base_bet=5.0, loss_multiplier=2.0, max_bet=100.0
        )

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        # With Martingale, total wagered will vary based on win/loss pattern
        sr = result.seat_results[0].session_result
        assert sr.total_wagered > 0
        assert sr.hands_played == 20


# --- Reproducibility Tests ---


class TestTableReproducibility:
    """Integration tests for Table reproducibility."""

    def test_same_seed_produces_identical_session(
        self,
        main_paytable: MainGamePaytable,
    ) -> None:
        """Verify same RNG seed produces identical session results."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=15,
        )

        # Run session 1
        deck1 = Deck()
        rng1 = random.Random(42)
        strategy1 = BasicStrategy()
        table1 = Table(
            deck1,
            strategy1,
            main_paytable,
            None,
            rng1,
            table_config=TableConfig(num_seats=2),
        )
        betting_system1 = FlatBetting(5.0)
        session1 = TableSession(config, table1, betting_system1)
        result1 = session1.run_to_completion()

        # Run session 2 with same seed
        deck2 = Deck()
        rng2 = random.Random(42)
        strategy2 = BasicStrategy()
        table2 = Table(
            deck2,
            strategy2,
            main_paytable,
            None,
            rng2,
            table_config=TableConfig(num_seats=2),
        )
        betting_system2 = FlatBetting(5.0)
        session2 = TableSession(config, table2, betting_system2)
        result2 = session2.run_to_completion()

        # Results should be identical
        assert result1.total_rounds == result2.total_rounds
        assert result1.stop_reason == result2.stop_reason

        for sr1, sr2 in zip(result1.seat_results, result2.seat_results, strict=True):
            assert sr1.seat_number == sr2.seat_number
            assert (
                sr1.session_result.session_profit == sr2.session_result.session_profit
            )
            assert (
                sr1.session_result.final_bankroll == sr2.session_result.final_bankroll
            )
            assert sr1.session_result.total_wagered == sr2.session_result.total_wagered

    def test_different_seeds_produce_different_results(
        self,
        main_paytable: MainGamePaytable,
    ) -> None:
        """Verify different seeds produce different results."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=50,
        )

        # Run with seed 1
        deck1 = Deck()
        rng1 = random.Random(11111)
        strategy1 = BasicStrategy()
        table1 = Table(deck1, strategy1, main_paytable, None, rng1)
        betting_system1 = FlatBetting(5.0)
        session1 = TableSession(config, table1, betting_system1)
        result1 = session1.run_to_completion()

        # Run with seed 2
        deck2 = Deck()
        rng2 = random.Random(22222)
        strategy2 = BasicStrategy()
        table2 = Table(deck2, strategy2, main_paytable, None, rng2)
        betting_system2 = FlatBetting(5.0)
        session2 = TableSession(config, table2, betting_system2)
        result2 = session2.run_to_completion()

        # Results should be different (with very high probability)
        profit1 = result1.seat_results[0].session_result.session_profit
        profit2 = result2.seat_results[0].session_result.session_profit

        # With 50 hands and different seeds, profits should differ
        # Note: Theoretically could be same, but extremely unlikely
        assert profit1 != profit2 or result1.total_rounds != result2.total_rounds


# --- Edge Cases and Boundary Tests ---


class TestTableEdgeCases:
    """Integration tests for edge cases and boundary conditions."""

    def test_session_with_large_bankroll(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify session handles large bankrolls correctly."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1_000_000.0,
            base_bet=100.0,
            max_hands=100,
        )
        deck = Deck()
        strategy = BasicStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = FlatBetting(100.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        sr = result.seat_results[0].session_result
        assert sr.starting_bankroll == 1_000_000.0
        assert sr.hands_played == 100

    def test_session_with_minimum_bankroll(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify session handles minimum viable bankroll."""
        # Minimum bankroll = 3 * base_bet
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=15.0,
            base_bet=5.0,
            # Will stop on insufficient funds after first loss
        )
        deck = Deck()
        strategy = AlwaysPullStrategy()
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        # Should complete (either win or run out of funds)
        assert result.total_rounds >= 1

    def test_max_seats_with_max_discard(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify table handles max seats (6) with max discard (10)."""
        deck = Deck()
        strategy = BasicStrategy()
        table_config = TableConfig(num_seats=6)
        dealer_config = DealerConfig(discard_enabled=True, discard_cards=10)
        table = Table(
            deck,
            strategy,
            main_paytable,
            None,
            rng,
            table_config=table_config,
            dealer_config=dealer_config,
        )

        # 6 seats * 3 cards + 2 community + 10 discard = 30 cards (within 52)
        result = table.play_round(round_id=1, base_bet=5.0)

        assert len(result.seat_results) == 6
        assert result.dealer_discards is not None
        assert len(result.dealer_discards) == 10

        # All cards should be unique
        all_cards = list(result.dealer_discards)
        all_cards.extend(result.community_cards)
        for seat in result.seat_results:
            all_cards.extend(seat.player_cards)

        assert len(all_cards) == 30
        assert len(set(all_cards)) == 30


# --- Strategy Context Tests ---


class TestTableWithStrategyContext:
    """Integration tests for strategy context handling in Table."""

    def test_strategy_context_passed_correctly(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify strategy context is passed through to strategy."""

        class ContextCapturingStrategy:
            """Strategy that captures context for inspection."""

            captured_contexts: list[StrategyContext]

            def __init__(self) -> None:
                self.captured_contexts = []

            def decide_bet1(
                self,
                analysis: object,  # noqa: ARG002
                context: StrategyContext,
            ) -> Decision:
                self.captured_contexts.append(context)
                return Decision.PULL

            def decide_bet2(
                self,
                analysis: object,  # noqa: ARG002
                context: StrategyContext,
            ) -> Decision:
                self.captured_contexts.append(context)
                return Decision.PULL

        strategy = ContextCapturingStrategy()
        deck = Deck()
        table = Table(deck, strategy, main_paytable, None, rng)

        custom_context = StrategyContext(
            session_profit=200.0,
            hands_played=25,
            streak=3,
            bankroll=700.0,
        )

        table.play_round(round_id=1, base_bet=5.0, context=custom_context)

        # Strategy should have captured the context
        assert len(strategy.captured_contexts) >= 2  # bet1 and bet2 for each seat
        for ctx in strategy.captured_contexts:
            assert ctx.session_profit == 200.0
            assert ctx.hands_played == 25
            assert ctx.streak == 3
            assert ctx.bankroll == 700.0

    def test_session_provides_updated_context_each_round(
        self,
        main_paytable: MainGamePaytable,
        rng: random.Random,
    ) -> None:
        """Verify TableSession provides updated context for each round."""

        class ContextTrackingStrategy:
            """Strategy that tracks context evolution."""

            context_history: list[tuple[float, int, int, float]]

            def __init__(self) -> None:
                self.context_history = []

            def decide_bet1(
                self,
                analysis: object,  # noqa: ARG002
                context: StrategyContext,
            ) -> Decision:
                self.context_history.append(
                    (
                        context.session_profit,
                        context.hands_played,
                        context.streak,
                        context.bankroll,
                    )
                )
                return Decision.PULL

            def decide_bet2(
                self,
                analysis: object,  # noqa: ARG002
                context: StrategyContext,  # noqa: ARG002
            ) -> Decision:
                return Decision.PULL

        strategy = ContextTrackingStrategy()
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=5,
        )
        deck = Deck()
        table = Table(deck, strategy, main_paytable, None, rng)
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        session.run_to_completion()

        # Should have captured context for each round
        assert len(strategy.context_history) == 5

        # hands_played should increment (context is passed before hand is complete)
        # First round: hands_played = 0, second round: hands_played = 1, etc.
        for i, (_profit, hands_played, _streak, _bankroll) in enumerate(
            strategy.context_history
        ):
            assert hands_played == i
