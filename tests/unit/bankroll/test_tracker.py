"""Unit tests for BankrollTracker class."""

import pytest

from let_it_ride.bankroll.tracker import BankrollTracker


class TestBankrollTrackerInitialization:
    """Tests for BankrollTracker initialization."""

    def test_initialization_with_positive_amount(self) -> None:
        """Verify tracker initializes with positive starting amount."""
        tracker = BankrollTracker(1000.0)
        assert tracker.balance == 1000.0
        assert tracker.starting_balance == 1000.0
        assert tracker.peak_balance == 1000.0
        assert tracker.session_profit == 0.0

    def test_initialization_with_zero_amount(self) -> None:
        """Verify tracker accepts zero starting amount."""
        tracker = BankrollTracker(0.0)
        assert tracker.balance == 0.0
        assert tracker.starting_balance == 0.0

    def test_initialization_with_negative_amount_raises(self) -> None:
        """Verify negative starting amount raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            BankrollTracker(-100.0)
        assert "Starting amount cannot be negative" in str(exc_info.value)

    def test_initialization_history_is_empty(self) -> None:
        """Verify history is empty on initialization."""
        tracker = BankrollTracker(1000.0, track_history=True)
        assert tracker.history == []

    def test_initialization_history_tracking_disabled_by_default(self) -> None:
        """Verify history tracking is disabled by default."""
        tracker = BankrollTracker(1000.0)
        assert not tracker.is_tracking_history
        tracker.apply_result(100.0)
        assert tracker.history == []

    def test_initialization_history_tracking_enabled(self) -> None:
        """Verify history tracking can be enabled."""
        tracker = BankrollTracker(1000.0, track_history=True)
        assert tracker.is_tracking_history

    def test_initialization_max_drawdown_is_zero(self) -> None:
        """Verify max drawdown starts at zero."""
        tracker = BankrollTracker(1000.0)
        assert tracker.max_drawdown == 0.0
        assert tracker.max_drawdown_pct == 0.0

    def test_initialization_current_drawdown_is_zero(self) -> None:
        """Verify current drawdown starts at zero."""
        tracker = BankrollTracker(1000.0)
        assert tracker.current_drawdown == 0.0


class TestApplyResult:
    """Tests for apply_result method."""

    def test_apply_positive_result(self) -> None:
        """Verify positive result increases balance."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(50.0)
        assert tracker.balance == 1050.0

    def test_apply_negative_result(self) -> None:
        """Verify negative result decreases balance."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-30.0)
        assert tracker.balance == 970.0

    def test_apply_zero_result(self) -> None:
        """Verify zero result maintains balance."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(0.0)
        assert tracker.balance == 1000.0

    def test_apply_multiple_results(self) -> None:
        """Verify multiple results accumulate correctly."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(100.0)  # 1100
        tracker.apply_result(-50.0)  # 1050
        tracker.apply_result(25.0)  # 1075
        assert tracker.balance == 1075.0

    def test_apply_result_can_go_negative(self) -> None:
        """Verify balance can go negative."""
        tracker = BankrollTracker(100.0)
        tracker.apply_result(-150.0)
        assert tracker.balance == -50.0

    def test_apply_result_updates_history(self) -> None:
        """Verify each result is recorded in history when tracking enabled."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.apply_result(50.0)
        tracker.apply_result(-30.0)
        assert tracker.history == [1050.0, 1020.0]

    def test_apply_result_does_not_update_history_when_disabled(self) -> None:
        """Verify history is not updated when tracking is disabled."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(50.0)
        tracker.apply_result(-30.0)
        assert tracker.history == []
        assert tracker.history_length == 0


class TestSessionProfit:
    """Tests for session_profit property."""

    def test_session_profit_after_win(self) -> None:
        """Verify session profit is positive after winning."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(200.0)
        assert tracker.session_profit == 200.0

    def test_session_profit_after_loss(self) -> None:
        """Verify session profit is negative after losing."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-150.0)
        assert tracker.session_profit == -150.0

    def test_session_profit_breakeven(self) -> None:
        """Verify session profit is zero at breakeven."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(100.0)
        tracker.apply_result(-100.0)
        assert tracker.session_profit == 0.0


