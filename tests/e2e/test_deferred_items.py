"""Tests for deferred code review items.

These tests address specific items deferred from previous PR code reviews:

From PR #78 (LIR-41: Dealer Discard Mechanics):
- DeckEmptyError edge case test
- YAML loader test for dealer section

From PR #111 (LIR-22: Simulation Results Aggregation):
- Integration test connecting aggregate_results() to SimulationController.run()
  (Note: This is also covered in test_full_simulation.py)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from let_it_ride.config.loader import load_config
from let_it_ride.config.models import (
    BankrollConfig,
    BettingSystemConfig,
    DealerConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    StrategyConfig,
)
from let_it_ride.core.deck import Deck, DeckEmptyError
from let_it_ride.simulation import SimulationController
from let_it_ride.simulation.aggregation import aggregate_results


class TestDeckEmptyErrorEdgeCases:
    """Tests for DeckEmptyError edge cases.

    Addresses deferred item from PR #78.
    """

    def test_deck_empty_error_raised_on_overdeal(self) -> None:
        """Verify DeckEmptyError is raised when dealing more cards than available."""
        import random

        deck = Deck()
        rng = random.Random(42)
        deck.shuffle(rng)

        # Deal until almost empty
        deck.deal(50)

        # Try to deal more than remaining (should have 2 cards)
        assert deck.cards_remaining() == 2

        with pytest.raises(DeckEmptyError) as exc_info:
            deck.deal(5)

        assert "Cannot deal 5 cards" in str(exc_info.value)
        assert "only 2 remaining" in str(exc_info.value)

    def test_deck_with_discard_sufficient_cards(self) -> None:
        """Verify deck handles discard + deal when cards are sufficient.

        Standard hand: 3 player + 2 community = 5 cards
        With 3 card discard: 3 + 5 = 8 cards needed
        Deck has 52 cards, so this should work.
        """
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=10,
                hands_per_session=5,
                random_seed=42,
            ),
            dealer=DealerConfig(discard_enabled=True, discard_cards=3),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=100.0,
                    loss_limit=200.0,
                    stop_on_insufficient_funds=True,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
        )

        # Should complete without error
        results = SimulationController(config).run()
        assert len(results.session_results) == 10

    def test_deck_empty_error_message_details(self) -> None:
        """Verify DeckEmptyError provides useful diagnostic information."""
        import random

        deck = Deck()
        rng = random.Random(42)
        deck.shuffle(rng)

        # Deal specific number
        deck.deal(45)
        remaining = deck.cards_remaining()

        try:
            deck.deal(remaining + 10)
        except DeckEmptyError as e:
            error_msg = str(e)
            # Error should include requested count
            assert str(remaining + 10) in error_msg
            # Error should include remaining count
            assert str(remaining) in error_msg

    def test_deck_deal_exact_remaining(self) -> None:
        """Verify dealing exactly the remaining cards works."""
        import random

        deck = Deck()
        rng = random.Random(42)
        deck.shuffle(rng)

        # Deal until few remain
        deck.deal(48)
        remaining = deck.cards_remaining()
        assert remaining == 4

        # Deal exactly remaining - should work
        cards = deck.deal(remaining)
        assert len(cards) == remaining
        assert deck.cards_remaining() == 0

    def test_deck_reset_restores_cards(self) -> None:
        """Verify deck reset restores all cards for subsequent hands."""
        import random

        deck = Deck()
        rng = random.Random(42)
        deck.shuffle(rng)

        # Deal many cards
        deck.deal(40)
        assert deck.cards_remaining() == 12

        # Reset
        deck.reset()
        assert deck.cards_remaining() == 52


class TestDealerConfigYAMLLoading:
    """Tests for YAML loader with dealer section.

    Addresses deferred item from PR #78.
    """

    def test_yaml_with_dealer_section_loads(self) -> None:
        """Verify YAML config with dealer section loads correctly."""
        config_content = """
simulation:
  num_sessions: 10
  hands_per_session: 10
  random_seed: 42

dealer:
  discard_enabled: true
  discard_cards: 3

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 200.0
  betting_system:
    type: flat

strategy:
  type: basic
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)

            config = load_config(config_path)

            assert config.dealer.discard_enabled is True
            assert config.dealer.discard_cards == 3

    def test_yaml_dealer_section_defaults(self) -> None:
        """Verify YAML config without dealer section uses defaults."""
        config_content = """
simulation:
  num_sessions: 10
  hands_per_session: 10
  random_seed: 42

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 200.0
  betting_system:
    type: flat

strategy:
  type: basic
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)

            config = load_config(config_path)

            # Default should be discard disabled
            # Note: discard_cards defaults to 3, but discard_enabled is False
            # so the cards setting doesn't matter
            assert config.dealer.discard_enabled is False
            assert config.dealer.discard_cards == 3  # Default is 3

    def test_yaml_dealer_disabled_with_nonzero_cards(self) -> None:
        """Verify dealer config allows discard_cards > 0 with discard_enabled=false."""
        config_content = """
simulation:
  num_sessions: 5
  hands_per_session: 5
  random_seed: 42

dealer:
  discard_enabled: false
  discard_cards: 5

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 200.0
  betting_system:
    type: flat

