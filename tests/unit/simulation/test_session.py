"""Unit tests for session state management."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from let_it_ride.bankroll.betting_systems import BettingContext, FlatBetting
from let_it_ride.simulation.session import (
    Session,
    SessionConfig,
    SessionOutcome,
    SessionResult,
    StopReason,
)

# --- Test Fixtures ---


def create_mock_engine(results: list[float]) -> Mock:
    """Create a mock GameEngine that returns predetermined results.

    Args:
        results: List of net_result values to return from play_hand().
            Each call to play_hand() returns the next result.

    Returns:
        A mock GameEngine.
    """
    mock = Mock()
    result_iter = iter(results)

    def play_hand_side_effect(
        hand_id: int,  # noqa: ARG001
        base_bet: float,
        bonus_bet: float = 0.0,
        context=None,  # noqa: ARG001
    ):
        result = Mock()
        result.net_result = next(result_iter)
        result.bets_at_risk = base_bet * 3  # Assume all bets ride
        result.bonus_bet = bonus_bet
        return result

    mock.play_hand.side_effect = play_hand_side_effect
    return mock


def create_mock_engine_with_custom_bets(
    results: list[tuple[float, float]]
) -> Mock:
    """Create a mock GameEngine with custom bets_at_risk.

    Args:
        results: List of (net_result, bets_at_risk) tuples.

    Returns:
        A mock GameEngine.
    """
    mock = Mock()
    result_iter = iter(results)

    def play_hand_side_effect(
        hand_id: int,  # noqa: ARG001
        base_bet: float,  # noqa: ARG001
        bonus_bet: float = 0.0,
        context=None,  # noqa: ARG001
    ):
        net_result, bets_at_risk = next(result_iter)
        result = Mock()
        result.net_result = net_result
        result.bets_at_risk = bets_at_risk
        result.bonus_bet = bonus_bet
        return result

    mock.play_hand.side_effect = play_hand_side_effect
    return mock


# --- SessionConfig Tests ---


class TestSessionConfigInitialization:
    """Tests for SessionConfig initialization."""

    def test_create_minimal_config(self) -> None:
        """Verify SessionConfig can be created with minimal required fields."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
        )
        assert config.starting_bankroll == 1000.0
        assert config.base_bet == 25.0
        assert config.win_limit is None
        assert config.loss_limit is None
        assert config.max_hands is None
        assert config.stop_on_insufficient_funds is True
        assert config.bonus_bet == 0.0

    def test_create_full_config(self) -> None:
        """Verify SessionConfig can be created with all fields."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=500.0,
            loss_limit=250.0,
            max_hands=100,
            stop_on_insufficient_funds=False,
            bonus_bet=5.0,
        )
        assert config.starting_bankroll == 1000.0
        assert config.base_bet == 25.0
        assert config.win_limit == 500.0
        assert config.loss_limit == 250.0
        assert config.max_hands == 100
        assert config.stop_on_insufficient_funds is False
        assert config.bonus_bet == 5.0

    def test_config_is_frozen(self) -> None:
        """Verify SessionConfig is immutable."""
        config = SessionConfig(starting_bankroll=1000.0, base_bet=25.0)
        with pytest.raises(FrozenInstanceError):
            config.starting_bankroll = 500.0  # type: ignore[misc]

    def test_config_is_hashable(self) -> None:
        """Verify SessionConfig is hashable."""
        config = SessionConfig(starting_bankroll=1000.0, base_bet=25.0)
        hash_value = hash(config)
        assert isinstance(hash_value, int)


class TestSessionConfigValidation:
    """Tests for SessionConfig validation."""

    def test_zero_starting_bankroll_raises(self) -> None:
        """Verify zero starting bankroll raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=0.0, base_bet=25.0)
        assert "starting_bankroll must be positive" in str(exc_info.value)

    def test_negative_starting_bankroll_raises(self) -> None:
        """Verify negative starting bankroll raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=-100.0, base_bet=25.0)
        assert "starting_bankroll must be positive" in str(exc_info.value)

    def test_zero_base_bet_raises(self) -> None:
        """Verify zero base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=0.0)
        assert "base_bet must be positive" in str(exc_info.value)

    def test_negative_base_bet_raises(self) -> None:
        """Verify negative base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=-25.0)
        assert "base_bet must be positive" in str(exc_info.value)

    def test_zero_win_limit_raises(self) -> None:
        """Verify zero win limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=25.0, win_limit=0.0)
        assert "win_limit must be positive" in str(exc_info.value)

    def test_negative_win_limit_raises(self) -> None:
        """Verify negative win limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=25.0, win_limit=-100.0)
        assert "win_limit must be positive" in str(exc_info.value)

    def test_zero_loss_limit_raises(self) -> None:
        """Verify zero loss limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=25.0, loss_limit=0.0)
        assert "loss_limit must be positive" in str(exc_info.value)

    def test_negative_loss_limit_raises(self) -> None:
        """Verify negative loss limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=25.0, loss_limit=-100.0)
        assert "loss_limit must be positive" in str(exc_info.value)

    def test_zero_max_hands_raises(self) -> None:
        """Verify zero max hands raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=25.0, max_hands=0)
        assert "max_hands must be positive" in str(exc_info.value)

    def test_negative_max_hands_raises(self) -> None:
        """Verify negative max hands raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=25.0, max_hands=-10)
        assert "max_hands must be positive" in str(exc_info.value)

    def test_negative_bonus_bet_raises(self) -> None:
        """Verify negative bonus bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(starting_bankroll=1000.0, base_bet=25.0, bonus_bet=-5.0)
        assert "bonus_bet cannot be negative" in str(exc_info.value)

    def test_no_stop_conditions_raises(self) -> None:
        """Verify config with no stop conditions raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(
                starting_bankroll=1000.0,
                base_bet=25.0,
                win_limit=None,
                loss_limit=None,
                max_hands=None,
                stop_on_insufficient_funds=False,
            )
        assert "At least one stop condition must be configured" in str(exc_info.value)

    def test_stop_condition_win_limit_only_valid(self) -> None:
        """Verify config with only win_limit stop condition is valid."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=500.0,
            stop_on_insufficient_funds=False,
        )
        assert config.win_limit == 500.0

    def test_stop_condition_loss_limit_only_valid(self) -> None:
        """Verify config with only loss_limit stop condition is valid."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            loss_limit=250.0,
            stop_on_insufficient_funds=False,
        )
        assert config.loss_limit == 250.0

    def test_stop_condition_max_hands_only_valid(self) -> None:
        """Verify config with only max_hands stop condition is valid."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=100,
            stop_on_insufficient_funds=False,
        )
        assert config.max_hands == 100

    def test_stop_condition_insufficient_funds_only_valid(self) -> None:
        """Verify config with only stop_on_insufficient_funds is valid."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            stop_on_insufficient_funds=True,
        )
        assert config.stop_on_insufficient_funds is True

    def test_starting_bankroll_insufficient_for_min_bet_raises(self) -> None:
        """Verify config with bankroll less than minimum bet raises."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(
                starting_bankroll=50.0,
                base_bet=25.0,  # min bet = 75
            )
        assert "starting_bankroll" in str(exc_info.value)
        assert "75" in str(exc_info.value)

    def test_starting_bankroll_exactly_min_bet_valid(self) -> None:
        """Verify config with bankroll equal to minimum bet is valid."""
        config = SessionConfig(
            starting_bankroll=75.0,
            base_bet=25.0,  # min bet = 75
        )
        assert config.starting_bankroll == 75.0

    def test_starting_bankroll_with_bonus_bet_insufficient_raises(self) -> None:
        """Verify config with bankroll less than min bet including bonus raises."""
        with pytest.raises(ValueError) as exc_info:
            SessionConfig(
                starting_bankroll=80.0,
                base_bet=25.0,
                bonus_bet=10.0,  # min bet = 75 + 10 = 85
            )
        assert "starting_bankroll" in str(exc_info.value)
        assert "85" in str(exc_info.value)

    def test_starting_bankroll_with_bonus_bet_exactly_valid(self) -> None:
        """Verify config with bankroll equal to min bet including bonus is valid."""
        config = SessionConfig(
            starting_bankroll=85.0,
            base_bet=25.0,
            bonus_bet=10.0,  # min bet = 75 + 10 = 85
        )
        assert config.starting_bankroll == 85.0