class TestPeakBalance:
    """Tests for peak_balance tracking."""

    def test_peak_increases_on_new_high(self) -> None:
        """Verify peak updates when balance exceeds previous peak."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(100.0)
        assert tracker.peak_balance == 1100.0

    def test_peak_does_not_decrease_on_loss(self) -> None:
        """Verify peak remains after balance drops."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(100.0)  # Peak = 1100
        tracker.apply_result(-200.0)  # Balance = 900
        assert tracker.peak_balance == 1100.0

    def test_peak_tracks_highest_point(self) -> None:
        """Verify peak tracks the all-time high."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)  # Peak = 1500
        tracker.apply_result(-300.0)  # Peak stays 1500
        tracker.apply_result(200.0)  # Peak stays 1500 (balance = 1400)
        tracker.apply_result(200.0)  # Peak = 1600
        assert tracker.peak_balance == 1600.0

    def test_peak_starts_at_starting_balance(self) -> None:
        """Verify peak starts at starting balance."""
        tracker = BankrollTracker(1000.0)
        assert tracker.peak_balance == 1000.0

    def test_peak_with_only_losses(self) -> None:
        """Verify peak remains at starting balance with only losses."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-100.0)
        tracker.apply_result(-50.0)
        assert tracker.peak_balance == 1000.0


class TestMaxDrawdown:
    """Tests for max_drawdown calculation."""

    def test_max_drawdown_simple_case(self) -> None:
        """Verify max drawdown calculation for simple loss."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-200.0)
        assert tracker.max_drawdown == 200.0

    def test_max_drawdown_after_peak(self) -> None:
        """Verify max drawdown from new peak."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)  # Peak = 1500
        tracker.apply_result(-600.0)  # Balance = 900, drawdown = 600
        assert tracker.max_drawdown == 600.0

    def test_max_drawdown_tracks_largest(self) -> None:
        """Verify max drawdown tracks the largest decline."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-100.0)  # Drawdown = 100
        tracker.apply_result(200.0)  # New peak = 1100
        tracker.apply_result(-50.0)  # Drawdown = 50, max still 100
        assert tracker.max_drawdown == 100.0

        tracker.apply_result(-100.0)  # Drawdown = 150, new max
        assert tracker.max_drawdown == 150.0

    def test_max_drawdown_with_recovery(self) -> None:
        """Verify max drawdown persists after recovery."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-300.0)  # Max drawdown = 300
        tracker.apply_result(500.0)  # Recovered and new high
        assert tracker.max_drawdown == 300.0

    def test_max_drawdown_zero_with_only_wins(self) -> None:
        """Verify max drawdown is zero with only wins."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(100.0)
        tracker.apply_result(100.0)
        assert tracker.max_drawdown == 0.0


class TestMaxDrawdownPct:
    """Tests for max_drawdown_pct calculation."""

    def test_max_drawdown_pct_calculation(self) -> None:
        """Verify percentage calculation is correct."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-200.0)  # 20% drawdown from peak of 1000
        assert tracker.max_drawdown_pct == 20.0

    def test_max_drawdown_pct_from_higher_peak(self) -> None:
        """Verify percentage is relative to peak at time of max drawdown."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)  # Peak = 1500
        tracker.apply_result(-600.0)  # 600/1500 = 40%
        assert tracker.max_drawdown_pct == 40.0

    def test_max_drawdown_pct_with_zero_peak(self) -> None:
        """Verify zero peak handles gracefully."""
        tracker = BankrollTracker(0.0)
        tracker.apply_result(-50.0)  # Balance = -50, peak = 0
        assert tracker.max_drawdown_pct == 0.0  # Avoid division by zero


class TestCurrentDrawdown:
    """Tests for current_drawdown calculation."""

    def test_current_drawdown_at_peak(self) -> None:
        """Verify current drawdown is zero at peak."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(100.0)
        assert tracker.current_drawdown == 0.0

    def test_current_drawdown_below_peak(self) -> None:
        """Verify current drawdown when below peak."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(100.0)  # Peak = 1100
        tracker.apply_result(-50.0)  # Balance = 1050
        assert tracker.current_drawdown == 50.0

    def test_current_drawdown_updates(self) -> None:
        """Verify current drawdown updates correctly."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-100.0)
        assert tracker.current_drawdown == 100.0

        tracker.apply_result(-100.0)
        assert tracker.current_drawdown == 200.0

        tracker.apply_result(50.0)
        assert tracker.current_drawdown == 150.0

    def test_current_drawdown_resets_on_new_peak(self) -> None:
        """Verify current drawdown resets when reaching new peak."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-100.0)
        assert tracker.current_drawdown == 100.0

        tracker.apply_result(150.0)  # New peak at 1050
        assert tracker.current_drawdown == 0.0


class TestHistory:
    """Tests for history property."""

    def test_history_returns_copy(self) -> None:
        """Verify history returns a copy, not the internal list."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.apply_result(100.0)

        history = tracker.history
        history.clear()

        assert len(tracker.history) == 1

    def test_history_order(self) -> None:
        """Verify history maintains chronological order."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.apply_result(100.0)
        tracker.apply_result(-50.0)
        tracker.apply_result(25.0)

        assert tracker.history == [1100.0, 1050.0, 1075.0]

    def test_history_length_property(self) -> None:
        """Verify history_length returns correct count without copying."""
        tracker = BankrollTracker(1000.0, track_history=True)
        assert tracker.history_length == 0

        tracker.apply_result(100.0)
        assert tracker.history_length == 1

        tracker.apply_result(-50.0)
        tracker.apply_result(25.0)
        assert tracker.history_length == 3


class TestGetRecentHistory:
    """Tests for get_recent_history method."""

    def test_get_recent_history_returns_last_n_entries(self) -> None:
        """Verify get_recent_history returns correct recent entries."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.apply_result(100.0)  # 1100
        tracker.apply_result(-50.0)  # 1050
        tracker.apply_result(25.0)  # 1075
        tracker.apply_result(-10.0)  # 1065

        assert tracker.get_recent_history(2) == [1075.0, 1065.0]
        assert tracker.get_recent_history(3) == [1050.0, 1075.0, 1065.0]

    def test_get_recent_history_with_n_larger_than_history(self) -> None:
        """Verify returns all entries when n exceeds history length."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.apply_result(100.0)
        tracker.apply_result(-50.0)

        assert tracker.get_recent_history(10) == [1100.0, 1050.0]

    def test_get_recent_history_with_zero_n(self) -> None:
        """Verify returns empty list when n is zero."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.apply_result(100.0)

        assert tracker.get_recent_history(0) == []

    def test_get_recent_history_with_negative_n(self) -> None:
        """Verify returns empty list when n is negative."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.apply_result(100.0)

        assert tracker.get_recent_history(-5) == []

    def test_get_recent_history_with_empty_history(self) -> None:
        """Verify returns empty list when history is empty."""
        tracker = BankrollTracker(1000.0, track_history=True)

        assert tracker.get_recent_history(5) == []

    def test_get_recent_history_when_tracking_disabled(self) -> None:
        """Verify returns empty list when history tracking is disabled."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(100.0)
        tracker.apply_result(-50.0)

        assert tracker.get_recent_history(2) == []


