"""Game engine orchestration for Let It Ride.

This module provides the main game engine that coordinates dealing,
strategy decisions, and payout calculation for a single hand.
"""

import random
from dataclasses import dataclass

from let_it_ride.config.models import DealerConfig
from let_it_ride.config.paytables import BonusPaytable, MainGamePaytable
from let_it_ride.core.card import Card
from let_it_ride.core.deck import Deck
from let_it_ride.core.hand_evaluator import FiveCardHandRank
from let_it_ride.core.hand_processing import process_hand_decisions_and_payouts
from let_it_ride.core.three_card_evaluator import ThreeCardHandRank
from let_it_ride.strategy.base import Decision, Strategy, StrategyContext

# Module-level singleton for default dealer config to avoid Pydantic validation
# overhead on each GameEngine instantiation when dealer_config is not provided.
_DEFAULT_DEALER_CONFIG = DealerConfig()


@dataclass(frozen=True, slots=True)
class GameHandResult:
    """Complete result of a single Let It Ride hand.

    Attributes:
        hand_id: Unique identifier for this hand within the session.
        player_cards: The player's 3 dealt cards.
        community_cards: The 2 community cards.
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

    hand_id: int
    player_cards: tuple[Card, Card, Card]
    community_cards: tuple[Card, Card]
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


class GameEngine:
    """Orchestrates a single Let It Ride hand.

    The game engine coordinates the deck, strategy, and paytables to play
    a complete hand from dealing through payout calculation.
    """

    def __init__(
        self,
        deck: Deck,
        strategy: Strategy,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable | None,
        rng: random.Random,
        dealer_config: DealerConfig | None = None,
    ) -> None:
        """Initialize the game engine.

        Args:
            deck: The deck to deal from.
            strategy: The strategy for making pull/ride decisions.
            main_paytable: Paytable for main game payouts.
            bonus_paytable: Paytable for bonus bet payouts (None if no bonus).
            rng: Random number generator for shuffling.
            dealer_config: Optional dealer configuration for discard mechanics.
        """
        self._deck = deck
        self._strategy = strategy
        self._main_paytable = main_paytable
        self._bonus_paytable = bonus_paytable
        self._rng = rng
        self._dealer_config = (
            dealer_config if dealer_config is not None else _DEFAULT_DEALER_CONFIG
        )
        self._last_discarded_cards: list[Card] = []

    def play_hand(
        self,
        hand_id: int,
        base_bet: float,
        bonus_bet: float = 0.0,
        context: StrategyContext | None = None,
    ) -> GameHandResult:
        """Play a complete Let It Ride hand.

        Args:
            hand_id: Unique identifier for this hand.
            base_bet: The bet amount per circle (3 circles total).
            bonus_bet: Optional bonus bet amount.
            context: Strategy context for decision making.

        Returns:
            GameHandResult with complete hand details and payouts.

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

        # Step 1: Reset and shuffle the deck
        self._deck.reset()
        self._deck.shuffle(self._rng)

        # Step 2: Deal 3 cards to player (player receives cards first)
        player_cards = self._deck.deal(3)

        # Step 3: Dealer discard (if enabled)
        # In casino play, the shuffling machine dispenses 3 cards at a time.
        # When dealing the 2 community cards, the dealer receives 3 but discards 1.
        self._last_discarded_cards = []
        if self._dealer_config.discard_enabled:
            self._last_discarded_cards = self._deck.deal(
                self._dealer_config.discard_cards
            )

        # Step 4: Deal 2 community cards
        community_cards = self._deck.deal(2)

        player_tuple: tuple[Card, Card, Card] = (
            player_cards[0],
            player_cards[1],
            player_cards[2],
        )
        community_tuple: tuple[Card, Card] = (community_cards[0], community_cards[1])

        # Step 5: Process hand decisions and calculate payouts
        result = process_hand_decisions_and_payouts(
            player_cards=player_tuple,
            community_cards=community_tuple,
            strategy=self._strategy,
            main_paytable=self._main_paytable,
            bonus_paytable=self._bonus_paytable,
            base_bet=base_bet,
            bonus_bet=bonus_bet,
            context=context,
        )

        return GameHandResult(
            hand_id=hand_id,
            player_cards=player_tuple,
            community_cards=community_tuple,
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
        """Return the cards discarded by the dealer in the last hand.

        This method provides access to discarded cards for statistical
        validation purposes.

        Returns:
            Tuple of discarded cards from the last hand.
            Empty tuple if dealer discard is disabled or no hands played.
        """
        return tuple(self._last_discarded_cards)
