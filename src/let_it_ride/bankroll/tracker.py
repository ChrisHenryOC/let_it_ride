"""Bankroll tracking for Let It Ride.

This module provides the BankrollTracker class for tracking bankroll balance,
high water mark (peak balance), and drawdown calculations during a session.
"""


class BankrollTracker:
    """Tracks bankroll balance with high water mark and drawdown calculations.

    The tracker maintains:
    - Current balance
    - Peak balance (high water mark)
    - Maximum drawdown (largest peak-to-trough decline)
    - Balance history for visualization (optional, disabled by default)

    Memory considerations:
        History tracking stores one float per hand. For 10M hands, this consumes
        ~80MB. Enable only when visualization features (LIR-30) are needed.
    """

    def __init__(
        self, starting_amount: float, *, track_history: bool = False
    ) -> None:
        """Initialize the bankroll tracker.

        Args:
            starting_amount: The starting bankroll amount.
            track_history: If True, record balance after each transaction.
                Disabled by default for memory efficiency. Enable when
                visualization or detailed analysis is needed.

        Raises:
            ValueError: If starting_amount is negative.
        """
        if starting_amount < 0:
            raise ValueError("Starting amount cannot be negative")

        self._starting: float = starting_amount
        self._balance: float = starting_amount
        self._peak: float = starting_amount
        self._max_drawdown: float = 0.0
        self._peak_at_max_drawdown: float = starting_amount
        self._track_history: bool = track_history
        self._history: list[float] = []

    def apply_result(self, amount: float) -> None:
        """Apply a hand result to the bankroll.

        Args:
            amount: The result amount. Positive for wins, negative for losses.
        """
        self._balance += amount
        if self._track_history:
            self._history.append(self._balance)

        # Update peak if we've reached a new high
        if self._balance > self._peak:
            self._peak = self._balance

        # Calculate current drawdown and update max if needed
        current_dd = self._peak - self._balance
        if current_dd > self._max_drawdown:
            self._max_drawdown = current_dd
            self._peak_at_max_drawdown = self._peak

    @property
    def balance(self) -> float:
        """Return the current bankroll balance."""
        return self._balance

    @property
    def starting_balance(self) -> float:
        """Return the original starting balance."""
        return self._starting

    @property
    def session_profit(self) -> float:
        """Return the session profit (current balance - starting balance)."""
        return self._balance - self._starting

    @property
    def peak_balance(self) -> float:
        """Return the peak balance (high water mark)."""
        return self._peak

    @property
    def max_drawdown(self) -> float:
        """Return the maximum drawdown as an absolute value.

        The maximum drawdown is the largest peak-to-trough decline
        observed during the session.
        """
        return self._max_drawdown

    @property
    def max_drawdown_pct(self) -> float:
        """Return the maximum drawdown as a percentage of the peak.

        Returns:
            The maximum drawdown as a percentage (0-100 scale).
            Returns 0.0 if peak at max drawdown was 0.
        """
        if self._peak_at_max_drawdown == 0:
            return 0.0
        return (self._max_drawdown / self._peak_at_max_drawdown) * 100

    @property
    def current_drawdown(self) -> float:
        """Return the current drawdown from peak.

        Returns:
            The difference between peak and current balance.
            Returns 0.0 if at or above the peak.
        """
        drawdown = self._peak - self._balance
        return max(0.0, drawdown)

    @property
    def history(self) -> list[float]:
        """Return a copy of the balance history.

        The history contains the balance after each transaction.
        Returns an empty list if track_history was False during initialization.

        Returns:
            A copy of the balance history list.
        """
        return self._history.copy()

    @property
    def history_length(self) -> int:
        """Return the number of entries in the history without copying.

        This is more efficient than len(history) when you only need the count.

        Returns:
            The number of balance entries recorded.
        """
        return len(self._history)

    @property
    def is_tracking_history(self) -> bool:
        """Return whether history tracking is enabled."""
        return self._track_history

    def get_recent_history(self, n: int) -> list[float]:
        """Return the most recent n balance entries.

        This is more efficient than history[-n:] for large histories
        as it avoids copying the entire list.

        Args:
            n: Number of recent entries to retrieve. If n exceeds the
               history length, returns all available entries.

        Returns:
            A list of the most recent n balance values.
        """
        if n <= 0:
            return []
        return self._history[-n:]

    def __repr__(self) -> str:
        """Return a string representation of the tracker state."""
        return (
            f"BankrollTracker(balance={self._balance:.2f}, "
            f"peak={self._peak:.2f}, "
            f"max_drawdown={self._max_drawdown:.2f})"
        )
