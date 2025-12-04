"""Unit tests for betting systems."""

import pytest

from let_it_ride.bankroll.betting_systems import (
    BettingContext,
    BettingSystem,
    DAlembertBetting,
    FibonacciBetting,
    FlatBetting,
    MartingaleBetting,
    ParoliBetting,
    ReverseMartingaleBetting,
)


class TestBettingContext:
    """Tests for BettingContext dataclass."""

    def test_create_betting_context(self) -> None:
        """Verify BettingContext can be created with all fields."""
        context = BettingContext(
            bankroll=500.0,
            starting_bankroll=1000.0,
            session_profit=-500.0,
            last_result=-25.0,
            streak=-2,
            hands_played=10,
        )
        assert context.bankroll == 500.0
        assert context.starting_bankroll == 1000.0
        assert context.session_profit == -500.0
        assert context.last_result == -25.0
        assert context.streak == -2
        assert context.hands_played == 10

    def test_create_betting_context_first_hand(self) -> None:
        """Verify BettingContext for first hand of session."""
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert context.last_result is None
        assert context.streak == 0
        assert context.hands_played == 0

    def test_betting_context_winning_streak(self) -> None:
        """Verify BettingContext with positive streak."""
        context = BettingContext(
            bankroll=1200.0,
            starting_bankroll=1000.0,
            session_profit=200.0,
            last_result=50.0,
            streak=3,
            hands_played=5,
        )
        assert context.streak == 3
        assert context.last_result == 50.0

    def test_betting_context_losing_streak(self) -> None:
        """Verify BettingContext with negative streak."""
        context = BettingContext(
            bankroll=800.0,
            starting_bankroll=1000.0,
            session_profit=-200.0,
            last_result=-25.0,
            streak=-4,
            hands_played=8,
        )
        assert context.streak == -4
        assert context.last_result == -25.0

    def test_betting_context_is_frozen(self) -> None:
        """Verify BettingContext is immutable (frozen)."""
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        with pytest.raises(AttributeError):
            context.bankroll = 500.0  # type: ignore[misc]

    def test_betting_context_is_hashable(self) -> None:
        """Verify BettingContext is hashable (enabled by frozen=True)."""
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        # Should not raise - frozen dataclasses are hashable
        hash_value = hash(context)
        assert isinstance(hash_value, int)


class TestFlatBettingInitialization:
    """Tests for FlatBetting initialization."""

    def test_initialization_with_positive_bet(self) -> None:
        """Verify FlatBetting initializes with positive base bet."""
        betting = FlatBetting(25.0)
        assert betting.base_bet == 25.0

    def test_initialization_with_small_bet(self) -> None:
        """Verify FlatBetting accepts very small positive bets."""
        betting = FlatBetting(0.01)
        assert betting.base_bet == 0.01

    def test_initialization_with_large_bet(self) -> None:
        """Verify FlatBetting accepts large bets."""
        betting = FlatBetting(10000.0)
        assert betting.base_bet == 10000.0

    def test_initialization_with_zero_bet_raises(self) -> None:
        """Verify zero base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FlatBetting(0.0)
        assert "Base bet must be positive" in str(exc_info.value)

    def test_initialization_with_negative_bet_raises(self) -> None:
        """Verify negative base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FlatBetting(-25.0)
        assert "Base bet must be positive" in str(exc_info.value)


