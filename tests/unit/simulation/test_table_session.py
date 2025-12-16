"""Unit tests for TableSession multi-player session management."""

import random
from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from let_it_ride.bankroll.betting_systems import FlatBetting
from let_it_ride.config.models import TableConfig
from let_it_ride.config.paytables import standard_main_paytable
from let_it_ride.core.deck import Deck
from let_it_ride.core.table import PlayerSeat, Table, TableRoundResult
from let_it_ride.simulation.session import SessionOutcome, StopReason
from let_it_ride.simulation.table_session import (
    SeatSessionResult,
    TableSession,
    TableSessionConfig,
    TableSessionResult,
)
from let_it_ride.strategy.basic import BasicStrategy

# --- Test Fixtures ---


def create_mock_table(
    results_per_round: list[list[float]],
) -> Mock:
    """Create a mock Table that returns predetermined results.

    Args:
        results_per_round: List of rounds, each containing net_result for each seat.
            The number of elements in each inner list determines the number of seats.

    Returns:
        A mock Table.
    """
    mock = Mock()
    result_iter = iter(results_per_round)

    def play_round_side_effect(
        round_id: int,
        base_bet: float,
        bonus_bet: float = 0.0,
        context=None,  # noqa: ARG001
    ):
        round_results = next(result_iter)
        seat_results = []

        for seat_idx, net_result in enumerate(round_results):
            seat = Mock(spec=PlayerSeat)
            seat.seat_number = seat_idx + 1
            seat.net_result = net_result
            seat.bets_at_risk = base_bet * 3
            seat.bonus_bet = bonus_bet
            seat_results.append(seat)

        result = Mock(spec=TableRoundResult)
        result.round_id = round_id
        result.seat_results = tuple(seat_results)
        return result

    mock.play_round.side_effect = play_round_side_effect
    return mock


# --- TableSessionConfig Tests ---


class TestTableSessionConfigInitialization:
    """Tests for TableSessionConfig initialization."""

    def test_create_minimal_config(self) -> None:
        """Verify TableSessionConfig can be created with minimal required fields."""
        table_config = TableConfig(num_seats=1)
        config = TableSessionConfig(
            table_config=table_config,
            starting_bankroll=1000.0,
            base_bet=25.0,
        )
        assert config.table_config == table_config
        assert config.starting_bankroll == 1000.0
        assert config.base_bet == 25.0
        assert config.win_limit is None
        assert config.loss_limit is None
        assert config.max_hands is None
        assert config.stop_on_insufficient_funds is True
        assert config.bonus_bet == 0.0

    def test_create_full_config(self) -> None:
        """Verify TableSessionConfig can be created with all fields."""
        table_config = TableConfig(num_seats=3)
        config = TableSessionConfig(
            table_config=table_config,
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=500.0,
            loss_limit=250.0,
            max_hands=100,
            stop_on_insufficient_funds=False,
            bonus_bet=5.0,
        )
        assert config.table_config.num_seats == 3
        assert config.starting_bankroll == 1000.0
        assert config.base_bet == 25.0
        assert config.win_limit == 500.0
        assert config.loss_limit == 250.0
        assert config.max_hands == 100
        assert config.stop_on_insufficient_funds is False
        assert config.bonus_bet == 5.0

    def test_config_is_frozen(self) -> None:
        """Verify TableSessionConfig is immutable."""
        config = TableSessionConfig(
            table_config=TableConfig(),
            starting_bankroll=1000.0,
            base_bet=25.0,
        )
        with pytest.raises(FrozenInstanceError):
            config.starting_bankroll = 500.0  # type: ignore[misc]

    def test_config_fields_accessible(self) -> None:
        """Verify TableSessionConfig fields are accessible."""
        # Note: TableSessionConfig contains a Pydantic TableConfig,
        # which is not hashable. We verify fields are accessible instead.
        config = TableSessionConfig(
            table_config=TableConfig(),
            starting_bankroll=1000.0,
            base_bet=25.0,
        )
        assert config.table_config.num_seats == 1
        assert config.starting_bankroll == 1000.0
        assert config.base_bet == 25.0


class TestTableSessionConfigValidation:
    """Tests for TableSessionConfig validation."""

    def test_zero_starting_bankroll_raises(self) -> None:
        """Verify zero starting bankroll raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=0.0,
                base_bet=25.0,
            )
        assert "starting_bankroll must be positive" in str(exc_info.value)

    def test_negative_starting_bankroll_raises(self) -> None:
        """Verify negative starting bankroll raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=-100.0,
                base_bet=25.0,
            )
        assert "starting_bankroll must be positive" in str(exc_info.value)

    def test_zero_base_bet_raises(self) -> None:
        """Verify zero base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=0.0,
            )
        assert "base_bet must be positive" in str(exc_info.value)

    def test_negative_base_bet_raises(self) -> None:
        """Verify negative base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=-25.0,
            )
        assert "base_bet must be positive" in str(exc_info.value)

    def test_zero_win_limit_raises(self) -> None:
        """Verify zero win limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=25.0,
                win_limit=0.0,
            )
        assert "win_limit must be positive" in str(exc_info.value)

    def test_negative_win_limit_raises(self) -> None:
        """Verify negative win limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=25.0,
                win_limit=-100.0,
            )
        assert "win_limit must be positive" in str(exc_info.value)

    def test_zero_loss_limit_raises(self) -> None:
        """Verify zero loss limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=25.0,
                loss_limit=0.0,
            )
        assert "loss_limit must be positive" in str(exc_info.value)

    def test_negative_loss_limit_raises(self) -> None:
        """Verify negative loss limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=25.0,
                loss_limit=-100.0,
            )
        assert "loss_limit must be positive" in str(exc_info.value)

    def test_zero_max_hands_raises(self) -> None:
        """Verify zero max hands raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=25.0,
                max_hands=0,
            )
        assert "max_hands must be positive" in str(exc_info.value)

    def test_negative_max_hands_raises(self) -> None:
        """Verify negative max hands raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=25.0,
                max_hands=-10,
            )
        assert "max_hands must be positive" in str(exc_info.value)

    def test_negative_bonus_bet_raises(self) -> None:
        """Verify negative bonus bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=25.0,
                bonus_bet=-5.0,
            )
        assert "bonus_bet cannot be negative" in str(exc_info.value)

    def test_no_stop_conditions_raises(self) -> None:
        """Verify config with no stop conditions raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=1000.0,
                base_bet=25.0,
                stop_on_insufficient_funds=False,
            )
        assert "At least one stop condition" in str(exc_info.value)

    def test_insufficient_starting_bankroll_raises(self) -> None:
        """Verify starting bankroll less than minimum bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=50.0,
                base_bet=25.0,  # Requires 75 (25 * 3)
            )
        assert "must be at least" in str(exc_info.value)

    def test_starting_bankroll_covers_bonus(self) -> None:
        """Verify starting bankroll must cover base bet * 3 + bonus bet."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(),
                starting_bankroll=80.0,
                base_bet=25.0,
                bonus_bet=10.0,  # Requires 85 (75 + 10)
            )
        assert "must be at least" in str(exc_info.value)


