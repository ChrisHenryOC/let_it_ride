"""Table abstraction for multi-player Let It Ride.

This module provides the Table class that orchestrates multiple player positions
at a single table, dealing from a shared deck with shared community cards.
"""

import random
from dataclasses import dataclass

from let_it_ride.config.models import DealerConfig, TableConfig
from let_it_ride.config.paytables import BonusPaytable, MainGamePaytable
from let_it_ride.core.card import Card
from let_it_ride.core.deck import Deck
from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.hand_processing import process_hand_decisions_and_payouts
from let_it_ride.core.three_card_evaluator import ThreeCardHandRank
from let_it_ride.strategy.base import Decision, Strategy, StrategyContext

# Module-level singleton for default configs to avoid repeated validation overhead
_DEFAULT_DEALER_CONFIG = DealerConfig()
_DEFAULT_TABLE_CONFIG = TableConfig()


@dataclass(frozen=True, slots=True)
class PlayerSeat:
    """Result data for a single player seat in a round.

    Attributes:
        seat_number: The seat position (1-6).
        player_cards: The player's 3 dealt cards.
        decision_bet1: Player's decision on bet 1 (PULL or RIDE).
        decision_bet2: Player's decision on bet 2 (PULL or RIDE).
        final_hand_rank: The evaluated 5-card hand rank.
        base_bet: The bet amount per circle.
        bets_at_risk: Total amount wagered after pull/ride decisions.
        main_payout: Profit from the main game (0 for losing hands).
        bonus_bet: The bonus bet amount (0 if not playing bonus).
        bonus_hand_rank: The 3-card bonus hand rank (None if no bonus bet).
        bonus_payout: Profit from the bonus bet (0 for losing or no bet).
        net_result: Total profit/loss for the hand.
    """

    seat_number: int
    player_cards: tuple[Card, Card, Card]
    decision_bet1: Decision
    decision_bet2: Decision
    final_hand_rank: FiveCardHandRank
    base_bet: float
    bets_at_risk: float
    main_payout: float
    bonus_bet: float
    bonus_hand_rank: ThreeCardHandRank | None
    bonus_payout: float
    net_result: float


@dataclass(frozen=True, slots=True)
class TableRoundResult:
    """Complete result of a single round at the table.

    Attributes:
        round_id: Unique identifier for this round.
        community_cards: The 2 shared community cards.
        dealer_discards: Cards discarded by dealer when dealing community cards
            (None if disabled).
        seat_results: Results for each player seat.
    """

    round_id: int
    community_cards: tuple[Card, Card]
    dealer_discards: tuple[Card, ...] | None
    seat_results: tuple[PlayerSeat, ...]


