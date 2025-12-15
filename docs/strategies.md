# Main Game Strategies

This guide covers the pull/ride decision strategies for the main Let It Ride game.

## Strategy Types

| Strategy | Description | House Edge | Variance |
|----------|-------------|------------|----------|
| Basic | Mathematically optimal | ~3.5% | Medium |
| Always Ride | Never pull bets | Higher | Very High |
| Always Pull | Always pull bets 1 & 2 | Higher | Low |
| Conservative | Only ride made hands | Higher | Low |
| Aggressive | Ride on more draws | Higher | High |
| Custom | User-defined rules | Varies | Varies |

## Basic Strategy (Recommended)

Basic strategy minimizes the house edge by making mathematically optimal pull/ride decisions.

### Bet 1 Decision (3 Cards Visible)

**LET IT RIDE** with:

| Hand Type | Examples |
|-----------|----------|
| Any paying hand | Pair of 10s+, Three of a Kind |
| Three to Royal Flush | 10-J-K suited, J-Q-A suited |
| Three suited in sequence | 5-6-7 suited, 8-9-10 suited |
| Three to straight flush, spread 4, one high card | 5-7-8 suited with 10+ |
| Three to straight flush, spread 5, two high cards | 5-7-9 suited with two 10+ |

**PULL** on all other hands.

### Bet 2 Decision (4 Cards Visible)

**LET IT RIDE** with:

| Hand Type | Examples |
|-----------|----------|
| Any paying hand | Pair of 10s+, Two Pair, etc. |
| Four to a flush | Four cards same suit |
| Four to outside straight, one high card | 5-6-7-8 with 10+ |
| Four to inside straight, four high cards | 10-J-Q-K |

**PULL** on all other hands.

### Configuration

```yaml
strategy:
  type: "basic"
```

## Baseline Strategies

### Always Ride

Never pull any bets. Maximum variance, higher house edge.

```yaml
strategy:
  type: "always_ride"
```

**Use case:** Testing maximum variance scenarios.

### Always Pull

Always pull bets 1 and 2. Minimum variance (only bet 3 in play).

```yaml
strategy:
  type: "always_pull"
```

**Use case:** Baseline comparison, minimum risk per hand.

## Conservative Strategy

Only let it ride with made paying hands. Ignores draws entirely.

```yaml
strategy:
  type: "conservative"
  conservative:
    made_hands_only: true
    min_strength_bet1: 7  # Three of a kind or better
    min_strength_bet2: 5  # Two pair or better
```

**Hand strength scale:**
1. Any pair
2. Pair of 10s+
3. Two pair
4. Three of a kind
5. Straight
6. Flush
7. Full house
8. Four of a kind
9. Straight flush
10. Royal flush

**Use case:** Lower variance at cost of higher house edge.

## Aggressive Strategy

Let it ride on more draw situations, including gutshots and backdoor flushes.

```yaml
strategy:
  type: "aggressive"
  aggressive:
    ride_on_draws: true
    include_gutshots: true
    include_backdoor_flush: true
```

**Use case:** Higher variance strategy for hitting big hands.

## Custom Strategy

Define your own rules using conditions and actions.

### Basic Custom Strategy

```yaml
strategy:
  type: "custom"
  custom:
    bet1_rules:
      - condition: "has_paying_hand"
        action: "ride"
      - condition: "is_royal_draw"
        action: "ride"
      - condition: "default"
        action: "pull"

    bet2_rules:
      - condition: "has_paying_hand"
        action: "ride"
      - condition: "is_flush_draw"
        action: "ride"
      - condition: "default"
        action: "pull"
```

### Available Conditions

**Hand State:**
- `has_paying_hand` - Hand qualifies for payout
- `has_pair` - Any pair present
- `has_high_pair` - Pair of 10s or better
- `has_trips` - Three of a kind

**Draw Conditions:**
- `is_flush_draw` - Four to flush (bet 2) or three suited (bet 1)
- `is_straight_draw` - Four to any straight
- `is_open_straight_draw` - Open-ended straight draw
- `is_inside_straight_draw` - Gutshot straight draw
- `is_straight_flush_draw` - Drawing to straight flush
- `is_royal_draw` - Drawing to royal flush

**Hand Composition:**
- `high_cards >= N` - Count of 10, J, Q, K, A
- `suited_cards >= N` - Max cards of same suit
- `connected_cards >= N` - Max sequential cards
- `gaps <= N` - Gaps in straight draws

**Session Context:**
- `session_profit > N` - Current profit/loss
- `hands_played > N` - Hands this session
- `streak > N` - Current win/loss streak

### Complex Custom Strategy Example

```yaml
strategy:
  type: "custom"
  custom:
    bet1_rules:
      # Always ride with paying hands
      - condition: "has_paying_hand"
        action: "ride"

      # Ride on royal flush draws
      - condition: "is_royal_draw and suited_high_cards >= 3"
        action: "ride"

      # Ride on strong straight flush draws
      - condition: "is_straight_flush_draw and gaps <= 1"
        action: "ride"

      # Ride on flush draws with high cards
      - condition: "is_flush_draw and high_cards >= 2"
        action: "ride"

      # Default to pull
      - condition: "default"
        action: "pull"

    bet2_rules:
      - condition: "has_paying_hand"
        action: "ride"
      - condition: "is_flush_draw"
        action: "ride"
      - condition: "is_open_straight_draw and high_cards >= 1"
        action: "ride"
      - condition: "default"
        action: "pull"
```

## Strategy Comparison

To compare strategies, run simulations with different configurations and compare results:

```bash
# Run basic strategy
poetry run let-it-ride run configs/basic_strategy.yaml --output ./results/basic

# Run conservative strategy
poetry run let-it-ride run configs/conservative.yaml --output ./results/conservative

# Run aggressive strategy
poetry run let-it-ride run configs/aggressive.yaml --output ./results/aggressive
```

Compare session win rates, average profits, and variance across strategies.

## Choosing a Strategy

| Goal | Recommended Strategy |
|------|---------------------|
| Minimize house edge | Basic |
| Minimize variance | Conservative or Always Pull |
| Maximize big hand frequency | Aggressive |
| Test specific theories | Custom |
| Baseline comparison | Always Ride / Always Pull |

## Next Steps

- [Bonus Strategies](bonus_strategies.md) - Three Card Bonus betting
- [Configuration Reference](configuration.md) - All configuration options
- [Examples](examples.md) - Strategy comparison workflows