# --- Result Dataclass Tests ---


class TestSeatSessionResult:
    """Tests for SeatSessionResult dataclass."""

    def test_seat_session_result_is_frozen(self) -> None:
        """Verify SeatSessionResult is immutable."""
        from let_it_ride.simulation.session import SessionResult

        session_result = SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=10,
            starting_bankroll=1000.0,
            final_bankroll=1500.0,
            session_profit=500.0,
            total_wagered=750.0,
            total_bonus_wagered=0.0,
            peak_bankroll=1500.0,
            max_drawdown=50.0,
            max_drawdown_pct=5.0,
        )

        seat_result = SeatSessionResult(
            seat_number=1,
            session_result=session_result,
        )

        with pytest.raises(FrozenInstanceError):
            seat_result.seat_number = 2  # type: ignore[misc]


class TestTableSessionResult:
    """Tests for TableSessionResult dataclass."""

    def test_table_session_result_is_frozen(self) -> None:
        """Verify TableSessionResult is immutable."""
        table_result = TableSessionResult(
            seat_results=(),
            total_rounds=10,
            stop_reason=StopReason.MAX_HANDS,
        )

        with pytest.raises(FrozenInstanceError):
            table_result.total_rounds = 20  # type: ignore[misc]


# --- TableSession Single-Seat Tests ---


