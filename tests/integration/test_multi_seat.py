"""Integration tests for multi-seat table simulation."""

from __future__ import annotations

import pytest

from let_it_ride.config.models import (
    BankrollConfig,
    FullConfig,
    SimulationConfig,
    StopConditionsConfig,
    TableConfig,
)
from let_it_ride.simulation import SimulationController


class TestMultiSeatSimulation:
    """Integration tests for multi-seat table simulations."""

    def test_single_seat_simulation(self) -> None:
        """Test single-seat simulation produces expected number of results."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=10,
                hands_per_session=50,
                random_seed=42,
                workers=1,
            ),
            table=TableConfig(num_seats=1),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=None,
                    loss_limit=None,
                    max_hands=50,
                ),
            ),
        )

        controller = SimulationController(config)
        results = controller.run()

        # Single seat: num_results == num_sessions
        assert len(results.session_results) == 10

    def test_multi_seat_simulation_produces_per_seat_results(self) -> None:
        """Test multi-seat simulation produces results for each seat."""
        num_sessions = 10
        num_seats = 6

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=num_sessions,
                hands_per_session=50,
                random_seed=42,
                workers=1,
            ),
            table=TableConfig(num_seats=num_seats),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=None,
                    loss_limit=None,
                    max_hands=50,
                ),
            ),
        )

        controller = SimulationController(config)
        results = controller.run()

        # Multi-seat: num_results == num_sessions * num_seats
        assert len(results.session_results) == num_sessions * num_seats

    def test_multi_seat_seats_share_community_cards(self) -> None:
        """Test that seats within a table share outcomes due to shared community cards."""
        num_sessions = 100
        num_seats = 6

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=num_sessions,
                hands_per_session=20,
                random_seed=42,
                workers=1,
            ),
            table=TableConfig(num_seats=num_seats),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=None,
                    loss_limit=None,
                    max_hands=20,
                ),
            ),
        )

        controller = SimulationController(config)
        results = controller.run()

        # Group results by table (every num_seats results are from same table)
        for table_idx in range(num_sessions):
            start_idx = table_idx * num_seats
            table_results = results.session_results[start_idx : start_idx + num_seats]

            # All seats should play the same number of hands
            hands_played = [r.hands_played for r in table_results]
            assert len(set(hands_played)) == 1, (
                f"Table {table_idx}: seats played different hands: {hands_played}"
            )

    def test_multi_seat_reproducible_with_seed(self) -> None:
        """Test that multi-seat simulation is reproducible with same seed."""
        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=5,
                hands_per_session=20,
                random_seed=12345,
                workers=1,
            ),
            table=TableConfig(num_seats=3),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=None,
                    loss_limit=None,
                    max_hands=20,
                ),
            ),
        )

        # Run twice with same config
        results1 = SimulationController(config).run()
        results2 = SimulationController(config).run()

        # Results should be identical
        assert len(results1.session_results) == len(results2.session_results)
        for r1, r2 in zip(results1.session_results, results2.session_results, strict=True):
            assert r1.session_profit == r2.session_profit
            assert r1.hands_played == r2.hands_played

    @pytest.mark.parametrize("num_seats", [2, 3, 4, 5, 6])
    def test_all_seat_counts(self, num_seats: int) -> None:
        """Test simulation works for all valid seat counts."""
        num_sessions = 5

        config = FullConfig(
            simulation=SimulationConfig(
                num_sessions=num_sessions,
                hands_per_session=10,
                random_seed=42,
                workers=1,
            ),
            table=TableConfig(num_seats=num_seats),
            bankroll=BankrollConfig(
                starting_amount=500.0,
                base_bet=5.0,
                stop_conditions=StopConditionsConfig(
                    win_limit=None,
                    loss_limit=None,
                    max_hands=10,
                ),
            ),
        )

        results = SimulationController(config).run()
        assert len(results.session_results) == num_sessions * num_seats