strategy:
  type: basic
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)

            config = load_config(config_path)

            # Should load but discard not applied
            assert config.dealer.discard_enabled is False
            assert config.dealer.discard_cards == 5

            # Run simulation - should work without discard
            results = SimulationController(config).run()
            assert len(results.session_results) == 5

    def test_yaml_dealer_various_discard_counts(self) -> None:
        """Verify dealer config with various discard card counts."""
        for discard_count in [1, 2, 5, 10]:
            config_content = f"""
simulation:
  num_sessions: 5
  hands_per_session: 5
  random_seed: 42

dealer:
  discard_enabled: true
  discard_cards: {discard_count}

bankroll:
  starting_amount: 500.0
  base_bet: 5.0
  stop_conditions:
    win_limit: 100.0
    loss_limit: 200.0
  betting_system:
    type: flat

strategy:
  type: basic
"""
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = Path(tmpdir) / f"config_{discard_count}.yaml"
                config_path.write_text(config_content)

                config = load_config(config_path)
                assert config.dealer.discard_cards == discard_count

                # Verify simulation still works
                results = SimulationController(config).run()
                assert len(results.session_results) == 5


class TestAggregateResultsIntegration:
    """Integration tests for aggregate_results with SimulationController.

    Addresses deferred item from PR #111.
    Note: Additional coverage in test_full_simulation.py
    """

    def test_aggregate_results_with_simulation_output(self) -> None:
        """Verify aggregate_results() works with actual SimulationController output."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=200,
                hands_per_session=50,
                random_seed=42,
                workers=2,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=200.0,
                    loss_limit=150.0,
                    stop_on_insufficient_funds=True,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
        )

        results = SimulationController(config).run()
        aggregate = aggregate_results(results.session_results)

        # Verify aggregate matches simulation results
        assert aggregate.total_sessions == 200
        assert aggregate.total_sessions == len(results.session_results)

        # Verify session counts sum correctly
        assert (
            aggregate.winning_sessions
            + aggregate.losing_sessions
            + aggregate.push_sessions
            == aggregate.total_sessions
        )

        # Verify total hands
        expected_hands = sum(r.hands_played for r in results.session_results)
        assert aggregate.total_hands == expected_hands

    def test_aggregate_statistics_calculation_accuracy(self) -> None:
        """Verify aggregate statistics calculations are accurate."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=100,
                hands_per_session=30,
                random_seed=99999,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=150.0,
                    loss_limit=100.0,
                    stop_on_insufficient_funds=True,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
        )

        results = SimulationController(config).run()
        aggregate = aggregate_results(results.session_results)

        # Manually calculate expected values
        profits = [r.session_profit for r in results.session_results]
        expected_min = min(profits)
        expected_max = max(profits)
        expected_net = sum(profits)

        # Verify calculations
        assert aggregate.session_profit_min == expected_min
        assert aggregate.session_profit_max == expected_max
        assert abs(aggregate.net_result - expected_net) < 0.01

    def test_aggregate_with_all_strategies(self) -> None:
        """Verify aggregate_results works with all strategy types."""
        from let_it_ride.config.models import (
            AggressiveStrategyConfig,
            ConservativeStrategyConfig,
        )

        # Build strategy configs with required sub-configs
        strategy_configs = [
            StrategyConfig(type="basic"),
            StrategyConfig(
                type="conservative",
                conservative=ConservativeStrategyConfig(),
            ),
            StrategyConfig(
                type="aggressive",
                aggressive=AggressiveStrategyConfig(),
            ),
            StrategyConfig(type="always_ride"),
            StrategyConfig(type="always_pull"),
        ]

        for strategy in strategy_configs:
            config = FullConfig(
                simulation=SimulationConfig(
                    num_sessions=20,
                    hands_per_session=20,
                    random_seed=42,
                ),
                bankroll=BankrollConfig(
                    starting_amount=500.0,
                    base_bet=5.0,
                    stop_conditions=StopConditionsConfig(
                        win_limit=150.0,
                        loss_limit=100.0,
                        stop_on_insufficient_funds=True,
                    ),
                    betting_system=BettingSystemConfig(type="flat"),
                ),
                strategy=strategy,
            )

            results = SimulationController(config).run()
            aggregate = aggregate_results(results.session_results)

            assert (
                aggregate.total_sessions == 20
            ), f"Failed for strategy: {strategy.type}"
            assert aggregate.total_hands > 0, f"Failed for strategy: {strategy.type}"

    def test_aggregate_with_bonus_enabled(self) -> None:
        """Verify aggregate_results works with bonus betting enabled."""
        from let_it_ride.config.models import AlwaysBonusConfig, BonusStrategyConfig

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=50,
                hands_per_session=30,
                random_seed=42,
            ),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=200.0,
                    loss_limit=150.0,
                    stop_on_insufficient_funds=True,
                ),
                betting_system=BettingSystemConfig(type="flat"),
            ),
            strategy=StrategyConfig(type="basic"),
            bonus_strategy=BonusStrategyConfig(
                enabled=True,
                type="always",
                always=AlwaysBonusConfig(amount=5.0),
            ),
        )

        results = SimulationController(config).run()
        aggregate = aggregate_results(results.session_results)

        assert aggregate.total_sessions == 50
        # Verify bonus wagering is tracked
        assert aggregate.bonus_wagered >= 0