class TestTableSessionSingleSeat:
    """Tests for TableSession with single seat (backwards compatibility)."""

    def test_single_seat_initialization(self) -> None:
        """Verify single-seat TableSession initializes correctly."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=10,
        )
        mock_table = create_mock_table([[0.0] for _ in range(10)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)

        assert session.rounds_played == 0
        assert session.is_complete is False

    def test_single_seat_win_limit_triggered(self) -> None:
        """Verify single-seat session stops at win limit."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
        )
        # Win 50 each round
        mock_table = create_mock_table([[50.0], [50.0], [50.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 2
        assert result.stop_reason == StopReason.WIN_LIMIT
        assert len(result.seat_results) == 1
        assert result.seat_results[0].session_result.session_profit == 100.0

    def test_single_seat_loss_limit_triggered(self) -> None:
        """Verify single-seat session stops at loss limit."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            loss_limit=100.0,
        )
        # Lose 50 each round
        mock_table = create_mock_table([[-50.0], [-50.0], [-50.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 2
        assert result.stop_reason == StopReason.LOSS_LIMIT
        assert result.seat_results[0].session_result.session_profit == -100.0

    def test_single_seat_max_hands_triggered(self) -> None:
        """Verify single-seat session stops at max hands."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=5,
        )
        mock_table = create_mock_table([[0.0] for _ in range(10)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 5
        assert result.stop_reason == StopReason.MAX_HANDS

    def test_single_seat_insufficient_funds(self) -> None:
        """Verify single-seat session stops on insufficient funds."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=100.0,  # Just enough for 1 hand (25 * 3 = 75)
            base_bet=25.0,
        )
        # Big loss drains bankroll
        mock_table = create_mock_table([[-75.0], [0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 1
        assert result.stop_reason == StopReason.INSUFFICIENT_FUNDS

    def test_single_seat_outcome_win(self) -> None:
        """Verify WIN outcome when session profit is positive."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        mock_table = create_mock_table([[100.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_results[0].session_result.outcome == SessionOutcome.WIN

    def test_single_seat_outcome_loss(self) -> None:
        """Verify LOSS outcome when session profit is negative."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        mock_table = create_mock_table([[-50.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_results[0].session_result.outcome == SessionOutcome.LOSS

    def test_single_seat_outcome_push(self) -> None:
        """Verify PUSH outcome when session profit is zero."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        mock_table = create_mock_table([[0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_results[0].session_result.outcome == SessionOutcome.PUSH


# --- TableSession Multi-Seat Tests ---


class TestTableSessionMultiSeat:
    """Tests for TableSession with multiple seats."""

    def test_multi_seat_initialization(self) -> None:
        """Verify multi-seat TableSession initializes correctly."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=3),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=10,
        )
        mock_table = create_mock_table([[0.0, 0.0, 0.0] for _ in range(10)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)

        assert session.rounds_played == 0
        assert session.is_complete is False

    def test_multi_seat_all_hit_max_hands(self) -> None:
        """Verify session stops when max_hands is reached for all seats."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=3),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=5,
        )
        mock_table = create_mock_table([[0.0, 0.0, 0.0] for _ in range(10)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 5
        assert result.stop_reason == StopReason.MAX_HANDS
        assert len(result.seat_results) == 3

    def test_multi_seat_independent_bankrolls(self) -> None:
        """Verify each seat has independent bankroll tracking."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=3),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )
        # Seat 1 wins, Seat 2 loses, Seat 3 breaks even
        mock_table = create_mock_table(
            [
                [100.0, -50.0, 0.0],
                [100.0, -50.0, 0.0],
                [100.0, -50.0, 0.0],
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Check independent bankroll tracking
        assert result.seat_results[0].session_result.session_profit == 300.0
        assert result.seat_results[0].session_result.final_bankroll == 1300.0
        assert result.seat_results[1].session_result.session_profit == -150.0
        assert result.seat_results[1].session_result.final_bankroll == 850.0
        assert result.seat_results[2].session_result.session_profit == 0.0
        assert result.seat_results[2].session_result.final_bankroll == 1000.0

    def test_multi_seat_waits_for_all_to_stop(self) -> None:
        """Verify session waits for all seats to hit stop conditions."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=200.0,
            max_hands=100,  # High max to ensure win limit triggers first
        )
        # Seat 1 hits win limit after 2 rounds (100+100=200)
        # Seat 2 hits win limit after 4 rounds (50*4=200)
        mock_table = create_mock_table(
            [
                [100.0, 50.0],
                [100.0, 50.0],
                [0.0, 50.0],  # Seat 1 already stopped
                [0.0, 50.0],
                [0.0, 0.0],
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Session should run until seat 2 also hits win limit
        assert result.total_rounds == 4
        assert result.stop_reason == StopReason.WIN_LIMIT

    def test_multi_seat_different_stop_reasons(self) -> None:
        """Verify each seat can have different stop reasons."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=200.0,  # Low to trigger insufficient funds
            base_bet=25.0,
            win_limit=150.0,
        )
        # Seat 1 hits win limit, Seat 2 runs out of funds
        mock_table = create_mock_table(
            [
                [100.0, -75.0],
                [100.0, -75.0],
                [0.0, 0.0],
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Check different stop reasons per seat
        assert result.seat_results[0].session_result.stop_reason == StopReason.WIN_LIMIT
        assert (
            result.seat_results[1].session_result.stop_reason
            == StopReason.INSUFFICIENT_FUNDS
        )

    def test_multi_seat_correct_seat_numbers(self) -> None:
        """Verify seat numbers are correctly assigned."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=4),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        mock_table = create_mock_table([[0.0, 0.0, 0.0, 0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_results[0].seat_number == 1
        assert result.seat_results[1].seat_number == 2
        assert result.seat_results[2].seat_number == 3
        assert result.seat_results[3].seat_number == 4


# --- TableSession State Tests ---


class TestTableSessionState:
    """Tests for TableSession state management."""

    def test_play_round_increments_counter(self) -> None:
        """Verify play_round increments rounds_played."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=10,
        )
        mock_table = create_mock_table([[0.0] for _ in range(10)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)

        session.play_round()
        assert session.rounds_played == 1

        session.play_round()
        assert session.rounds_played == 2

    def test_play_round_after_complete_raises(self) -> None:
        """Verify play_round raises error after session is complete."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        mock_table = create_mock_table([[0.0], [0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        session.run_to_completion()

        with pytest.raises(RuntimeError) as exc_info:
            session.play_round()
        assert "session is already complete" in str(exc_info.value)

    def test_stop_reason_returns_none_before_stop(self) -> None:
        """Verify stop_reason returns None before session stops."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=10,
        )
        mock_table = create_mock_table([[0.0] for _ in range(10)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)

        assert session.stop_reason is None

    def test_is_complete_true_after_run_to_completion(self) -> None:
        """Verify is_complete is True after run_to_completion."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        mock_table = create_mock_table([[0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        session.run_to_completion()

        assert session.is_complete is True


# --- TableSession Bankroll Tracking Tests ---


class TestTableSessionBankrollTracking:
    """Tests for TableSession bankroll tracking."""

    def test_peak_bankroll_tracked(self) -> None:
        """Verify peak bankroll is tracked correctly."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )
        # Win, then lose, then lose more
        mock_table = create_mock_table([[100.0], [-50.0], [-50.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_results[0].session_result.peak_bankroll == 1100.0

    def test_max_drawdown_tracked(self) -> None:
        """Verify max drawdown is tracked correctly."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=4,
        )
        # Win to peak, then lose, then win again
        mock_table = create_mock_table([[200.0], [-150.0], [-100.0], [50.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Peak was 1200, dropped to 950 (-250 drawdown)
        assert result.seat_results[0].session_result.max_drawdown == 250.0

    def test_total_wagered_tracked(self) -> None:
        """Verify total wagered is accumulated."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )
        mock_table = create_mock_table([[0.0], [0.0], [0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # 3 rounds * 75 (base_bet * 3) = 225
        assert result.seat_results[0].session_result.total_wagered == 225.0


# --- Integration Test with Real Table ---


class TestTableSessionIntegration:
    """Integration tests with real Table and components."""

    def test_with_real_table(self, rng: random.Random) -> None:
        """Verify TableSession works with real Table."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=5.0,
            max_hands=10,
        )

        deck = Deck()
        strategy = BasicStrategy()
        paytable = standard_main_paytable()
        table = Table(deck, strategy, paytable, None, rng)
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 10
        assert len(result.seat_results) == 2
        assert result.seat_results[0].seat_number == 1
        assert result.seat_results[1].seat_number == 2

    def test_single_seat_matches_session_behavior(self, rng: random.Random) -> None:
        """Verify single-seat TableSession behaves like Session."""
        # This is the backwards compatibility test
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=500.0,
            base_bet=5.0,
            max_hands=5,
        )

        deck = Deck()
        strategy = BasicStrategy()
        paytable = standard_main_paytable()
        table = Table(deck, strategy, paytable, None, rng)
        betting_system = FlatBetting(5.0)

        session = TableSession(config, table, betting_system)
        result = session.run_to_completion()

        # Should have exactly 1 seat result
        assert len(result.seat_results) == 1

        # The seat result should have all expected fields
        seat_result = result.seat_results[0].session_result
        assert seat_result.hands_played == 5
        assert seat_result.starting_bankroll == 500.0
        assert isinstance(seat_result.outcome, SessionOutcome)
        assert isinstance(seat_result.stop_reason, StopReason)


# --- Streak Tracking Tests ---


class TestSeatStateStreakTracking:
    """Tests for _SeatState.update_streak() via calculate_new_streak()."""

    def test_streak_starts_at_zero(self) -> None:
        """Verify initial streak is zero."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        assert state.streak == 0

    def test_streak_win_after_fresh_start(self) -> None:
        """Verify streak becomes +1 on first win."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(50.0)
        assert state.streak == 1

    def test_streak_loss_after_fresh_start(self) -> None:
        """Verify streak becomes -1 on first loss."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(-50.0)
        assert state.streak == -1

    def test_streak_consecutive_wins(self) -> None:
        """Verify streak increments on consecutive wins."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(50.0)  # +1
        state.update_streak(50.0)  # +2
        state.update_streak(50.0)  # +3
        assert state.streak == 3

    def test_streak_consecutive_losses(self) -> None:
        """Verify streak decrements on consecutive losses."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(-50.0)  # -1
        state.update_streak(-50.0)  # -2
        state.update_streak(-50.0)  # -3
        assert state.streak == -3

    def test_streak_win_after_loss_resets(self) -> None:
        """Verify streak resets to +1 after a loss."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(-50.0)  # -1
        state.update_streak(-50.0)  # -2
        state.update_streak(50.0)  # Should reset to +1
        assert state.streak == 1

    def test_streak_loss_after_win_resets(self) -> None:
        """Verify streak resets to -1 after a win."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(50.0)  # +1
        state.update_streak(50.0)  # +2
        state.update_streak(-50.0)  # Should reset to -1
        assert state.streak == -1

    def test_push_preserves_positive_streak(self) -> None:
        """Verify push does not reset positive streak."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(50.0)  # +1
        state.update_streak(50.0)  # +2
        state.update_streak(0.0)  # Push - should stay +2
        assert state.streak == 2

    def test_push_preserves_negative_streak(self) -> None:
        """Verify push does not reset negative streak."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(-50.0)  # -1
        state.update_streak(-50.0)  # -2
        state.update_streak(0.0)  # Push - should stay -2
        assert state.streak == -2

    def test_push_on_zero_streak_stays_zero(self) -> None:
        """Verify push on fresh start keeps streak at zero."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0)
        state.update_streak(0.0)  # Push
        assert state.streak == 0


# --- Stopped Seat Behavior Tests ---


class TestStoppedSeatBehavior:
    """Tests for stopped seat handling during rounds."""

    def test_stopped_seat_not_updated_in_subsequent_rounds(self) -> None:
        """Verify stopped seats do not receive updates from rounds after stopping."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            max_hands=100,
        )
        # Seat 1 hits win limit after round 1 (100 profit)
        # Seat 2 continues for more rounds
        mock_table = create_mock_table(
            [
                [100.0, 10.0],  # Seat 1 stops after this
                [50.0, 10.0],  # Seat 1 should NOT get this 50
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 100.0],  # Seat 2 hits win limit
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Seat 1 should have stopped at 100 profit, NOT 550 (100 + 9*50)
        seat1_result = result.seat_results[0].session_result
        assert seat1_result.session_profit == 100.0
        assert seat1_result.stop_reason == StopReason.WIN_LIMIT

        # Seat 1's total_wagered should only reflect 1 round (75), not 10 rounds
        assert seat1_result.total_wagered == 75.0

    def test_stopped_seat_bankroll_unchanged(self) -> None:
        """Verify stopped seat's bankroll doesn't change in subsequent rounds."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            loss_limit=100.0,
            max_hands=100,
        )
        # Seat 1 hits loss limit after round 2
        # Seat 2 keeps going
        mock_table = create_mock_table(
            [
                [-50.0, 0.0],
                [-50.0, 0.0],  # Seat 1 stops here at -100
                [-100.0, 0.0],  # This -100 should NOT affect seat 1
                [-100.0, -100.0],  # Seat 2 stops
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Seat 1's final bankroll should be 900 (1000 - 100), not lower
        seat1_result = result.seat_results[0].session_result
        assert seat1_result.final_bankroll == 900.0


# --- Bonus Wagering Tests ---


class TestBonusWageredTracking:
    """Tests for total_bonus_wagered tracking."""

    def test_total_bonus_wagered_tracked_per_seat(self) -> None:
        """Verify total_bonus_wagered is accumulated correctly for each seat."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            bonus_bet=5.0,
            max_hands=3,
        )
        mock_table = create_mock_table(
            [
                [0.0, 0.0],
                [0.0, 0.0],
                [0.0, 0.0],
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Each seat should have 3 rounds * 5.0 bonus = 15.0
        assert result.seat_results[0].session_result.total_bonus_wagered == 15.0
        assert result.seat_results[1].session_result.total_bonus_wagered == 15.0

    def test_bonus_wagered_not_tracked_when_zero(self) -> None:
        """Verify bonus_wagered is zero when no bonus bet configured."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            bonus_bet=0.0,
            max_hands=3,
        )
        mock_table = create_mock_table([[0.0], [0.0], [0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_results[0].session_result.total_bonus_wagered == 0.0

    def test_stopped_seat_bonus_wagered_correct(self) -> None:
        """Verify stopped seat's bonus_wagered only reflects rounds played."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            bonus_bet=10.0,
            win_limit=100.0,
            max_hands=100,
        )
        # Seat 1 stops after round 1, Seat 2 continues
        mock_table = create_mock_table(
            [
                [100.0, 10.0],  # Seat 1 stops
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 10.0],
                [50.0, 100.0],  # Seat 2 stops
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Seat 1 only played 1 round, so bonus wagered = 10
        assert result.seat_results[0].session_result.total_bonus_wagered == 10.0
        # Seat 2 played 10 rounds, so bonus wagered = 100
        assert result.seat_results[1].session_result.total_bonus_wagered == 100.0


# --- Betting System Tests ---


class TestBettingSystemBehavior:
    """Tests for betting system behavior in TableSession."""

    def test_betting_system_reset_called_on_init(self) -> None:
        """Verify betting system reset() is called during initialization."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        mock_table = create_mock_table([[0.0]])
        mock_betting = Mock()
        mock_betting.get_bet.return_value = 25.0

        TableSession(config, mock_table, mock_betting)

        mock_betting.reset.assert_called_once()


# --- Max Drawdown Percentage Tests ---


class TestMaxDrawdownPercentage:
    """Tests for max_drawdown_pct accuracy."""

    def test_max_drawdown_pct_tracked(self) -> None:
        """Verify max drawdown percentage is calculated correctly."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=4,
        )
        # Peak at 1200, then drop to 900 = 300/1200 = 25%
        mock_table = create_mock_table([[200.0], [-100.0], [-200.0], [50.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Peak was 1200, dropped to 900, max_drawdown = 300
        # max_drawdown_pct = 300 / 1200 * 100 = 25.0%
        assert result.seat_results[0].session_result.max_drawdown == 300.0
        assert result.seat_results[0].session_result.max_drawdown_pct == 25.0


# --- Simultaneous Stop Tests ---


class TestSimultaneousStop:
    """Tests for multiple seats stopping simultaneously."""

    def test_stop_reason_when_all_seats_stop_simultaneously(self) -> None:
        """Verify stop_reason selection when all seats hit max_hands together."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=3),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=2,
        )
        mock_table = create_mock_table(
            [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # All seats stop for same reason
        assert result.stop_reason == StopReason.MAX_HANDS
        assert all(
            sr.session_result.stop_reason == StopReason.MAX_HANDS
            for sr in result.seat_results
        )

    def test_last_seat_stop_reason_used(self) -> None:
        """Verify the last seat's stop reason becomes the session stop reason."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=200.0,
            base_bet=25.0,
            win_limit=100.0,
            loss_limit=100.0,
        )
        # Both stop in same round: Seat 1 wins, Seat 2 loses
        # Last seat (2) has loss_limit, so that should be session stop reason
        mock_table = create_mock_table(
            [
                [50.0, -50.0],
                [50.0, -50.0],  # Both stop here
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_results[0].session_result.stop_reason == StopReason.WIN_LIMIT
        assert (
            result.seat_results[1].session_result.stop_reason == StopReason.LOSS_LIMIT
        )
        # Session stop reason should be from last seat (reversed iteration)
        assert result.stop_reason == StopReason.LOSS_LIMIT


# --- Progressive Betting Integration Tests ---


class TestProgressiveBettingIntegration:
    """Tests for progressive betting system integration."""

    def test_shared_betting_system_with_martingale(self) -> None:
        """Verify progressive betting system is shared correctly across seats."""
        from let_it_ride.bankroll.betting_systems import MartingaleBetting

        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=10.0,
            max_hands=3,
        )
        # Martingale doubles after loss
        # Round 1: bet 10, Seat 1 loses -> next bet should be 20
        # Round 2: bet 20, Seat 1 wins -> bet resets to 10
        # Round 3: bet 10
        mock_table = create_mock_table(
            [
                [-30.0, -30.0],  # Both lose 30 (3 * 10)
                [60.0, 60.0],  # Both win 60 (3 * 20)
                [-30.0, -30.0],  # Both lose 30 (3 * 10)
            ]
        )
        betting_system = MartingaleBetting(
            base_bet=10.0, loss_multiplier=2.0, max_bet=100.0
        )

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Both seats use the shared betting system progression
        # Final profit: -30 + 60 - 30 = 0
        assert result.seat_results[0].session_result.session_profit == 0.0
        assert result.seat_results[1].session_result.session_profit == 0.0


# --- Seat Replacement Mode Tests ---


class TestTableSessionConfigSeatReplacement:
    """Tests for TableSessionConfig with table_total_rounds."""

    def test_config_with_table_total_rounds(self) -> None:
        """Verify config accepts table_total_rounds parameter."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=100,
        )
        assert config.table_total_rounds == 100

    def test_config_table_total_rounds_none_by_default(self) -> None:
        """Verify table_total_rounds defaults to None."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=10,
        )
        assert config.table_total_rounds is None

    def test_config_zero_table_total_rounds_raises(self) -> None:
        """Verify zero table_total_rounds raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(num_seats=2),
                starting_bankroll=1000.0,
                base_bet=25.0,
                win_limit=100.0,
                table_total_rounds=0,
            )
        assert "table_total_rounds must be positive" in str(exc_info.value)

    def test_config_negative_table_total_rounds_raises(self) -> None:
        """Verify negative table_total_rounds raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TableSessionConfig(
                table_config=TableConfig(num_seats=2),
                starting_bankroll=1000.0,
                base_bet=25.0,
                win_limit=100.0,
                table_total_rounds=-10,
            )
        assert "table_total_rounds must be positive" in str(exc_info.value)


class TestSeatReplacementMode:
    """Tests for seat replacement mode behavior."""

    def test_seat_replacement_mode_enabled_when_table_total_rounds_set(self) -> None:
        """Verify seat_replacement_mode is True when table_total_rounds is configured."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=50,
        )
        mock_table = create_mock_table([[0.0, 0.0] for _ in range(50)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        assert session.seat_replacement_mode is True

    def test_seat_replacement_mode_disabled_by_default(self) -> None:
        """Verify seat_replacement_mode is False when table_total_rounds is None."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=10,
        )
        mock_table = create_mock_table([[0.0, 0.0] for _ in range(10)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        assert session.seat_replacement_mode is False

    def test_seat_replacement_stops_at_table_total_rounds(self) -> None:
        """Verify table stops at table_total_rounds regardless of seat states."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=10000.0,  # Very high, won't be reached
            table_total_rounds=5,
        )
        mock_table = create_mock_table([[0.0, 0.0] for _ in range(10)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 5
        assert result.stop_reason == StopReason.TABLE_ROUNDS_COMPLETE

    def test_seat_replacement_resets_seat_on_win_limit(self) -> None:
        """Verify seat is reset when hitting win limit in replacement mode."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=10,
        )
        # Win 100 in round 1, triggering reset
        # Then play 9 more rounds with small wins
        mock_table = create_mock_table([[100.0]] + [[10.0] for _ in range(9)])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Should have completed sessions from resets
        assert result.seat_sessions is not None
        seat1_sessions = result.seat_sessions[1]

        # First session should have hit win limit
        assert len(seat1_sessions) >= 1
        assert seat1_sessions[0].session_result.stop_reason == StopReason.WIN_LIMIT
        assert seat1_sessions[0].session_result.session_profit == 100.0

    def test_seat_replacement_tracks_multiple_sessions_per_seat(self) -> None:
        """Verify multiple sessions are tracked when seat resets multiple times."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=6,
        )
        # Win 100 in rounds 1, 3, 5 - triggering 3 resets
        mock_table = create_mock_table(
            [
                [100.0],  # Round 0: Win limit, reset
                [50.0],  # Round 1: In new session
                [100.0],  # Round 2: Win limit again, reset
                [30.0],  # Round 3: In new session
                [100.0],  # Round 4: Win limit again, reset
                [20.0],  # Round 5: Partial session
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None
        seat1_sessions = result.seat_sessions[1]

        # Should have 3 completed sessions + 1 in-progress
        assert len(seat1_sessions) == 4

        # Check completed sessions
        assert seat1_sessions[0].session_result.stop_reason == StopReason.WIN_LIMIT
        assert seat1_sessions[0].session_result.hands_played == 1
        assert seat1_sessions[0].session_result.session_profit == 100.0

        assert seat1_sessions[1].session_result.stop_reason == StopReason.WIN_LIMIT
        assert seat1_sessions[1].session_result.hands_played == 2
        assert seat1_sessions[1].session_result.session_profit == 150.0  # 50 + 100

        assert seat1_sessions[2].session_result.stop_reason == StopReason.WIN_LIMIT
        assert seat1_sessions[2].session_result.hands_played == 2
        assert seat1_sessions[2].session_result.session_profit == 130.0  # 30 + 100

        # In-progress session
        assert seat1_sessions[3].session_result.stop_reason == StopReason.IN_PROGRESS
        assert seat1_sessions[3].session_result.hands_played == 1
        assert seat1_sessions[3].session_result.session_profit == 20.0

    def test_seat_replacement_independent_seat_resets(self) -> None:
        """Verify different seats can reset independently."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=5,
        )
        # Seat 1 hits limit in round 0 (100), resets
        # Seat 2 hits limit in round 2 (50+30+100=180, but win_limit=100, so at round 2)
        # Both seats will have sessions completing and in-progress
        mock_table = create_mock_table(
            [
                [100.0, 50.0],  # Round 0: Seat 1 resets (profit=100)
                [20.0, 30.0],  # Round 1: Seat 1 at 20, Seat 2 at 80
                [10.0, 100.0],  # Round 2: Seat 1 at 30, Seat 2 resets (profit=180)
                [10.0, 20.0],  # Round 3: Seat 1 at 40, Seat 2 at 20
                [10.0, 30.0],  # Round 4: Seat 1 at 50, Seat 2 at 50
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None

        # Seat 1: 1 completed session (round 0) + 1 in-progress (rounds 1-4)
        seat1_sessions = result.seat_sessions[1]
        assert len(seat1_sessions) == 2
        assert seat1_sessions[0].session_result.stop_reason == StopReason.WIN_LIMIT
        assert seat1_sessions[0].session_result.session_profit == 100.0
        assert seat1_sessions[1].session_result.stop_reason == StopReason.IN_PROGRESS
        assert seat1_sessions[1].session_result.session_profit == 50.0  # 20+10+10+10

        # Seat 2: 1 completed session (rounds 0-2) + 1 in-progress (rounds 3-4)
        seat2_sessions = result.seat_sessions[2]
        assert len(seat2_sessions) == 2
        assert seat2_sessions[0].session_result.stop_reason == StopReason.WIN_LIMIT
        assert seat2_sessions[0].session_result.session_profit == 180.0  # 50+30+100
        assert seat2_sessions[1].session_result.stop_reason == StopReason.IN_PROGRESS
        assert seat2_sessions[1].session_result.session_profit == 50.0  # 20+30

    def test_seat_replacement_on_loss_limit(self) -> None:
        """Verify seat resets on loss limit in replacement mode."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=200.0,
            base_bet=25.0,
            loss_limit=100.0,
            table_total_rounds=5,
        )
        # Lose 100 in round 1, triggering reset
        mock_table = create_mock_table([[-100.0], [10.0], [20.0], [30.0], [40.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None
        seat1_sessions = result.seat_sessions[1]

        assert len(seat1_sessions) == 2
        assert seat1_sessions[0].session_result.stop_reason == StopReason.LOSS_LIMIT
        assert seat1_sessions[0].session_result.session_profit == -100.0

    def test_seat_replacement_on_insufficient_funds(self) -> None:
        """Verify seat resets on insufficient funds in replacement mode."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=100.0,  # Just enough for 1 hand (75)
            base_bet=25.0,
            table_total_rounds=3,
        )
        # Big loss drains bankroll, triggering reset
        mock_table = create_mock_table(
            [[-75.0], [10.0], [20.0]]  # After -75, only 25 left < 75 required
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None
        seat1_sessions = result.seat_sessions[1]

        assert len(seat1_sessions) == 2
        assert (
            seat1_sessions[0].session_result.stop_reason
            == StopReason.INSUFFICIENT_FUNDS
        )

    def test_seat_replacement_on_max_hands(self) -> None:
        """Verify seat resets on max_hands in replacement mode."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=2,  # Per-session max
            table_total_rounds=6,
        )
        mock_table = create_mock_table([[10.0], [20.0], [30.0], [40.0], [50.0], [60.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None
        seat1_sessions = result.seat_sessions[1]

        # 6 rounds with max_hands=2 means 3 complete sessions
        assert len(seat1_sessions) == 3

        assert seat1_sessions[0].session_result.stop_reason == StopReason.MAX_HANDS
        assert seat1_sessions[0].session_result.hands_played == 2

        assert seat1_sessions[1].session_result.stop_reason == StopReason.MAX_HANDS
        assert seat1_sessions[1].session_result.hands_played == 2

        assert seat1_sessions[2].session_result.stop_reason == StopReason.MAX_HANDS
        assert seat1_sessions[2].session_result.hands_played == 2

    def test_seat_replacement_bankroll_resets_to_starting(self) -> None:
        """Verify bankroll resets to starting_bankroll on seat reset."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=200.0,
            table_total_rounds=4,
        )
        # Win 200, reset with fresh 1000, then lose 50
        mock_table = create_mock_table([[200.0], [-50.0], [0.0], [0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None
        seat1_sessions = result.seat_sessions[1]

        assert len(seat1_sessions) == 2

        # First session: ended at 1200, profit 200
        assert seat1_sessions[0].session_result.final_bankroll == 1200.0
        assert seat1_sessions[0].session_result.session_profit == 200.0
        assert seat1_sessions[0].session_result.starting_bankroll == 1000.0

        # Second session: started at 1000 again
        assert seat1_sessions[1].session_result.starting_bankroll == 1000.0
        assert seat1_sessions[1].session_result.session_profit == -50.0
        assert seat1_sessions[1].session_result.final_bankroll == 950.0


class TestSeatReplacementBackwardsCompatibility:
    """Tests to ensure backwards compatibility when table_total_rounds is None."""

    def test_classic_mode_single_seat_unchanged(self) -> None:
        """Verify single-seat classic mode behaves same as before."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )
        mock_table = create_mock_table([[10.0], [20.0], [30.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.total_rounds == 3
        assert result.stop_reason == StopReason.MAX_HANDS
        assert result.seat_sessions is None  # Not set in classic mode
        assert len(result.seat_results) == 1
        assert result.seat_results[0].session_result.hands_played == 3

    def test_classic_mode_multi_seat_unchanged(self) -> None:
        """Verify multi-seat classic mode behaves same as before."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=200.0,
            max_hands=100,
        )
        # Seat 1 hits win limit after 2 rounds (100+100=200)
        # Seat 2 hits win limit after 4 rounds (50*4=200)
        mock_table = create_mock_table(
            [
                [100.0, 50.0],
                [100.0, 50.0],  # Seat 1 hits 200, stops
                [0.0, 50.0],  # Seat 1 stopped, ignored
                [0.0, 50.0],  # Seat 2 hits 200, stops
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # Classic behavior: wait for all seats
        assert result.total_rounds == 4
        assert result.stop_reason == StopReason.WIN_LIMIT
        assert result.seat_sessions is None

        # Seat 1 stopped at round 2, profit frozen at 200
        assert result.seat_results[0].session_result.session_profit == 200.0
        # Seat 2 stopped at round 4, profit 200 (50*4)
        assert result.seat_results[1].session_result.session_profit == 200.0


class TestSeatReplacementResultStructure:
    """Tests for TableSessionResult structure in seat replacement mode."""

    def test_seat_sessions_dict_structure(self) -> None:
        """Verify seat_sessions dict has correct structure."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=3,
        )
        mock_table = create_mock_table([[100.0, 50.0], [20.0, 50.0], [30.0, 0.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None
        assert 1 in result.seat_sessions
        assert 2 in result.seat_sessions
        assert isinstance(result.seat_sessions[1], list)
        assert isinstance(result.seat_sessions[2], list)
        assert all(isinstance(s, SeatSessionResult) for s in result.seat_sessions[1])

    def test_seat_results_contains_last_session_per_seat(self) -> None:
        """Verify seat_results contains the last/in-progress session per seat."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=3,
        )
        # Two completed sessions + in-progress
        mock_table = create_mock_table([[100.0], [100.0], [50.0]])
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        # seat_results should have the last (in-progress) session
        assert len(result.seat_results) == 1
        last_session = result.seat_results[0].session_result
        assert last_session.stop_reason == StopReason.IN_PROGRESS
        assert last_session.session_profit == 50.0

    def test_no_in_progress_session_when_last_round_triggers_reset(self) -> None:
        """Verify no in-progress session when the last round triggers a reset."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=1),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=2,
        )
        # Win limit hit on last round
        mock_table = create_mock_table(
            [[50.0], [100.0]]  # Hits win limit exactly at end
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None
        seat1_sessions = result.seat_sessions[1]

        # Should have completed session but no hands played after reset
        # So no in-progress session to add
        # Wait - after the reset, hands_played_this_session would be 0
        # The completed session had 2 hands with profit 150
        assert len(seat1_sessions) == 1
        assert seat1_sessions[0].session_result.stop_reason == StopReason.WIN_LIMIT
        assert seat1_sessions[0].session_result.session_profit == 150.0


class TestSeatStateReset:
    """Tests for _SeatState.reset() method."""

    def test_reset_clears_bankroll(self) -> None:
        """Verify reset creates fresh bankroll."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0, current_round=0)
        state.bankroll.apply_result(500.0)  # Now at 1500

        state.reset(current_round=5)

        assert state.bankroll.balance == 1000.0
        assert state.bankroll.session_profit == 0.0

    def test_reset_clears_wagering_totals(self) -> None:
        """Verify reset clears wagering totals."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0, current_round=0)
        state.total_wagered = 500.0
        state.total_bonus_wagered = 50.0

        state.reset(current_round=5)

        assert state.total_wagered == 0.0
        assert state.total_bonus_wagered == 0.0

    def test_reset_clears_streak(self) -> None:
        """Verify reset clears streak."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0, current_round=0)
        state.streak = 5

        state.reset(current_round=5)

        assert state.streak == 0

    def test_reset_preserves_completed_sessions(self) -> None:
        """Verify reset does not clear completed_sessions."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0, current_round=0)
        # Simulate adding a completed session
        state.completed_sessions.append("dummy_session")  # type: ignore[arg-type]

        state.reset(current_round=5)

        assert len(state.completed_sessions) == 1

    def test_reset_updates_session_start_round(self) -> None:
        """Verify reset updates session_start_round."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0, current_round=0)
        assert state.session_start_round == 0

        state.reset(current_round=10)

        assert state.session_start_round == 10

    def test_hands_played_this_session(self) -> None:
        """Verify hands_played_this_session calculates correctly."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0, current_round=5)

        assert state.hands_played_this_session(5) == 0
        assert state.hands_played_this_session(7) == 2
        assert state.hands_played_this_session(10) == 5

    def test_reset_reuses_bankroll_object(self) -> None:
        """Verify reset reuses the same BankrollTracker instance (no new allocation)."""
        from let_it_ride.simulation.table_session import _SeatState

        state = _SeatState(1000.0, current_round=0)
        original_bankroll_id = id(state.bankroll)

        state.bankroll.apply_result(500.0)
        state.reset(current_round=5)

        # Same object should be reused
        assert id(state.bankroll) == original_bankroll_id
        # But state should be reset
        assert state.bankroll.balance == 1000.0
        assert state.bankroll.session_profit == 0.0


class TestSeatReplacementConcurrentStopConditions:
    """Tests for concurrent stop condition triggers in seat replacement mode."""

    def test_multiple_seats_hit_stop_condition_same_round(self) -> None:
        """Verify multiple seats can reset in the same round."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=3),
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            table_total_rounds=4,
        )
        # All 3 seats hit win limit simultaneously in round 0
        mock_table = create_mock_table(
            [
                [100.0, 100.0, 100.0],  # All hit win limit, all reset
                [10.0, 20.0, 30.0],  # New sessions
                [40.0, 50.0, 60.0],  # Continue
                [5.0, 5.0, 5.0],  # Continue
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None

        # All seats should have completed session from round 0 + in-progress
        for seat_num in [1, 2, 3]:
            sessions = result.seat_sessions[seat_num]
            assert len(sessions) == 2  # 1 completed + 1 in-progress
            assert sessions[0].session_result.stop_reason == StopReason.WIN_LIMIT
            assert sessions[0].session_result.hands_played == 1
            assert sessions[0].session_result.session_profit == 100.0
            assert sessions[1].session_result.stop_reason == StopReason.IN_PROGRESS

        # Verify in-progress profits
        assert result.seat_sessions[1][1].session_result.session_profit == 55.0  # 10+40+5
        assert result.seat_sessions[2][1].session_result.session_profit == 75.0  # 20+50+5
        assert result.seat_sessions[3][1].session_result.session_profit == 95.0  # 30+60+5

    def test_mixed_stop_conditions_same_round(self) -> None:
        """Verify different stop conditions can trigger for different seats in same round."""
        config = TableSessionConfig(
            table_config=TableConfig(num_seats=2),
            starting_bankroll=200.0,
            base_bet=25.0,
            win_limit=100.0,
            loss_limit=100.0,
            table_total_rounds=3,
        )
        # Round 0: Seat 1 hits win, Seat 2 hits loss
        mock_table = create_mock_table(
            [
                [100.0, -100.0],  # Seat 1 win_limit, Seat 2 loss_limit
                [10.0, 10.0],  # New sessions
                [20.0, 20.0],  # Continue
            ]
        )
        betting_system = FlatBetting(25.0)

        session = TableSession(config, mock_table, betting_system)
        result = session.run_to_completion()

        assert result.seat_sessions is not None

        # Seat 1: hit win limit
        seat1_sessions = result.seat_sessions[1]
        assert seat1_sessions[0].session_result.stop_reason == StopReason.WIN_LIMIT

        # Seat 2: hit loss limit
        seat2_sessions = result.seat_sessions[2]
        assert seat2_sessions[0].session_result.stop_reason == StopReason.LOSS_LIMIT

        # Both have in-progress sessions
        assert seat1_sessions[1].session_result.stop_reason == StopReason.IN_PROGRESS
        assert seat2_sessions[1].session_result.stop_reason == StopReason.IN_PROGRESS
