# API Documentation

Use the simulator as a Python library for custom analysis and integration.

## Installation

```bash
pip install -e .
# or
poetry install
```

## Quick Start

```python
from let_it_ride.core import Card, Deck, Rank, Suit, evaluate_five_card_hand
from let_it_ride.strategy import BasicStrategy
from let_it_ride.simulation import Session, SessionConfig

# Create a session
config = SessionConfig(
    starting_bankroll=500.0,
    base_bet=5.0,
    win_limit=100.0,
    loss_limit=100.0,
    max_hands=200,
)
strategy = BasicStrategy()
session = Session(config, strategy)

# Run the session
result = session.run()
print(f"Result: ${result.net_profit:.2f}")
```

## Core Module

### Card, Rank, Suit

```python
from let_it_ride.core import Card, Rank, Suit

# Create cards
ace_spades = Card(Rank.ACE, Suit.SPADES)
ten_hearts = Card(Rank.TEN, Suit.HEARTS)

# Parse from string
card = Card.from_string("As")  # Ace of spades
card = Card.from_string("Th")  # Ten of hearts

# Card properties
print(card.rank)  # Rank.TEN
print(card.suit)  # Suit.HEARTS
print(card.is_high_card)  # True (10, J, Q, K, A)
```

### Deck

```python
from let_it_ride.core import Deck

deck = Deck()
deck.shuffle()

# Deal cards
cards = deck.deal(5)

# Check remaining
print(deck.cards_remaining)

# Reset for new hand
deck.reset()
deck.shuffle()
```

### Hand Evaluation

```python
from let_it_ride.core import (
    evaluate_five_card_hand,
    evaluate_three_card_hand,
    FiveCardHandRank,
    ThreeCardHandRank,
)

# Five-card hand
cards = [Card.from_string(s) for s in ["As", "Ks", "Qs", "Js", "Ts"]]
result = evaluate_five_card_hand(cards)
print(result.rank)      # FiveCardHandRank.ROYAL_FLUSH
print(result.high_cards)  # [ACE, KING, QUEEN, JACK, TEN]

# Three-card hand (for bonus)
three_cards = cards[:3]
result = evaluate_three_card_hand(three_cards)
print(result)  # ThreeCardHandRank.MINI_ROYAL
```

### Hand Analysis

```python
from let_it_ride.core import analyze_three_cards, analyze_four_cards

# Analyze 3 cards (Bet 1 decision)
analysis = analyze_three_cards(cards[:3])
print(analysis.is_paying_hand)
print(analysis.is_flush_draw)
print(analysis.is_straight_draw)
print(analysis.high_card_count)

# Analyze 4 cards (Bet 2 decision)
analysis = analyze_four_cards(cards[:4])
print(analysis.is_four_to_flush)
print(analysis.is_outside_straight_draw)
```

## Strategy Module

### Built-in Strategies

```python
from let_it_ride.strategy import (
    BasicStrategy,
    AlwaysRideStrategy,
    AlwaysPullStrategy,
    conservative_strategy,
    aggressive_strategy,
)

# Create strategies
basic = BasicStrategy()
always_ride = AlwaysRideStrategy()
always_pull = AlwaysPullStrategy()
conservative = conservative_strategy()
aggressive = aggressive_strategy()
```

### Strategy Interface

```python
from let_it_ride.strategy import Strategy, StrategyContext, Decision

# All strategies implement this interface
class Strategy:
    def decide_bet1(self, context: StrategyContext) -> Decision:
        """Decide whether to ride or pull Bet 1."""
        ...

    def decide_bet2(self, context: StrategyContext) -> Decision:
        """Decide whether to ride or pull Bet 2."""
        ...

# Context provides hand information
context = StrategyContext(
    player_cards=[...],
    community_cards=[...],
    analysis=hand_analysis,
)

decision = strategy.decide_bet1(context)
print(decision)  # Decision.RIDE or Decision.PULL
```

### Bonus Strategies

```python
from let_it_ride.strategy import (
    NeverBonusStrategy,
    AlwaysBonusStrategy,
    StaticBonusStrategy,
    BankrollConditionalBonusStrategy,
    StreakBasedBonusStrategy,
    BonusContext,
)

# Never bet bonus
bonus_strategy = NeverBonusStrategy()

# Always bet fixed amount
bonus_strategy = AlwaysBonusStrategy(amount=1.0)

# Static amount or ratio
bonus_strategy = StaticBonusStrategy(amount=1.0)
bonus_strategy = StaticBonusStrategy(ratio=0.2, base_bet=5.0)

# Bankroll conditional
bonus_strategy = BankrollConditionalBonusStrategy(
    base_amount=1.0,
    min_session_profit=25.0,
    max_drawdown_ratio=0.25,
)

# Get bonus bet
context = BonusContext(
    session_profit=50.0,
    bankroll=550.0,
    starting_bankroll=500.0,
)
bet = bonus_strategy.get_bonus_bet(context)
```