# --- StopReason Tests ---


class TestStopReason:
    """Tests for StopReason enum."""

    def test_stop_reason_values(self) -> None:
        """Verify all StopReason values exist."""
        assert StopReason.WIN_LIMIT.value == "win_limit"
        assert StopReason.LOSS_LIMIT.value == "loss_limit"
        assert StopReason.MAX_HANDS.value == "max_hands"
        assert StopReason.INSUFFICIENT_FUNDS.value == "insufficient_funds"

    def test_stop_reason_count(self) -> None:
        """Verify number of StopReason variants."""
        assert len(StopReason) == 4


# --- SessionOutcome Tests ---


class TestSessionOutcome:
    """Tests for SessionOutcome enum."""

    def test_session_outcome_values(self) -> None:
        """Verify all SessionOutcome values exist."""
        assert SessionOutcome.WIN.value == "win"
        assert SessionOutcome.LOSS.value == "loss"
        assert SessionOutcome.PUSH.value == "push"

    def test_session_outcome_count(self) -> None:
        """Verify number of SessionOutcome variants."""
        assert len(SessionOutcome) == 3


# --- SessionResult Tests ---


class TestSessionResult:
    """Tests for SessionResult dataclass."""

    def test_create_session_result(self) -> None:
        """Verify SessionResult can be created."""
        result = SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=50,
            starting_bankroll=1000.0,
            final_bankroll=1500.0,
            session_profit=500.0,
            total_wagered=3750.0,
            total_bonus_wagered=250.0,
            peak_bankroll=1550.0,
            max_drawdown=100.0,
            max_drawdown_pct=6.45,
        )
        assert result.outcome == SessionOutcome.WIN
        assert result.stop_reason == StopReason.WIN_LIMIT
        assert result.hands_played == 50
        assert result.session_profit == 500.0

    def test_session_result_is_frozen(self) -> None:
        """Verify SessionResult is immutable."""
        result = SessionResult(
            outcome=SessionOutcome.WIN,
            stop_reason=StopReason.WIN_LIMIT,
            hands_played=50,
            starting_bankroll=1000.0,
            final_bankroll=1500.0,
            session_profit=500.0,
            total_wagered=3750.0,
            total_bonus_wagered=0.0,
            peak_bankroll=1550.0,
            max_drawdown=100.0,
            max_drawdown_pct=6.45,
        )
        with pytest.raises(FrozenInstanceError):
            result.hands_played = 100  # type: ignore[misc]