class Table:
    """Orchestrates multiple player positions at a Let It Ride table.

    The Table manages dealing from a shared deck, shared community cards,
    and tracks results for each player seat. All seats use the same strategy.
    """

    def __init__(
        self,
        deck: Deck,
        strategy: Strategy,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable | None,
        rng: random.Random,
        table_config: TableConfig | None = None,
        dealer_config: DealerConfig | None = None,
    ) -> None:
        """Initialize the table.

        Args:
            deck: The deck to deal from.
            strategy: The strategy for making pull/ride decisions (shared by all seats).
            main_paytable: Paytable for main game payouts.
            bonus_paytable: Paytable for bonus bet payouts (None if no bonus).
            rng: Random number generator for shuffling.
            table_config: Optional table configuration. Defaults to single seat.
            dealer_config: Optional dealer configuration for discard mechanics.
        """
        self._deck = deck
        self._strategy = strategy
        self._main_paytable = main_paytable
        self._bonus_paytable = bonus_paytable
        self._rng = rng
        self._table_config = (
            table_config if table_config is not None else _DEFAULT_TABLE_CONFIG
        )
        self._dealer_config = (
            dealer_config if dealer_config is not None else _DEFAULT_DEALER_CONFIG
        )
        self._last_discarded_cards: list[Card] = []

    def play_round(
        self,
        round_id: int,
        base_bet: float,
        bonus_bet: float = 0.0,
        context: StrategyContext | None = None,
    ) -> TableRoundResult:
        """Play a complete round at the table.

        Args:
            round_id: Unique identifier for this round.
            base_bet: The bet amount per circle (3 circles total).
            bonus_bet: Optional bonus bet amount (same for all seats).
            context: Strategy context for decision making.

        Returns:
            TableRoundResult with complete round details and per-seat results.

        Raises:
            ValueError: If base_bet is not positive or bonus_bet is negative.
            ValueError: If bonus_bet > 0 but no bonus_paytable was configured.
        """
        if base_bet <= 0:
            raise ValueError(f"base_bet must be positive, got {base_bet}")
        if bonus_bet < 0:
            raise ValueError(f"bonus_bet cannot be negative, got {bonus_bet}")
        if bonus_bet > 0 and self._bonus_paytable is None:
            raise ValueError("bonus_bet > 0 requires a bonus_paytable to be configured")

        if context is None:
            context = StrategyContext(
                session_profit=0.0,
                hands_played=0,
                streak=0,
                bankroll=0.0,
            )

        num_seats = self._table_config.num_seats

        # Step 1: Reset and shuffle the deck
        self._deck.reset()
        self._deck.shuffle(self._rng)

        # Step 2: Deal 3 cards to each seat (players receive cards first)
        seat_cards: list[tuple[Card, Card, Card]] = []
        for _ in range(num_seats):
            cards = self._deck.deal(3)
            seat_cards.append((cards[0], cards[1], cards[2]))

        # Step 3: Dealer discard (if enabled)
        # In casino play, the shuffling machine dispenses 3 cards at a time.
        # When dealing the 2 community cards, the dealer receives 3 but discards 1.
        self._last_discarded_cards = []
        if self._dealer_config.discard_enabled:
            self._last_discarded_cards = self._deck.deal(
                self._dealer_config.discard_cards
            )

        # Step 4: Deal 2 community cards
        community = self._deck.deal(2)
        community_tuple: tuple[Card, Card] = (community[0], community[1])

        # Step 5: Process each seat
        seat_results: list[PlayerSeat] = []
        for seat_idx, player_cards in enumerate(seat_cards):
            seat_number = seat_idx + 1
            seat_result = self._process_seat(
                seat_number=seat_number,
                player_cards=player_cards,
                community_cards=community_tuple,
                base_bet=base_bet,
                bonus_bet=bonus_bet,
                context=context,
            )
            seat_results.append(seat_result)

        # Step 6: Return round result
        dealer_discards: tuple[Card, ...] | None = None
        if self._dealer_config.discard_enabled:
            dealer_discards = tuple(self._last_discarded_cards)

        return TableRoundResult(
            round_id=round_id,
            community_cards=community_tuple,
            dealer_discards=dealer_discards,
            seat_results=tuple(seat_results),
        )

    def _process_seat(
        self,
        seat_number: int,
        player_cards: tuple[Card, Card, Card],
        community_cards: tuple[Card, Card],
        base_bet: float,
        bonus_bet: float,
        context: StrategyContext,
    ) -> PlayerSeat:
        """Process a single seat's decisions and payouts.

        Args:
            seat_number: The seat position (1-6).
            player_cards: The player's 3 dealt cards.
            community_cards: The 2 shared community cards.
            base_bet: The bet amount per circle.
            bonus_bet: The bonus bet amount.
            context: Strategy context for decision making.

        Returns:
            PlayerSeat with complete seat results.
        """
        # Process hand decisions and calculate payouts using shared logic
        result = process_hand_decisions_and_payouts(
            player_cards=player_cards,
            community_cards=community_cards,
            strategy=self._strategy,
            main_paytable=self._main_paytable,
            bonus_paytable=self._bonus_paytable,
            base_bet=base_bet,
            bonus_bet=bonus_bet,
            context=context,
        )

        return PlayerSeat(
            seat_number=seat_number,
            player_cards=player_cards,
            decision_bet1=result.decision_bet1,
            decision_bet2=result.decision_bet2,
            final_hand_rank=result.final_hand_rank,
            base_bet=base_bet,
            bets_at_risk=result.bets_at_risk,
            main_payout=result.main_payout,
            bonus_bet=bonus_bet,
            bonus_hand_rank=result.bonus_hand_rank,
            bonus_payout=result.bonus_payout,
            net_result=result.net_result,
        )

    def last_discarded_cards(self) -> tuple[Card, ...]:
        """Return the cards discarded by the dealer in the last round.

        This method provides access to discarded cards for statistical
        validation purposes.

        Returns:
            Tuple of discarded cards from the last round.
            Empty tuple if dealer discard is disabled or no rounds played.
        """
        return tuple(self._last_discarded_cards)