## Simulation Module

### Session

```python
from let_it_ride.simulation import Session, SessionConfig, SessionResult

config = SessionConfig(
    starting_bankroll=500.0,
    base_bet=5.0,
    win_limit=100.0,
    loss_limit=100.0,
    max_hands=200,
    stop_on_insufficient_funds=True,
)

session = Session(config, strategy)
result: SessionResult = session.run()

# Result properties
print(result.net_profit)
print(result.hands_played)
print(result.stop_reason)
print(result.outcome)  # SessionOutcome.WIN, LOSS, or PUSH
print(result.peak_bankroll)
print(result.max_drawdown)
```

### Table Session (Multi-Player)

```python
from let_it_ride.simulation import TableSession, TableSessionConfig

config = TableSessionConfig(
    num_seats=6,
    starting_bankroll=500.0,
    base_bet=5.0,
    win_limit=100.0,
    loss_limit=100.0,
    max_hands=200,
)

table_session = TableSession(config, strategy)
result = table_session.run()

# Per-seat results
for seat_result in result.seat_results:
    print(f"Seat {seat_result.seat_position}: ${seat_result.net_profit:.2f}")
```

### Simulation Controller

```python
from let_it_ride.simulation import SimulationController, SimulationResults
from let_it_ride.config import load_config

# Load configuration
config = load_config("configs/basic_strategy.yaml")

# Create controller
controller = SimulationController(config)

# Run simulation
results: SimulationResults = controller.run()

print(f"Sessions: {results.total_sessions}")
print(f"Win rate: {results.win_rate:.1%}")
print(f"Total hands: {results.total_hands}")
```

### RNG Management

```python
from let_it_ride.simulation import RNGManager, validate_rng_quality

# Create RNG with specific seed
rng = RNGManager(seed=42)

# Use cryptographic entropy (non-reproducible)
rng = RNGManager(use_crypto=True)

# Validate RNG quality
result = validate_rng_quality(rng, num_samples=100000)
print(f"Chi-square p-value: {result.chi_square_p_value:.4f}")
print(f"Runs test p-value: {result.runs_test_p_value:.4f}")
print(f"Passed: {result.passed}")
```

## Bankroll Module

### Betting Systems

```python
from let_it_ride.bankroll import (
    FlatBetting,
    MartingaleBetting,
    ReverseMartingaleBetting,
    ParoliBetting,
    DAlembertBetting,
    FibonacciBetting,
    ProportionalBetting,
)

# Flat betting
betting = FlatBetting(base_bet=5.0)

# Martingale
betting = MartingaleBetting(
    base_bet=5.0,
    loss_multiplier=2.0,
    max_bet=500.0,
)

# Get next bet
bet = betting.get_bet(bankroll=500.0)

# Record result
betting.record_result(won=False, profit=-15.0)
```

## Configuration Module

### Loading Configuration

```python
from let_it_ride.config import load_config, SimulationConfig

# Load from YAML file
config: SimulationConfig = load_config("configs/basic_strategy.yaml")

# Access configuration values
print(config.simulation.num_sessions)
print(config.bankroll.starting_amount)
print(config.strategy.type)
```

## Complete Example

```python
"""Run a custom simulation programmatically."""
from let_it_ride.core import Deck
from let_it_ride.strategy import BasicStrategy, BankrollConditionalBonusStrategy
from let_it_ride.simulation import Session, SessionConfig

# Configure session
config = SessionConfig(
    starting_bankroll=500.0,
    base_bet=5.0,
    win_limit=150.0,
    loss_limit=200.0,
    max_hands=200,
)

# Set up strategies
strategy = BasicStrategy()
bonus_strategy = BankrollConditionalBonusStrategy(
    base_amount=1.0,
    min_session_profit=25.0,
)

# Run multiple sessions
wins = 0
total_profit = 0.0

for i in range(1000):
    session = Session(config, strategy, bonus_strategy=bonus_strategy, seed=i)
    result = session.run()

    if result.net_profit > 0:
        wins += 1
    total_profit += result.net_profit

print(f"Win rate: {wins/1000:.1%}")
print(f"Average profit: ${total_profit/1000:.2f}")
```

## Error Handling

```python
from let_it_ride.core import DeckEmptyError
from let_it_ride.core.hand_state import InvalidPhaseError
from let_it_ride.strategy import ConditionParseError, InvalidFieldError

try:
    deck = Deck()
    deck.deal(100)  # More than 52 cards
except DeckEmptyError:
    print("Deck is empty")

try:
    # Invalid custom strategy condition
    strategy = CustomStrategy(rules={"invalid": "condition"})
except ConditionParseError as e:
    print(f"Invalid condition: {e}")
```

## Next Steps

- [Examples](examples.md) - More usage examples
- [Configuration Reference](configuration.md) - YAML configuration options
- [Strategies Guide](strategies.md) - Strategy details