# --- Session Initialization Tests ---


class TestSessionInitialization:
    """Tests for Session initialization."""

    def test_session_initial_state(self) -> None:
        """Verify Session initializes with correct state."""
        config = SessionConfig(starting_bankroll=1000.0, base_bet=25.0)
        engine = create_mock_engine([0.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)

        assert session.hands_played == 0
        assert session.is_complete is False
        assert session.session_profit == 0.0
        assert session.bankroll == 1000.0
        assert session.streak == 0
        assert session.stop_reason() is None


# --- Stop Condition Tests ---


class TestStopOnWinLimit:
    """Tests for win limit stop condition."""

    def test_stops_on_win_limit(self) -> None:
        """Verify session stops when win limit is reached."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
        )
        # Win $150 (exceeds win limit of $100)
        engine = create_mock_engine([150.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.WIN_LIMIT
        assert session.session_profit == 150.0

    def test_stops_on_exact_win_limit(self) -> None:
        """Verify session stops when exactly at win limit."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
        )
        engine = create_mock_engine([100.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.WIN_LIMIT

    def test_continues_below_win_limit(self) -> None:
        """Verify session continues when below win limit."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            max_hands=10,
        )
        # First hand: +50 (below limit), second hand: +60 (total 110, above limit)
        engine = create_mock_engine([50.0, 60.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.should_stop() is False
        assert session.session_profit == 50.0

        session.play_hand()
        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.WIN_LIMIT
        assert session.session_profit == 110.0


class TestStopOnLossLimit:
    """Tests for loss limit stop condition."""

    def test_stops_on_loss_limit(self) -> None:
        """Verify session stops when loss limit is reached."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            loss_limit=200.0,
        )
        # Lose $250 (exceeds loss limit of $200)
        engine = create_mock_engine([-250.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.LOSS_LIMIT
        assert session.session_profit == -250.0

    def test_stops_on_exact_loss_limit(self) -> None:
        """Verify session stops when exactly at loss limit."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            loss_limit=200.0,
        )
        engine = create_mock_engine([-200.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.LOSS_LIMIT

    def test_continues_above_loss_limit(self) -> None:
        """Verify session continues when above loss limit."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            loss_limit=200.0,
            max_hands=10,
        )
        engine = create_mock_engine([-75.0, -75.0, -75.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()
        assert session.should_stop() is False
        assert session.session_profit == -75.0

        session.play_hand()
        assert session.should_stop() is False
        assert session.session_profit == -150.0

        session.play_hand()
        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.LOSS_LIMIT
        assert session.session_profit == -225.0


class TestStopOnMaxHands:
    """Tests for max hands stop condition."""

    def test_stops_on_max_hands(self) -> None:
        """Verify session stops when max hands is reached."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )
        engine = create_mock_engine([10.0, -20.0, 15.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()
        assert session.hands_played == 1
        assert session.should_stop() is False

        session.play_hand()
        assert session.hands_played == 2
        assert session.should_stop() is False

        session.play_hand()
        assert session.hands_played == 3
        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.MAX_HANDS

    def test_single_hand_max(self) -> None:
        """Verify session stops after single hand when max_hands=1."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        engine = create_mock_engine([50.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.MAX_HANDS


class TestStopOnInsufficientFunds:
    """Tests for insufficient funds stop condition."""

    def test_stops_when_bankroll_too_low(self) -> None:
        """Verify session stops when bankroll cannot cover minimum bet."""
        config = SessionConfig(
            starting_bankroll=100.0,
            base_bet=25.0,  # Minimum = 75 (3 * 25)
        )
        # Lose $50, leaving $50 which is less than $75 minimum
        engine = create_mock_engine([-50.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.bankroll == 50.0
        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.INSUFFICIENT_FUNDS

    def test_continues_when_exactly_at_minimum(self) -> None:
        """Verify session continues when exactly at minimum bet."""
        config = SessionConfig(
            starting_bankroll=100.0,
            base_bet=25.0,  # Minimum = 75
            max_hands=10,
        )
        # Lose $25, leaving $75 which equals minimum
        engine = create_mock_engine([-25.0, 0.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.bankroll == 75.0
        assert session.should_stop() is False

    def test_insufficient_funds_with_bonus_bet(self) -> None:
        """Verify insufficient funds accounts for bonus bet."""
        config = SessionConfig(
            starting_bankroll=100.0,
            base_bet=25.0,  # Minimum = 75 + 5 bonus = 80
            bonus_bet=5.0,
        )
        # Lose $25, leaving $75 which is less than $80 minimum
        engine = create_mock_engine([-25.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.bankroll == 75.0
        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.INSUFFICIENT_FUNDS

    def test_insufficient_funds_disabled(self) -> None:
        """Verify session continues when insufficient funds check is disabled."""
        config = SessionConfig(
            starting_bankroll=100.0,
            base_bet=25.0,
            stop_on_insufficient_funds=False,
            max_hands=2,
        )
        engine = create_mock_engine([-50.0, -40.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.bankroll == 50.0
        assert session.should_stop() is False  # Would normally stop


class TestStopConditionPriority:
    """Tests for stop condition priority when multiple conditions are met."""

    def test_win_limit_checked_first(self) -> None:
        """Verify win limit is checked before max hands."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
            max_hands=1,  # Would trigger at same time
        )
        engine = create_mock_engine([150.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        # Must call should_stop() to determine stop reason
        assert session.should_stop() is True
        # Win limit should be checked first
        assert session.stop_reason() == StopReason.WIN_LIMIT

    def test_loss_limit_before_insufficient_funds(self) -> None:
        """Verify loss limit is checked before insufficient funds."""
        config = SessionConfig(
            starting_bankroll=100.0,
            base_bet=25.0,
            loss_limit=50.0,  # Would trigger first
        )
        engine = create_mock_engine([-75.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        # Must call should_stop() to determine stop reason
        assert session.should_stop() is True
        assert session.stop_reason() == StopReason.LOSS_LIMIT


# --- Session Execution Tests ---


class TestPlayHand:
    """Tests for Session.play_hand() method."""

    def test_play_hand_updates_state(self) -> None:
        """Verify play_hand updates session state correctly."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=10,
        )
        engine = create_mock_engine([50.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        assert session.hands_played == 1
        assert session.session_profit == 50.0
        assert session.bankroll == 1050.0

    def test_play_hand_raises_when_complete(self) -> None:
        """Verify play_hand raises when session is complete."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=1,
        )
        engine = create_mock_engine([0.0, 0.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        # Must call should_stop() to mark session complete
        assert session.should_stop() is True
        assert session.is_complete is True

        with pytest.raises(RuntimeError) as exc_info:
            session.play_hand()
        assert "session is already complete" in str(exc_info.value)

    def test_play_hand_passes_context_to_engine(self) -> None:
        """Verify play_hand passes correct context to engine."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            bonus_bet=5.0,
            max_hands=2,
        )
        engine = create_mock_engine([50.0, -25.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        session.play_hand()

        # Check the engine was called correctly
        call_args = engine.play_hand.call_args
        assert call_args.kwargs.get("hand_id") == 0 or call_args[1].get("hand_id") == 0
        assert call_args.kwargs.get("base_bet") == 25.0 or call_args[1].get("base_bet") == 25.0
        assert call_args.kwargs.get("bonus_bet") == 5.0 or call_args[1].get("bonus_bet") == 5.0


class TestRunToCompletion:
    """Tests for Session.run_to_completion() method."""

    def test_run_to_completion_returns_result(self) -> None:
        """Verify run_to_completion returns SessionResult."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )
        engine = create_mock_engine([50.0, -25.0, 100.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert isinstance(result, SessionResult)
        assert result.hands_played == 3
        assert result.stop_reason == StopReason.MAX_HANDS
        assert result.session_profit == 125.0
        assert result.final_bankroll == 1125.0

    def test_run_to_completion_win_outcome(self) -> None:
        """Verify WIN outcome when session ends with profit."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=100.0,
        )
        engine = create_mock_engine([150.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.outcome == SessionOutcome.WIN

    def test_run_to_completion_loss_outcome(self) -> None:
        """Verify LOSS outcome when session ends with loss."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            loss_limit=100.0,
        )
        engine = create_mock_engine([-150.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.outcome == SessionOutcome.LOSS

    def test_run_to_completion_push_outcome(self) -> None:
        """Verify PUSH outcome when session ends break-even."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=2,
        )
        engine = create_mock_engine([50.0, -50.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.outcome == SessionOutcome.PUSH
        assert result.session_profit == 0.0


# --- Streak Tracking Tests ---


class TestStreakTracking:
    """Tests for win/loss streak tracking."""

    def test_winning_streak(self) -> None:
        """Verify winning streak is tracked correctly."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=4,
        )
        engine = create_mock_engine([50.0, 25.0, 75.0, 10.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)

        session.play_hand()
        assert session.streak == 1

        session.play_hand()
        assert session.streak == 2

        session.play_hand()
        assert session.streak == 3

        session.play_hand()
        assert session.streak == 4

    def test_losing_streak(self) -> None:
        """Verify losing streak is tracked correctly."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=4,
        )
        engine = create_mock_engine([-50.0, -25.0, -75.0, -10.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)

        session.play_hand()
        assert session.streak == -1

        session.play_hand()
        assert session.streak == -2

        session.play_hand()
        assert session.streak == -3

        session.play_hand()
        assert session.streak == -4

    def test_streak_resets_on_direction_change(self) -> None:
        """Verify streak resets when win/loss direction changes."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=5,
        )
        engine = create_mock_engine([50.0, 50.0, -25.0, 50.0, 50.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)

        session.play_hand()
        assert session.streak == 1

        session.play_hand()
        assert session.streak == 2

        session.play_hand()  # Loss
        assert session.streak == -1

        session.play_hand()  # Win
        assert session.streak == 1

        session.play_hand()
        assert session.streak == 2

    def test_push_does_not_change_streak(self) -> None:
        """Verify push (break-even) does not change streak."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=4,
        )
        engine = create_mock_engine([50.0, 0.0, 50.0, 0.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)

        session.play_hand()
        assert session.streak == 1

        session.play_hand()  # Push
        assert session.streak == 1  # Unchanged

        session.play_hand()
        assert session.streak == 2

        session.play_hand()  # Push
        assert session.streak == 2  # Unchanged


# --- Statistics Accuracy Tests ---


class TestStatisticsAccuracy:
    """Tests for session statistics accuracy."""

    def test_total_wagered_accumulated(self) -> None:
        """Verify total wagered is accumulated correctly."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )
        # Each hand has bets_at_risk of 75 (3 * 25)
        engine = create_mock_engine_with_custom_bets([
            (50.0, 75.0),
            (-25.0, 75.0),
            (100.0, 75.0),
        ])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.total_wagered == 225.0  # 75 * 3

    def test_total_bonus_wagered_accumulated(self) -> None:
        """Verify total bonus wagered is accumulated correctly."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            bonus_bet=5.0,
            max_hands=3,
        )
        engine = create_mock_engine([50.0, -25.0, 100.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.total_bonus_wagered == 15.0  # 5 * 3

    def test_peak_bankroll_tracked(self) -> None:
        """Verify peak bankroll is tracked correctly."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=4,
        )
        # Start: 1000, +200: 1200 (peak), -100: 1100, +50: 1150
        engine = create_mock_engine([200.0, -100.0, 50.0, -25.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.peak_bankroll == 1200.0

    def test_max_drawdown_tracked(self) -> None:
        """Verify max drawdown is tracked correctly."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=5,
        )
        # Start: 1000, +200: 1200 (peak), -300: 900 (drawdown 300), +100: 1000
        engine = create_mock_engine([200.0, -300.0, 100.0, 0.0, 0.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.max_drawdown == 300.0

    def test_max_drawdown_percentage(self) -> None:
        """Verify max drawdown percentage is calculated correctly."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )
        # Start: 1000 (peak), -500: 500 (50% drawdown), +250: 750
        engine = create_mock_engine([-500.0, 250.0, 0.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.max_drawdown_pct == 50.0


# --- Edge Cases ---


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_session_with_all_losses(self) -> None:
        """Verify session handles consecutive losses."""
        config = SessionConfig(
            starting_bankroll=200.0,
            base_bet=25.0,  # Minimum = 75
        )
        # Lose $75 each hand until insufficient funds
        engine = create_mock_engine([-75.0, -75.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.outcome == SessionOutcome.LOSS
        assert result.stop_reason == StopReason.INSUFFICIENT_FUNDS
        assert result.final_bankroll == 50.0

    def test_session_with_all_wins(self) -> None:
        """Verify session handles consecutive wins."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            win_limit=500.0,
        )
        engine = create_mock_engine([100.0, 150.0, 200.0, 100.0])
        betting = FlatBetting(25.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.outcome == SessionOutcome.WIN
        assert result.stop_reason == StopReason.WIN_LIMIT

    def test_very_small_bets(self) -> None:
        """Verify session handles very small bet amounts."""
        config = SessionConfig(
            starting_bankroll=10.0,
            base_bet=0.10,  # Minimum = 0.30
            max_hands=5,
        )
        engine = create_mock_engine([0.50, -0.30, 0.20, -0.30, 0.10])
        betting = FlatBetting(0.10)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.hands_played == 5
        assert result.session_profit == pytest.approx(0.20, rel=1e-9)

    def test_very_large_bankroll(self) -> None:
        """Verify session handles large bankroll amounts."""
        config = SessionConfig(
            starting_bankroll=1_000_000.0,
            base_bet=1000.0,
            max_hands=3,
        )
        engine = create_mock_engine([50000.0, -30000.0, 25000.0])
        betting = FlatBetting(1000.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.session_profit == 45000.0
        assert result.final_bankroll == 1_045_000.0


# --- Integration Tests ---


class TestSessionIntegration:
    """Integration-style tests for complete session flows."""

    def test_complete_session_workflow(self) -> None:
        """Verify complete session workflow with realistic scenario."""
        config = SessionConfig(
            starting_bankroll=500.0,
            base_bet=10.0,
            win_limit=100.0,
            loss_limit=100.0,
            max_hands=50,
            bonus_bet=2.0,
        )

        # Simulate a mix of wins and losses
        results = [
            25.0, -30.0, 15.0, -30.0, 50.0,  # +30
            -30.0, -30.0, 100.0, -30.0, 25.0,  # +35 = +65
            15.0, 25.0, -30.0, 15.0, 10.0,    # +35 = +100 (hit win limit)
        ]
        engine = create_mock_engine(results)
        betting = FlatBetting(10.0)

        session = Session(config, engine, betting)
        result = session.run_to_completion()

        assert result.stop_reason == StopReason.WIN_LIMIT
        assert result.outcome == SessionOutcome.WIN
        assert result.hands_played <= 50

    def test_betting_system_receives_correct_context(self) -> None:
        """Verify betting system receives accurate context."""
        config = SessionConfig(
            starting_bankroll=1000.0,
            base_bet=25.0,
            max_hands=3,
        )

        # Create a mock betting system to capture contexts
        captured_contexts: list[BettingContext] = []

        class CapturingBettingSystem:
            def get_bet(self, context: BettingContext) -> float:
                captured_contexts.append(context)
                return 25.0

            def record_result(self, result: float) -> None:
                pass

            def reset(self) -> None:
                pass

        engine = create_mock_engine([50.0, -25.0, 100.0])
        betting = CapturingBettingSystem()

        session = Session(config, engine, betting)  # type: ignore[arg-type]
        session.run_to_completion()

        # Verify first context
        assert captured_contexts[0].bankroll == 1000.0
        assert captured_contexts[0].session_profit == 0.0
        assert captured_contexts[0].hands_played == 0
        assert captured_contexts[0].streak == 0
        assert captured_contexts[0].last_result is None

        # Verify second context (after first win)
        assert captured_contexts[1].bankroll == 1050.0
        assert captured_contexts[1].session_profit == 50.0
        assert captured_contexts[1].hands_played == 1
        assert captured_contexts[1].streak == 1
        assert captured_contexts[1].last_result == 50.0

        # Verify third context (after loss)
        assert captured_contexts[2].bankroll == 1025.0
        assert captured_contexts[2].session_profit == 25.0
        assert captured_contexts[2].hands_played == 2
        assert captured_contexts[2].streak == -1
        assert captured_contexts[2].last_result == -25.0