class TestRepr:
    """Tests for string representation."""

    def test_repr_initial_state(self) -> None:
        """Verify repr of initial tracker."""
        tracker = BankrollTracker(1000.0)
        assert repr(tracker) == (
            "BankrollTracker(balance=1000.00, peak=1000.00, max_drawdown=0.00)"
        )

    def test_repr_after_transactions(self) -> None:
        """Verify repr after transactions."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)
        tracker.apply_result(-200.0)
        assert repr(tracker) == (
            "BankrollTracker(balance=1300.00, peak=1500.00, max_drawdown=200.00)"
        )


class TestDrawdownScenarios:
    """Complex scenarios for drawdown calculation accuracy."""

    def test_multiple_drawdown_events(self) -> None:
        """Verify correct tracking through multiple drawdown events."""
        tracker = BankrollTracker(1000.0)

        # First drawdown: peak 1000, low 800
        tracker.apply_result(-200.0)
        assert tracker.max_drawdown == 200.0
        assert tracker.current_drawdown == 200.0

        # Recovery to new peak
        tracker.apply_result(500.0)  # Balance = 1300, peak = 1300
        assert tracker.max_drawdown == 200.0  # Still 200
        assert tracker.current_drawdown == 0.0

        # Second drawdown: larger
        tracker.apply_result(-400.0)  # Balance = 900, drawdown = 400
        assert tracker.max_drawdown == 400.0
        assert tracker.current_drawdown == 400.0

    def test_gradual_decline(self) -> None:
        """Verify tracking through gradual decline."""
        tracker = BankrollTracker(1000.0)

        for _ in range(5):
            tracker.apply_result(-50.0)

        assert tracker.balance == 750.0
        assert tracker.max_drawdown == 250.0
        assert tracker.current_drawdown == 250.0

    def test_volatile_session(self) -> None:
        """Verify tracking through volatile up-and-down session."""
        tracker = BankrollTracker(1000.0, track_history=True)

        # Win, lose, win big, lose big
        tracker.apply_result(200.0)  # 1200, peak 1200
        tracker.apply_result(-100.0)  # 1100
        tracker.apply_result(400.0)  # 1500, peak 1500
        tracker.apply_result(-700.0)  # 800, drawdown 700

        assert tracker.balance == 800.0
        assert tracker.peak_balance == 1500.0
        assert tracker.max_drawdown == 700.0
        assert tracker.current_drawdown == 700.0
        assert tracker.session_profit == -200.0
        assert tracker.history_length == 4

    def test_zero_starting_balance_scenario(self) -> None:
        """Verify behavior with zero starting balance."""
        tracker = BankrollTracker(0.0)

        tracker.apply_result(100.0)  # Balance 100, peak 100
        tracker.apply_result(-50.0)  # Balance 50, drawdown 50

        assert tracker.balance == 50.0
        assert tracker.peak_balance == 100.0
        assert tracker.max_drawdown == 50.0
        assert tracker.max_drawdown_pct == 50.0


class TestReset:
    """Tests for reset() method."""

    def test_reset_restores_initial_balance(self) -> None:
        """Verify reset restores balance to starting amount."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)
        tracker.apply_result(-200.0)

        tracker.reset()

        assert tracker.balance == 1000.0
        assert tracker.starting_balance == 1000.0

    def test_reset_clears_session_profit(self) -> None:
        """Verify reset clears session profit."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(300.0)

        tracker.reset()

        assert tracker.session_profit == 0.0

    def test_reset_clears_peak(self) -> None:
        """Verify reset clears peak balance."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)  # Peak = 1500

        tracker.reset()

        assert tracker.peak_balance == 1000.0

    def test_reset_clears_drawdown(self) -> None:
        """Verify reset clears max drawdown."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(-200.0)  # max_drawdown = 200

        tracker.reset()

        assert tracker.max_drawdown == 0.0
        assert tracker.max_drawdown_pct == 0.0
        assert tracker.current_drawdown == 0.0

    def test_reset_clears_history(self) -> None:
        """Verify reset clears history."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.apply_result(100.0)
        tracker.apply_result(-50.0)

        tracker.reset()

        assert tracker.history_length == 0
        assert tracker.history == []

    def test_reset_preserves_history_tracking_setting(self) -> None:
        """Verify reset preserves the track_history setting."""
        tracker = BankrollTracker(1000.0, track_history=True)
        tracker.reset()
        tracker.apply_result(100.0)

        assert tracker.is_tracking_history is True
        assert tracker.history_length == 1

    def test_reset_with_new_starting_amount(self) -> None:
        """Verify reset can change the starting amount."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)

        tracker.reset(2000.0)

        assert tracker.balance == 2000.0
        assert tracker.starting_balance == 2000.0
        assert tracker.peak_balance == 2000.0

    def test_reset_with_none_uses_original_starting(self) -> None:
        """Verify reset with None uses original starting amount."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)

        tracker.reset(None)

        assert tracker.balance == 1000.0
        assert tracker.starting_balance == 1000.0

    def test_reset_with_negative_amount_raises(self) -> None:
        """Verify reset with negative starting amount raises ValueError."""
        tracker = BankrollTracker(1000.0)

        with pytest.raises(ValueError) as exc_info:
            tracker.reset(-500.0)

        assert "Starting amount cannot be negative" in str(exc_info.value)

    def test_reset_allows_tracking_after_reset(self) -> None:
        """Verify tracker works correctly after reset."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)
        tracker.apply_result(-200.0)

        tracker.reset()

        # Apply new transactions
        tracker.apply_result(100.0)
        tracker.apply_result(-50.0)

        assert tracker.balance == 1050.0
        assert tracker.session_profit == 50.0
        assert tracker.peak_balance == 1100.0
        assert tracker.max_drawdown == 50.0

    def test_reset_with_zero_starting_amount(self) -> None:
        """Verify reset works with zero starting amount (edge case)."""
        tracker = BankrollTracker(1000.0)
        tracker.apply_result(500.0)

        tracker.reset(0.0)

        assert tracker.balance == 0.0
        assert tracker.starting_balance == 0.0
        assert tracker.session_profit == 0.0
        assert tracker.peak_balance == 0.0

    def test_multiple_consecutive_resets(self) -> None:
        """Verify tracker handles multiple consecutive resets correctly."""
        tracker = BankrollTracker(1000.0)

        # First session
        tracker.apply_result(200.0)
        tracker.reset(500.0)

        # Second session
        tracker.apply_result(-100.0)
        tracker.reset(2000.0)

        # Third session
        tracker.apply_result(50.0)

        assert tracker.balance == 2050.0
        assert tracker.starting_balance == 2000.0
        assert tracker.session_profit == 50.0
        assert tracker.peak_balance == 2050.0