class TestFlatBettingGetBet:
    """Tests for FlatBetting.get_bet() method."""

    def test_get_bet_normal_bankroll(self) -> None:
        """Verify get_bet returns base bet when bankroll is sufficient."""
        betting = FlatBetting(25.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert betting.get_bet(context) == 25.0

    def test_get_bet_exactly_enough_bankroll(self) -> None:
        """Verify get_bet returns base bet when bankroll equals bet."""
        betting = FlatBetting(25.0)
        context = BettingContext(
            bankroll=25.0,
            starting_bankroll=1000.0,
            session_profit=-975.0,
            last_result=-25.0,
            streak=-10,
            hands_played=20,
        )
        assert betting.get_bet(context) == 25.0

    def test_get_bet_ignores_streak(self) -> None:
        """Verify get_bet ignores streak information."""
        betting = FlatBetting(25.0)

        # Winning streak
        context = BettingContext(
            bankroll=1500.0,
            starting_bankroll=1000.0,
            session_profit=500.0,
            last_result=100.0,
            streak=5,
            hands_played=10,
        )
        assert betting.get_bet(context) == 25.0

        # Losing streak
        context = BettingContext(
            bankroll=500.0,
            starting_bankroll=1000.0,
            session_profit=-500.0,
            last_result=-25.0,
            streak=-10,
            hands_played=20,
        )
        assert betting.get_bet(context) == 25.0

    def test_get_bet_ignores_session_profit(self) -> None:
        """Verify get_bet ignores session profit."""
        betting = FlatBetting(25.0)

        # Big profit
        context = BettingContext(
            bankroll=5000.0,
            starting_bankroll=1000.0,
            session_profit=4000.0,
            last_result=500.0,
            streak=2,
            hands_played=50,
        )
        assert betting.get_bet(context) == 25.0


class TestFlatBettingInsufficientBankroll:
    """Tests for FlatBetting with insufficient bankroll."""

    def test_get_bet_reduced_when_bankroll_less_than_bet(self) -> None:
        """Verify get_bet returns bankroll when less than base bet."""
        betting = FlatBetting(25.0)
        context = BettingContext(
            bankroll=15.0,
            starting_bankroll=1000.0,
            session_profit=-985.0,
            last_result=-25.0,
            streak=-15,
            hands_played=30,
        )
        assert betting.get_bet(context) == 15.0

    def test_get_bet_returns_small_remaining_bankroll(self) -> None:
        """Verify get_bet returns very small remaining bankroll."""
        betting = FlatBetting(25.0)
        context = BettingContext(
            bankroll=0.50,
            starting_bankroll=1000.0,
            session_profit=-999.50,
            last_result=-25.0,
            streak=-20,
            hands_played=40,
        )
        assert betting.get_bet(context) == 0.50

    def test_get_bet_zero_bankroll(self) -> None:
        """Verify get_bet returns 0 when bankroll is zero."""
        betting = FlatBetting(25.0)
        context = BettingContext(
            bankroll=0.0,
            starting_bankroll=1000.0,
            session_profit=-1000.0,
            last_result=-25.0,
            streak=-25,
            hands_played=50,
        )
        assert betting.get_bet(context) == 0.0

    def test_get_bet_negative_bankroll(self) -> None:
        """Verify get_bet returns 0 when bankroll is negative."""
        betting = FlatBetting(25.0)
        context = BettingContext(
            bankroll=-50.0,
            starting_bankroll=1000.0,
            session_profit=-1050.0,
            last_result=-75.0,
            streak=-30,
            hands_played=55,
        )
        assert betting.get_bet(context) == 0.0

    def test_get_bet_floating_point_precision_edge_case(self) -> None:
        """Verify get_bet handles floating-point precision near base_bet."""
        betting = FlatBetting(25.0)
        # Bankroll extremely close to but not exactly equal to base_bet
        # This tests floating-point precision handling
        context = BettingContext(
            bankroll=24.999999999999996,  # Just under 25.0 due to FP precision
            starting_bankroll=1000.0,
            session_profit=-975.0,
            last_result=-25.0,
            streak=-10,
            hands_played=20,
        )
        # Should return the bankroll (slightly less than base bet)
        result = betting.get_bet(context)
        assert result == 24.999999999999996
        assert result < 25.0

    def test_get_bet_floating_point_precision_slightly_over(self) -> None:
        """Verify get_bet handles floating-point precision slightly over base_bet."""
        betting = FlatBetting(25.0)
        # Bankroll just over base_bet due to FP precision
        context = BettingContext(
            bankroll=25.000000000000004,  # Just over 25.0 due to FP precision
            starting_bankroll=1000.0,
            session_profit=-975.0,
            last_result=0.000000000000004,
            streak=0,
            hands_played=20,
        )
        # Should return the base bet (min of base_bet and bankroll)
        result = betting.get_bet(context)
        assert result == 25.0


class TestFlatBettingRecordResult:
    """Tests for FlatBetting.record_result() method."""

    def test_record_result_no_effect(self) -> None:
        """Verify record_result is a no-op for flat betting."""
        betting = FlatBetting(25.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Record various results
        betting.record_result(100.0)
        betting.record_result(-25.0)
        betting.record_result(0.0)

        # Bet should still be the same
        assert betting.get_bet(context) == 25.0

    def test_record_result_with_win(self) -> None:
        """Verify record_result handles wins (no-op)."""
        betting = FlatBetting(25.0)
        betting.record_result(100.0)
        # No exception, no effect

    def test_record_result_with_loss(self) -> None:
        """Verify record_result handles losses (no-op)."""
        betting = FlatBetting(25.0)
        betting.record_result(-25.0)
        # No exception, no effect


class TestFlatBettingReset:
    """Tests for FlatBetting.reset() method."""

    def test_reset_no_effect(self) -> None:
        """Verify reset is a no-op for flat betting."""
        betting = FlatBetting(25.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Reset should have no effect
        betting.reset()
        assert betting.get_bet(context) == 25.0

    def test_reset_called_multiple_times(self) -> None:
        """Verify reset can be called multiple times without error."""
        betting = FlatBetting(25.0)
        betting.reset()
        betting.reset()
        betting.reset()
        # No exception


class TestFlatBettingRepr:
    """Tests for FlatBetting string representation."""

    def test_repr(self) -> None:
        """Verify repr of FlatBetting."""
        betting = FlatBetting(25.0)
        assert repr(betting) == "FlatBetting(base_bet=25.0)"

    def test_repr_with_decimal_bet(self) -> None:
        """Verify repr with non-integer bet."""
        betting = FlatBetting(10.50)
        assert repr(betting) == "FlatBetting(base_bet=10.5)"


class TestFlatBettingProtocolCompliance:
    """Tests verifying FlatBetting satisfies BettingSystem protocol."""

    def test_implements_betting_system(self) -> None:
        """Verify FlatBetting implements BettingSystem protocol.

        This test uses structural typing to verify protocol compliance.
        """
        betting = FlatBetting(25.0)

        # Verify all required methods exist with correct signatures
        assert hasattr(betting, "get_bet")
        assert hasattr(betting, "record_result")
        assert hasattr(betting, "reset")

        # Verify methods are callable
        assert callable(betting.get_bet)
        assert callable(betting.record_result)
        assert callable(betting.reset)

    def test_can_be_used_as_betting_system(self) -> None:
        """Verify FlatBetting can be used where BettingSystem is expected."""

        def use_betting_system(system: BettingSystem) -> float:
            context = BettingContext(
                bankroll=100.0,
                starting_bankroll=100.0,
                session_profit=0.0,
                last_result=None,
                streak=0,
                hands_played=0,
            )
            return system.get_bet(context)

        betting = FlatBetting(10.0)
        result = use_betting_system(betting)
        assert result == 10.0


class TestBettingSystemScenarios:
    """Integration-style tests for complete betting scenarios."""

    def test_session_with_declining_bankroll(self) -> None:
        """Verify betting behavior through declining bankroll session."""
        betting = FlatBetting(25.0)

        # Start of session
        context = BettingContext(
            bankroll=100.0,
            starting_bankroll=100.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert betting.get_bet(context) == 25.0

        # After some losses, still enough bankroll
        context = BettingContext(
            bankroll=50.0,
            starting_bankroll=100.0,
            session_profit=-50.0,
            last_result=-25.0,
            streak=-2,
            hands_played=2,
        )
        assert betting.get_bet(context) == 25.0

        # Bankroll getting low
        context = BettingContext(
            bankroll=20.0,
            starting_bankroll=100.0,
            session_profit=-80.0,
            last_result=-25.0,
            streak=-3,
            hands_played=3,
        )
        assert betting.get_bet(context) == 20.0  # Reduced bet

        # Very low bankroll
        context = BettingContext(
            bankroll=5.0,
            starting_bankroll=100.0,
            session_profit=-95.0,
            last_result=-15.0,
            streak=-4,
            hands_played=4,
        )
        assert betting.get_bet(context) == 5.0  # Minimal bet

        # Bankroll exhausted
        context = BettingContext(
            bankroll=0.0,
            starting_bankroll=100.0,
            session_profit=-100.0,
            last_result=-5.0,
            streak=-5,
            hands_played=5,
        )
        assert betting.get_bet(context) == 0.0  # Can't bet

    def test_session_with_wins_and_losses(self) -> None:
        """Verify betting remains constant through wins and losses."""
        betting = FlatBetting(25.0)

        # Start
        context = BettingContext(
            bankroll=100.0,
            starting_bankroll=100.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert betting.get_bet(context) == 25.0
        betting.record_result(50.0)

        # After win
        context = BettingContext(
            bankroll=150.0,
            starting_bankroll=100.0,
            session_profit=50.0,
            last_result=50.0,
            streak=1,
            hands_played=1,
        )
        assert betting.get_bet(context) == 25.0
        betting.record_result(-25.0)

        # After loss
        context = BettingContext(
            bankroll=125.0,
            starting_bankroll=100.0,
            session_profit=25.0,
            last_result=-25.0,
            streak=-1,
            hands_played=2,
        )
        assert betting.get_bet(context) == 25.0

        # Reset for new session
        betting.reset()
        context = BettingContext(
            bankroll=200.0,
            starting_bankroll=200.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert betting.get_bet(context) == 25.0


# =============================================================================
# Martingale Betting Tests
# =============================================================================


class TestMartingaleBettingInitialization:
    """Tests for MartingaleBetting initialization."""

    def test_initialization_with_defaults(self) -> None:
        """Verify MartingaleBetting initializes with default values."""
        betting = MartingaleBetting(base_bet=10.0)
        assert betting.base_bet == 10.0
        assert betting.loss_multiplier == 2.0
        assert betting.max_bet == 500.0
        assert betting.max_progressions == 6
        assert betting.current_progression == 0

    def test_initialization_with_custom_values(self) -> None:
        """Verify MartingaleBetting initializes with custom values."""
        betting = MartingaleBetting(
            base_bet=25.0,
            loss_multiplier=3.0,
            max_bet=1000.0,
            max_progressions=4,
        )
        assert betting.base_bet == 25.0
        assert betting.loss_multiplier == 3.0
        assert betting.max_bet == 1000.0
        assert betting.max_progressions == 4

    def test_initialization_zero_base_bet_raises(self) -> None:
        """Verify zero base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            MartingaleBetting(base_bet=0.0)
        assert "Base bet must be positive" in str(exc_info.value)

    def test_initialization_negative_base_bet_raises(self) -> None:
        """Verify negative base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            MartingaleBetting(base_bet=-10.0)
        assert "Base bet must be positive" in str(exc_info.value)

    def test_initialization_invalid_loss_multiplier_raises(self) -> None:
        """Verify loss_multiplier <= 1 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            MartingaleBetting(base_bet=10.0, loss_multiplier=1.0)
        assert "Loss multiplier must be greater than 1" in str(exc_info.value)

    def test_initialization_zero_max_bet_raises(self) -> None:
        """Verify zero max bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            MartingaleBetting(base_bet=10.0, max_bet=0.0)
        assert "Max bet must be positive" in str(exc_info.value)

    def test_initialization_zero_max_progressions_raises(self) -> None:
        """Verify zero max progressions raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            MartingaleBetting(base_bet=10.0, max_progressions=0)
        assert "Max progressions must be at least 1" in str(exc_info.value)


class TestMartingaleBettingProgression:
    """Tests for MartingaleBetting progression logic."""

    def test_base_bet_at_start(self) -> None:
        """Verify base bet at start of session."""
        betting = MartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert betting.get_bet(context) == 10.0

    def test_double_after_loss(self) -> None:
        """Verify bet doubles after a loss."""
        betting = MartingaleBetting(base_bet=10.0, loss_multiplier=2.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Initial bet
        assert betting.get_bet(context) == 10.0

        # After loss
        betting.record_result(-10.0)
        assert betting.get_bet(context) == 20.0

        # After another loss
        betting.record_result(-20.0)
        assert betting.get_bet(context) == 40.0

    def test_reset_after_win(self) -> None:
        """Verify progression resets after a win."""
        betting = MartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Progress to higher bet
        betting.record_result(-10.0)
        betting.record_result(-20.0)
        assert betting.get_bet(context) == 40.0

        # Win - should reset
        betting.record_result(40.0)
        assert betting.get_bet(context) == 10.0

    def test_reset_on_push(self) -> None:
        """Verify progression resets on push (result = 0)."""
        betting = MartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(-10.0)
        assert betting.get_bet(context) == 20.0

        # Push
        betting.record_result(0.0)
        assert betting.get_bet(context) == 10.0

    def test_max_progressions_limit(self) -> None:
        """Verify progression is capped at max_progressions."""
        betting = MartingaleBetting(base_bet=10.0, max_progressions=3)
        context = BettingContext(
            bankroll=10000.0,
            starting_bankroll=10000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Progress: 10 -> 20 -> 40 (max at 3 progressions = position 2)
        betting.record_result(-10.0)  # Position 1
        betting.record_result(-20.0)  # Position 2 (max-1)
        assert betting.get_bet(context) == 40.0

        # Another loss should not increase further
        betting.record_result(-40.0)
        assert betting.get_bet(context) == 40.0

    def test_max_bet_limit(self) -> None:
        """Verify bet is capped at max_bet."""
        betting = MartingaleBetting(base_bet=100.0, max_bet=250.0, max_progressions=10)
        context = BettingContext(
            bankroll=10000.0,
            starting_bankroll=10000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # 100 -> 200 -> 400 (but capped at 250)
        betting.record_result(-100.0)
        assert betting.get_bet(context) == 200.0

        betting.record_result(-200.0)
        assert betting.get_bet(context) == 250.0  # Capped


class TestMartingaleBettingBankrollLimits:
    """Tests for MartingaleBetting bankroll handling."""

    def test_bet_capped_by_bankroll(self) -> None:
        """Verify bet is capped at available bankroll."""
        betting = MartingaleBetting(base_bet=10.0)

        # Progress to higher bet
        betting.record_result(-10.0)
        betting.record_result(-20.0)

        context = BettingContext(
            bankroll=30.0,
            starting_bankroll=1000.0,
            session_profit=-970.0,
            last_result=-20.0,
            streak=-2,
            hands_played=2,
        )
        # Would be 40, but bankroll is only 30
        assert betting.get_bet(context) == 30.0

    def test_zero_bankroll(self) -> None:
        """Verify zero bet with zero bankroll."""
        betting = MartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=0.0,
            starting_bankroll=1000.0,
            session_profit=-1000.0,
            last_result=-10.0,
            streak=-10,
            hands_played=10,
        )
        assert betting.get_bet(context) == 0.0


class TestMartingaleBettingReset:
    """Tests for MartingaleBetting.reset() method."""

    def test_reset_clears_progression(self) -> None:
        """Verify reset clears the progression."""
        betting = MartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Progress
        betting.record_result(-10.0)
        betting.record_result(-20.0)
        assert betting.current_progression == 2

        # Reset
        betting.reset()
        assert betting.current_progression == 0
        assert betting.get_bet(context) == 10.0


class TestMartingaleBettingRepr:
    """Tests for MartingaleBetting string representation."""

    def test_repr(self) -> None:
        """Verify repr of MartingaleBetting."""
        betting = MartingaleBetting(base_bet=10.0, loss_multiplier=2.0, max_bet=500.0, max_progressions=6)
        expected = "MartingaleBetting(base_bet=10.0, loss_multiplier=2.0, max_bet=500.0, max_progressions=6)"
        assert repr(betting) == expected


class TestMartingaleBettingProtocol:
    """Tests for MartingaleBetting protocol compliance."""

    def test_implements_betting_system(self) -> None:
        """Verify MartingaleBetting implements BettingSystem protocol."""
        betting = MartingaleBetting(base_bet=10.0)
        assert hasattr(betting, "get_bet")
        assert hasattr(betting, "record_result")
        assert hasattr(betting, "reset")

    def test_can_be_used_as_betting_system(self) -> None:
        """Verify MartingaleBetting can be used where BettingSystem is expected."""

        def use_betting_system(system: BettingSystem) -> float:
            context = BettingContext(
                bankroll=100.0,
                starting_bankroll=100.0,
                session_profit=0.0,
                last_result=None,
                streak=0,
                hands_played=0,
            )
            return system.get_bet(context)

        betting = MartingaleBetting(base_bet=10.0)
        result = use_betting_system(betting)
        assert result == 10.0


# =============================================================================
# Reverse Martingale Betting Tests
# =============================================================================


class TestReverseMartingaleBettingInitialization:
    """Tests for ReverseMartingaleBetting initialization."""

    def test_initialization_with_defaults(self) -> None:
        """Verify ReverseMartingaleBetting initializes with default values."""
        betting = ReverseMartingaleBetting(base_bet=10.0)
        assert betting.base_bet == 10.0
        assert betting.win_multiplier == 2.0
        assert betting.profit_target_streak == 3
        assert betting.max_bet == 500.0
        assert betting.win_streak == 0

    def test_initialization_with_custom_values(self) -> None:
        """Verify ReverseMartingaleBetting initializes with custom values."""
        betting = ReverseMartingaleBetting(
            base_bet=25.0,
            win_multiplier=1.5,
            profit_target_streak=4,
            max_bet=1000.0,
        )
        assert betting.base_bet == 25.0
        assert betting.win_multiplier == 1.5
        assert betting.profit_target_streak == 4
        assert betting.max_bet == 1000.0

    def test_initialization_zero_base_bet_raises(self) -> None:
        """Verify zero base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReverseMartingaleBetting(base_bet=0.0)
        assert "Base bet must be positive" in str(exc_info.value)

    def test_initialization_invalid_win_multiplier_raises(self) -> None:
        """Verify win_multiplier <= 1 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReverseMartingaleBetting(base_bet=10.0, win_multiplier=1.0)
        assert "Win multiplier must be greater than 1" in str(exc_info.value)

    def test_initialization_zero_profit_target_raises(self) -> None:
        """Verify zero profit_target_streak raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReverseMartingaleBetting(base_bet=10.0, profit_target_streak=0)
        assert "Profit target streak must be at least 1" in str(exc_info.value)

    def test_initialization_zero_max_bet_raises(self) -> None:
        """Verify zero max bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReverseMartingaleBetting(base_bet=10.0, max_bet=0.0)
        assert "Max bet must be positive" in str(exc_info.value)


class TestReverseMartingaleBettingProgression:
    """Tests for ReverseMartingaleBetting progression logic."""

    def test_base_bet_at_start(self) -> None:
        """Verify base bet at start of session."""
        betting = ReverseMartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert betting.get_bet(context) == 10.0

    def test_double_after_win(self) -> None:
        """Verify bet doubles after a win."""
        betting = ReverseMartingaleBetting(base_bet=10.0, win_multiplier=2.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        assert betting.get_bet(context) == 10.0

        betting.record_result(10.0)  # Win
        assert betting.get_bet(context) == 20.0

        betting.record_result(20.0)  # Win again
        assert betting.get_bet(context) == 40.0

    def test_reset_after_loss(self) -> None:
        """Verify progression resets after a loss."""
        betting = ReverseMartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(10.0)
        betting.record_result(20.0)
        assert betting.get_bet(context) == 40.0

        betting.record_result(-40.0)  # Loss
        assert betting.get_bet(context) == 10.0

    def test_reset_on_push(self) -> None:
        """Verify progression resets on push."""
        betting = ReverseMartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(10.0)
        assert betting.get_bet(context) == 20.0

        betting.record_result(0.0)  # Push
        assert betting.get_bet(context) == 10.0

    def test_reset_after_profit_target(self) -> None:
        """Verify reset after reaching profit target streak."""
        betting = ReverseMartingaleBetting(base_bet=10.0, profit_target_streak=3)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(10.0)  # Streak = 1
        assert betting.get_bet(context) == 20.0

        betting.record_result(20.0)  # Streak = 2
        assert betting.get_bet(context) == 40.0

        betting.record_result(40.0)  # Streak = 3 (target reached, reset)
        assert betting.get_bet(context) == 10.0

    def test_max_bet_limit(self) -> None:
        """Verify bet is capped at max_bet."""
        betting = ReverseMartingaleBetting(base_bet=100.0, max_bet=150.0, profit_target_streak=10)
        context = BettingContext(
            bankroll=10000.0,
            starting_bankroll=10000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(100.0)  # 200
        assert betting.get_bet(context) == 150.0  # Capped


class TestReverseMartingaleBettingReset:
    """Tests for ReverseMartingaleBetting.reset() method."""

    def test_reset_clears_win_streak(self) -> None:
        """Verify reset clears the win streak."""
        betting = ReverseMartingaleBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(10.0)
        betting.record_result(20.0)
        assert betting.win_streak == 2

        betting.reset()
        assert betting.win_streak == 0
        assert betting.get_bet(context) == 10.0


class TestReverseMartingaleBettingRepr:
    """Tests for ReverseMartingaleBetting string representation."""

    def test_repr(self) -> None:
        """Verify repr of ReverseMartingaleBetting."""
        betting = ReverseMartingaleBetting(
            base_bet=10.0, win_multiplier=2.0, profit_target_streak=3, max_bet=500.0
        )
        expected = "ReverseMartingaleBetting(base_bet=10.0, win_multiplier=2.0, profit_target_streak=3, max_bet=500.0)"
        assert repr(betting) == expected


class TestReverseMartingaleBettingProtocol:
    """Tests for ReverseMartingaleBetting protocol compliance."""

    def test_can_be_used_as_betting_system(self) -> None:
        """Verify ReverseMartingaleBetting can be used where BettingSystem is expected."""

        def use_betting_system(system: BettingSystem) -> float:
            context = BettingContext(
                bankroll=100.0,
                starting_bankroll=100.0,
                session_profit=0.0,
                last_result=None,
                streak=0,
                hands_played=0,
            )
            return system.get_bet(context)

        betting = ReverseMartingaleBetting(base_bet=10.0)
        result = use_betting_system(betting)
        assert result == 10.0


# =============================================================================
# Paroli Betting Tests
# =============================================================================


class TestParoliBettingInitialization:
    """Tests for ParoliBetting initialization."""

    def test_initialization_with_defaults(self) -> None:
        """Verify ParoliBetting initializes with default values."""
        betting = ParoliBetting(base_bet=10.0)
        assert betting.base_bet == 10.0
        assert betting.win_multiplier == 2.0
        assert betting.wins_before_reset == 3
        assert betting.max_bet == 500.0
        assert betting.consecutive_wins == 0

    def test_initialization_with_custom_values(self) -> None:
        """Verify ParoliBetting initializes with custom values."""
        betting = ParoliBetting(
            base_bet=25.0,
            win_multiplier=1.5,
            wins_before_reset=4,
            max_bet=1000.0,
        )
        assert betting.base_bet == 25.0
        assert betting.win_multiplier == 1.5
        assert betting.wins_before_reset == 4
        assert betting.max_bet == 1000.0

    def test_initialization_zero_base_bet_raises(self) -> None:
        """Verify zero base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ParoliBetting(base_bet=0.0)
        assert "Base bet must be positive" in str(exc_info.value)

    def test_initialization_invalid_win_multiplier_raises(self) -> None:
        """Verify win_multiplier <= 1 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ParoliBetting(base_bet=10.0, win_multiplier=1.0)
        assert "Win multiplier must be greater than 1" in str(exc_info.value)

    def test_initialization_zero_wins_before_reset_raises(self) -> None:
        """Verify zero wins_before_reset raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ParoliBetting(base_bet=10.0, wins_before_reset=0)
        assert "Wins before reset must be at least 1" in str(exc_info.value)


class TestParoliBettingProgression:
    """Tests for ParoliBetting progression logic."""

    def test_base_bet_at_start(self) -> None:
        """Verify base bet at start of session."""
        betting = ParoliBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert betting.get_bet(context) == 10.0

    def test_increase_after_win(self) -> None:
        """Verify bet increases after a win."""
        betting = ParoliBetting(base_bet=10.0, win_multiplier=2.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        assert betting.get_bet(context) == 10.0

        betting.record_result(10.0)
        assert betting.get_bet(context) == 20.0

        betting.record_result(20.0)
        assert betting.get_bet(context) == 40.0

    def test_reset_after_loss(self) -> None:
        """Verify progression resets after a loss."""
        betting = ParoliBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(10.0)
        betting.record_result(20.0)
        assert betting.get_bet(context) == 40.0

        betting.record_result(-40.0)
        assert betting.get_bet(context) == 10.0

    def test_reset_after_wins_before_reset(self) -> None:
        """Verify reset after reaching wins_before_reset."""
        betting = ParoliBetting(base_bet=10.0, wins_before_reset=3)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(10.0)  # Win 1
        assert betting.get_bet(context) == 20.0

        betting.record_result(20.0)  # Win 2
        assert betting.get_bet(context) == 40.0

        betting.record_result(40.0)  # Win 3 (reset)
        assert betting.get_bet(context) == 10.0

    def test_max_bet_limit(self) -> None:
        """Verify bet is capped at max_bet."""
        betting = ParoliBetting(base_bet=100.0, max_bet=150.0, wins_before_reset=10)
        context = BettingContext(
            bankroll=10000.0,
            starting_bankroll=10000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(100.0)
        assert betting.get_bet(context) == 150.0  # Capped


class TestParoliBettingReset:
    """Tests for ParoliBetting.reset() method."""

    def test_reset_clears_consecutive_wins(self) -> None:
        """Verify reset clears the consecutive wins."""
        betting = ParoliBetting(base_bet=10.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(10.0)
        betting.record_result(20.0)
        assert betting.consecutive_wins == 2

        betting.reset()
        assert betting.consecutive_wins == 0
        assert betting.get_bet(context) == 10.0


class TestParoliBettingRepr:
    """Tests for ParoliBetting string representation."""

    def test_repr(self) -> None:
        """Verify repr of ParoliBetting."""
        betting = ParoliBetting(base_bet=10.0, win_multiplier=2.0, wins_before_reset=3, max_bet=500.0)
        expected = "ParoliBetting(base_bet=10.0, win_multiplier=2.0, wins_before_reset=3, max_bet=500.0)"
        assert repr(betting) == expected


class TestParoliBettingProtocol:
    """Tests for ParoliBetting protocol compliance."""

    def test_can_be_used_as_betting_system(self) -> None:
        """Verify ParoliBetting can be used where BettingSystem is expected."""

        def use_betting_system(system: BettingSystem) -> float:
            context = BettingContext(
                bankroll=100.0,
                starting_bankroll=100.0,
                session_profit=0.0,
                last_result=None,
                streak=0,
                hands_played=0,
            )
            return system.get_bet(context)

        betting = ParoliBetting(base_bet=10.0)
        result = use_betting_system(betting)
        assert result == 10.0


# =============================================================================
# D'Alembert Betting Tests
# =============================================================================


class TestDAlembertBettingInitialization:
    """Tests for DAlembertBetting initialization."""

    def test_initialization_with_defaults(self) -> None:
        """Verify DAlembertBetting initializes with default values."""
        betting = DAlembertBetting(base_bet=25.0)
        assert betting.base_bet == 25.0
        assert betting.unit == 5.0
        assert betting.min_bet == 5.0
        assert betting.max_bet == 500.0
        assert betting.current_bet == 25.0

    def test_initialization_with_custom_values(self) -> None:
        """Verify DAlembertBetting initializes with custom values."""
        betting = DAlembertBetting(
            base_bet=50.0,
            unit=10.0,
            min_bet=10.0,
            max_bet=200.0,
        )
        assert betting.base_bet == 50.0
        assert betting.unit == 10.0
        assert betting.min_bet == 10.0
        assert betting.max_bet == 200.0

    def test_initialization_zero_base_bet_raises(self) -> None:
        """Verify zero base bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DAlembertBetting(base_bet=0.0)
        assert "Base bet must be positive" in str(exc_info.value)

    def test_initialization_zero_unit_raises(self) -> None:
        """Verify zero unit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DAlembertBetting(base_bet=25.0, unit=0.0)
        assert "Unit must be positive" in str(exc_info.value)

    def test_initialization_zero_min_bet_raises(self) -> None:
        """Verify zero min bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DAlembertBetting(base_bet=25.0, min_bet=0.0)
        assert "Min bet must be positive" in str(exc_info.value)

    def test_initialization_zero_max_bet_raises(self) -> None:
        """Verify zero max bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DAlembertBetting(base_bet=25.0, max_bet=0.0)
        assert "Max bet must be positive" in str(exc_info.value)

    def test_initialization_min_greater_than_max_raises(self) -> None:
        """Verify min_bet > max_bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DAlembertBetting(base_bet=25.0, min_bet=100.0, max_bet=50.0)
        assert "Min bet cannot exceed max bet" in str(exc_info.value)


class TestDAlembertBettingProgression:
    """Tests for DAlembertBetting progression logic."""

    def test_base_bet_at_start(self) -> None:
        """Verify base bet at start of session."""
        betting = DAlembertBetting(base_bet=25.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        assert betting.get_bet(context) == 25.0

    def test_increase_after_loss(self) -> None:
        """Verify bet increases by unit after loss."""
        betting = DAlembertBetting(base_bet=25.0, unit=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        assert betting.get_bet(context) == 25.0

        betting.record_result(-25.0)
        assert betting.get_bet(context) == 30.0

        betting.record_result(-30.0)
        assert betting.get_bet(context) == 35.0

    def test_decrease_after_win(self) -> None:
        """Verify bet decreases by unit after win."""
        betting = DAlembertBetting(base_bet=25.0, unit=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Increase first
        betting.record_result(-25.0)
        betting.record_result(-30.0)
        assert betting.get_bet(context) == 35.0

        # Now decrease
        betting.record_result(35.0)
        assert betting.get_bet(context) == 30.0

        betting.record_result(30.0)
        assert betting.get_bet(context) == 25.0

    def test_no_change_on_push(self) -> None:
        """Verify bet stays the same on push."""
        betting = DAlembertBetting(base_bet=25.0, unit=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(-25.0)
        assert betting.get_bet(context) == 30.0

        betting.record_result(0.0)  # Push
        assert betting.get_bet(context) == 30.0

    def test_min_bet_floor(self) -> None:
        """Verify bet doesn't go below min_bet."""
        betting = DAlembertBetting(base_bet=10.0, unit=5.0, min_bet=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        assert betting.get_bet(context) == 10.0

        betting.record_result(10.0)  # Win -> 5
        assert betting.get_bet(context) == 5.0

        betting.record_result(5.0)  # Win -> would be 0, but min is 5
        assert betting.get_bet(context) == 5.0

    def test_max_bet_cap(self) -> None:
        """Verify bet doesn't exceed max_bet."""
        betting = DAlembertBetting(base_bet=25.0, unit=5.0, max_bet=35.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(-25.0)  # 30
        betting.record_result(-30.0)  # 35 (max)
        assert betting.get_bet(context) == 35.0

        betting.record_result(-35.0)  # Would be 40, capped at 35
        assert betting.get_bet(context) == 35.0


class TestDAlembertBettingBankrollLimits:
    """Tests for DAlembertBetting bankroll handling."""

    def test_bet_capped_by_bankroll(self) -> None:
        """Verify bet is capped at available bankroll."""
        betting = DAlembertBetting(base_bet=25.0, unit=5.0)

        betting.record_result(-25.0)
        betting.record_result(-30.0)

        context = BettingContext(
            bankroll=30.0,
            starting_bankroll=1000.0,
            session_profit=-970.0,
            last_result=-30.0,
            streak=-2,
            hands_played=2,
        )
        # Would be 35, but bankroll is only 30
        assert betting.get_bet(context) == 30.0


class TestDAlembertBettingReset:
    """Tests for DAlembertBetting.reset() method."""

    def test_reset_restores_base_bet(self) -> None:
        """Verify reset restores the base bet."""
        betting = DAlembertBetting(base_bet=25.0, unit=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(-25.0)
        betting.record_result(-30.0)
        assert betting.current_bet == 35.0

        betting.reset()
        assert betting.current_bet == 25.0
        assert betting.get_bet(context) == 25.0


class TestDAlembertBettingRepr:
    """Tests for DAlembertBetting string representation."""

    def test_repr(self) -> None:
        """Verify repr of DAlembertBetting."""
        betting = DAlembertBetting(base_bet=25.0, unit=5.0, min_bet=5.0, max_bet=500.0)
        expected = "DAlembertBetting(base_bet=25.0, unit=5.0, min_bet=5.0, max_bet=500.0)"
        assert repr(betting) == expected


class TestDAlembertBettingProtocol:
    """Tests for DAlembertBetting protocol compliance."""

    def test_can_be_used_as_betting_system(self) -> None:
        """Verify DAlembertBetting can be used where BettingSystem is expected."""

        def use_betting_system(system: BettingSystem) -> float:
            context = BettingContext(
                bankroll=100.0,
                starting_bankroll=100.0,
                session_profit=0.0,
                last_result=None,
                streak=0,
                hands_played=0,
            )
            return system.get_bet(context)

        betting = DAlembertBetting(base_bet=10.0)
        result = use_betting_system(betting)
        assert result == 10.0


# =============================================================================
# Fibonacci Betting Tests
# =============================================================================


class TestFibonacciBettingInitialization:
    """Tests for FibonacciBetting initialization."""

    def test_initialization_with_defaults(self) -> None:
        """Verify FibonacciBetting initializes with default values."""
        betting = FibonacciBetting()
        assert betting.base_unit == 5.0
        assert betting.win_regression == 2
        assert betting.max_bet == 500.0
        assert betting.max_position == 10
        assert betting.position == 0

    def test_initialization_with_custom_values(self) -> None:
        """Verify FibonacciBetting initializes with custom values."""
        betting = FibonacciBetting(
            base_unit=10.0,
            win_regression=3,
            max_bet=1000.0,
            max_position=8,
        )
        assert betting.base_unit == 10.0
        assert betting.win_regression == 3
        assert betting.max_bet == 1000.0
        assert betting.max_position == 8

    def test_initialization_zero_base_unit_raises(self) -> None:
        """Verify zero base unit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FibonacciBetting(base_unit=0.0)
        assert "Base unit must be positive" in str(exc_info.value)

    def test_initialization_zero_win_regression_raises(self) -> None:
        """Verify zero win_regression raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FibonacciBetting(win_regression=0)
        assert "Win regression must be at least 1" in str(exc_info.value)

    def test_initialization_zero_max_bet_raises(self) -> None:
        """Verify zero max bet raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FibonacciBetting(max_bet=0.0)
        assert "Max bet must be positive" in str(exc_info.value)

    def test_initialization_zero_max_position_raises(self) -> None:
        """Verify zero max_position raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FibonacciBetting(max_position=0)
        assert "Max position must be at least 1" in str(exc_info.value)


class TestFibonacciBettingProgression:
    """Tests for FibonacciBetting progression logic."""

    def test_base_bet_at_start(self) -> None:
        """Verify base bet at start of session."""
        betting = FibonacciBetting(base_unit=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )
        # Position 0: Fibonacci[0] = 1, bet = 5 * 1 = 5
        assert betting.get_bet(context) == 5.0

    def test_advance_after_loss(self) -> None:
        """Verify position advances after loss."""
        betting = FibonacciBetting(base_unit=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Position 0: Fib[0]=1, bet=5
        assert betting.get_bet(context) == 5.0

        betting.record_result(-5.0)  # Position 1: Fib[1]=1, bet=5
        assert betting.get_bet(context) == 5.0

        betting.record_result(-5.0)  # Position 2: Fib[2]=2, bet=10
        assert betting.get_bet(context) == 10.0

        betting.record_result(-10.0)  # Position 3: Fib[3]=3, bet=15
        assert betting.get_bet(context) == 15.0

        betting.record_result(-15.0)  # Position 4: Fib[4]=5, bet=25
        assert betting.get_bet(context) == 25.0

    def test_regress_after_win(self) -> None:
        """Verify position regresses after win."""
        betting = FibonacciBetting(base_unit=5.0, win_regression=2)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Advance to position 4
        for _ in range(4):
            betting.record_result(-5.0)
        assert betting.position == 4

        # Win - regress by 2
        betting.record_result(25.0)
        assert betting.position == 2
        assert betting.get_bet(context) == 10.0  # Fib[2]=2, bet=10

    def test_no_change_on_push(self) -> None:
        """Verify position stays the same on push."""
        betting = FibonacciBetting(base_unit=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        betting.record_result(-5.0)
        betting.record_result(-5.0)
        assert betting.position == 2
        assert betting.get_bet(context) == 10.0

        betting.record_result(0.0)  # Push
        assert betting.position == 2
        assert betting.get_bet(context) == 10.0  # Bet unchanged

    def test_position_floor_at_zero(self) -> None:
        """Verify position doesn't go below 0."""
        betting = FibonacciBetting(base_unit=5.0, win_regression=5)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # At position 0, win with regression 5
        betting.record_result(5.0)
        assert betting.position == 0
        assert betting.get_bet(context) == 5.0

    def test_max_position_cap(self) -> None:
        """Verify position doesn't exceed max_position."""
        betting = FibonacciBetting(base_unit=5.0, max_position=3)
        context = BettingContext(
            bankroll=10000.0,
            starting_bankroll=10000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Advance beyond max
        for _ in range(5):
            betting.record_result(-5.0)

        # Position should be capped at 3
        assert betting.position == 3
        # Fib[3] = 3, bet = 15
        assert betting.get_bet(context) == 15.0

    def test_max_bet_cap(self) -> None:
        """Verify bet doesn't exceed max_bet."""
        betting = FibonacciBetting(base_unit=100.0, max_bet=250.0, max_position=10)
        context = BettingContext(
            bankroll=10000.0,
            starting_bankroll=10000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Position 3: Fib[3]=3, bet=300 -> capped at 250
        for _ in range(3):
            betting.record_result(-100.0)
        assert betting.get_bet(context) == 250.0


class TestFibonacciBettingBankrollLimits:
    """Tests for FibonacciBetting bankroll handling."""

    def test_bet_capped_by_bankroll(self) -> None:
        """Verify bet is capped at available bankroll."""
        betting = FibonacciBetting(base_unit=5.0)

        # Advance position
        for _ in range(4):
            betting.record_result(-5.0)

        context = BettingContext(
            bankroll=20.0,
            starting_bankroll=1000.0,
            session_profit=-980.0,
            last_result=-5.0,
            streak=-4,
            hands_played=4,
        )
        # Position 4: Fib[4]=5, bet=25, but bankroll=20
        assert betting.get_bet(context) == 20.0


class TestFibonacciBettingReset:
    """Tests for FibonacciBetting.reset() method."""

    def test_reset_clears_position(self) -> None:
        """Verify reset clears the position."""
        betting = FibonacciBetting(base_unit=5.0)
        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        for _ in range(4):
            betting.record_result(-5.0)
        assert betting.position == 4

        betting.reset()
        assert betting.position == 0
        assert betting.get_bet(context) == 5.0


class TestFibonacciBettingRepr:
    """Tests for FibonacciBetting string representation."""

    def test_repr(self) -> None:
        """Verify repr of FibonacciBetting."""
        betting = FibonacciBetting(base_unit=5.0, win_regression=2, max_bet=500.0, max_position=10)
        expected = "FibonacciBetting(base_unit=5.0, win_regression=2, max_bet=500.0, max_position=10)"
        assert repr(betting) == expected


class TestFibonacciBettingProtocol:
    """Tests for FibonacciBetting protocol compliance."""

    def test_can_be_used_as_betting_system(self) -> None:
        """Verify FibonacciBetting can be used where BettingSystem is expected."""

        def use_betting_system(system: BettingSystem) -> float:
            context = BettingContext(
                bankroll=100.0,
                starting_bankroll=100.0,
                session_profit=0.0,
                last_result=None,
                streak=0,
                hands_played=0,
            )
            return system.get_bet(context)

        betting = FibonacciBetting(base_unit=10.0)
        result = use_betting_system(betting)
        assert result == 10.0


# =============================================================================
# Integration Tests for Progressive Betting Systems
# =============================================================================


class TestProgressiveBettingIntegration:
    """Integration tests for progressive betting systems."""

    def test_martingale_full_session(self) -> None:
        """Test Martingale through a full session scenario."""
        betting = MartingaleBetting(base_bet=10.0, max_progressions=4, max_bet=100.0)

        # Loss sequence
        context = BettingContext(
            bankroll=500.0,
            starting_bankroll=500.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        assert betting.get_bet(context) == 10.0
        betting.record_result(-10.0)
        assert betting.get_bet(context) == 20.0
        betting.record_result(-20.0)
        assert betting.get_bet(context) == 40.0
        betting.record_result(-40.0)
        assert betting.get_bet(context) == 80.0

        # Win - reset
        betting.record_result(80.0)
        assert betting.get_bet(context) == 10.0

    def test_dalembert_mixed_session(self) -> None:
        """Test D'Alembert through mixed wins/losses."""
        betting = DAlembertBetting(base_bet=25.0, unit=5.0, min_bet=10.0, max_bet=50.0)

        context = BettingContext(
            bankroll=500.0,
            starting_bankroll=500.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Start at 25
        assert betting.get_bet(context) == 25.0

        # Loss -> 30
        betting.record_result(-25.0)
        assert betting.get_bet(context) == 30.0

        # Loss -> 35
        betting.record_result(-30.0)
        assert betting.get_bet(context) == 35.0

        # Win -> 30
        betting.record_result(35.0)
        assert betting.get_bet(context) == 30.0

        # Win -> 25
        betting.record_result(30.0)
        assert betting.get_bet(context) == 25.0

        # Win -> 20
        betting.record_result(25.0)
        assert betting.get_bet(context) == 20.0

        # Win -> 15
        betting.record_result(20.0)
        assert betting.get_bet(context) == 15.0

        # Win -> 10 (min)
        betting.record_result(15.0)
        assert betting.get_bet(context) == 10.0

        # Win -> still 10 (min)
        betting.record_result(10.0)
        assert betting.get_bet(context) == 10.0

    def test_fibonacci_full_sequence(self) -> None:
        """Test Fibonacci through losses and win regression."""
        betting = FibonacciBetting(base_unit=5.0, win_regression=2, max_position=6)

        context = BettingContext(
            bankroll=1000.0,
            starting_bankroll=1000.0,
            session_profit=0.0,
            last_result=None,
            streak=0,
            hands_played=0,
        )

        # Sequence: 1, 1, 2, 3, 5, 8, 13...
        # Position 0: bet = 5*1 = 5
        assert betting.get_bet(context) == 5.0

        # Loss sequence
        betting.record_result(-5.0)  # Position 1: bet = 5
        assert betting.get_bet(context) == 5.0

        betting.record_result(-5.0)  # Position 2: bet = 10
        assert betting.get_bet(context) == 10.0

        betting.record_result(-10.0)  # Position 3: bet = 15
        assert betting.get_bet(context) == 15.0

        betting.record_result(-15.0)  # Position 4: bet = 25
        assert betting.get_bet(context) == 25.0

        betting.record_result(-25.0)  # Position 5: bet = 40
        assert betting.get_bet(context) == 40.0

        # Win - regress by 2 to position 3
        betting.record_result(40.0)
        assert betting.position == 3
        assert betting.get_bet(context) == 15.0
