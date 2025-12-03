"""Unit tests for betting systems."""

import pytest

from let_it_ride.bankroll.betting_systems import (
    BettingContext,
    BettingSystem,
    FlatBetting,
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
