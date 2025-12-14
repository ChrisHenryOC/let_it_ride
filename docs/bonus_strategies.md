# Bonus Betting Strategies

This guide covers Three Card Bonus side bet strategies.

## Overview

The Three Card Bonus is an optional side bet evaluated on the player's initial 3 cards only. It pays independently of the main game and has a house edge of approximately 2.4-3.5% depending on the paytable.

## Bonus Paytables

### Paytable B (Default)

| Hand | Payout | House Edge |
|------|--------|------------|
| Mini Royal (AKQ suited) | 100:1 | ~3.5% |
| Straight Flush | 40:1 | |
| Three of a Kind | 30:1 | |
| Straight | 5:1 | |
| Flush | 4:1 | |
| Pair | 1:1 | |

### Paytable A (Lower Volatility)

| Hand | Payout | House Edge |
|------|--------|------------|
| Mini Royal | 50:1 | ~2.4% |
| Straight Flush | 40:1 | |
| Three of a Kind | 30:1 | |
| Straight | 6:1 | |
| Flush | 3:1 | |
| Pair | 1:1 | |

### Three Card Hand Probabilities

| Hand | Combinations | Probability |
|------|--------------|-------------|
| Mini Royal | 4 | 0.018% |
| Straight Flush | 44 | 0.199% |
| Three of a Kind | 52 | 0.235% |
| Straight | 720 | 3.26% |
| Flush | 1,096 | 4.96% |
| Pair | 3,744 | 16.94% |
| High Card | 16,440 | 74.39% |

## Strategy Types

### Never Bet Bonus

Baseline strategy - never place the bonus bet.

```yaml
bonus_strategy:
  enabled: false
  type: "never"
```

### Always Bet Bonus

Fixed bonus bet on every hand.

```yaml
bonus_strategy:
  enabled: true
  type: "always"
  always:
    amount: 1.00
```

### Static Betting

Constant bonus bet amount or ratio of base bet.

```yaml
bonus_strategy:
  enabled: true
  type: "static"
  static:
    amount: 1.00    # Fixed amount
    # OR
    ratio: 0.2      # 20% of base bet
```

### Bankroll Conditional

Bet bonus only when profitable, with optional scaling.

```yaml
bonus_strategy:
  enabled: true
  type: "bankroll_conditional"
  bankroll_conditional:
    base_amount: 1.00
    min_session_profit: 25.00  # Only bet when ahead $25+
    max_drawdown: 0.25         # Stop if 25% down from peak
    scaling:
      enabled: true
      tiers:
        - min_profit: 25
          max_profit: 75
          bet_amount: 1.00
        - min_profit: 75
          max_profit: 150
          bet_amount: 2.00
        - min_profit: 150
          max_profit: null     # No upper limit
          bet_amount: 5.00
```

**Use case:** Protect session profits by only risking bonus bets when ahead.

### Streak-Based Betting

Adjust bonus bets based on win/loss streaks.

```yaml
bonus_strategy:
  enabled: true
  type: "streak_based"
  streak_based:
    base_amount: 1.00
    trigger: "bonus_loss"      # Event type to track
    streak_length: 3           # Consecutive events to trigger
    action:
      type: "multiply"         # multiply, increase, decrease, stop, start
      value: 2.0               # Multiplier or amount
    reset_on: "bonus_win"      # Event that resets streak
    max_multiplier: 8.0        # Cap on multiplier
```

**Trigger types:**
- `main_loss` / `main_win` - Main game results
- `bonus_loss` / `bonus_win` - Bonus bet results
- `any_loss` / `any_win` - Either game

**Action types:**
- `multiply` - Multiply base_amount by value
- `increase` - Add value to current bet
- `decrease` - Subtract value from current bet
- `stop` - Stop bonus betting
- `start` - Resume bonus betting

### Configuration Examples

#### Conservative: Bonus Only When Winning

```yaml
bonus_strategy:
  enabled: true
  type: "bankroll_conditional"
  bankroll_conditional:
    base_amount: 1.00
    min_session_profit: 50.00
    max_drawdown: 0.20
```

#### Aggressive: Chase Bonus Losses

```yaml
bonus_strategy:
  enabled: true
  type: "streak_based"
  streak_based:
    base_amount: 2.00
    trigger: "bonus_loss"
    streak_length: 2
    action:
      type: "multiply"
      value: 2.0
    reset_on: "bonus_win"
    max_multiplier: 8.0
```

#### Profit-Based Scaling

```yaml
bonus_strategy:
  enabled: true
  type: "bankroll_conditional"
  bankroll_conditional:
    base_amount: 1.00
    min_session_profit: 0.00
    scaling:
      enabled: true
      tiers:
        - min_profit: 0
          max_profit: 50
          bet_amount: 1.00
        - min_profit: 50
          max_profit: 100
          bet_amount: 3.00
        - min_profit: 100
          max_profit: null
          bet_amount: 5.00
```

## Bonus Bet Limits

Configure table limits for bonus bets:

```yaml
bonus_strategy:
  limits:
    min_bet: 1.00
    max_bet: 25.00
    increment: 1.00  # Bets rounded to this
```

## Research Questions

The simulator can help answer:

1. **EV Impact:** What is the true cost per hand of bonus betting?
2. **Session Win Rate:** Can strategic bonus betting improve session outcomes?
3. **Optimal Timing:** When is bonus betting most/least costly?
4. **Variance Effect:** How does bonus betting affect session variance?

## Strategy Comparison

To compare bonus strategies:

```bash
# No bonus betting
poetry run let-it-ride run configs/basic_strategy.yaml --output ./results/no_bonus

# Always bet bonus
poetry run let-it-ride run configs/bonus_always.yaml --output ./results/bonus_always

# Conditional bonus
poetry run let-it-ride run configs/bonus_conditional.yaml --output ./results/bonus_conditional
```

Compare:
- Overall session win rate
- Bonus contribution to profits/losses
- Variance differences
- Distribution of outcomes

## Choosing a Strategy

| Goal | Strategy |
|------|----------|
| Minimize losses | Never |
| Simple fixed approach | Static |
| Protect profits | Bankroll Conditional |
| Chase variance | Streak-Based |
| Research optimal approach | Compare multiple |

## Next Steps

- [Strategies](strategies.md) - Main game strategies
- [Configuration Reference](configuration.md) - All configuration options
- [Examples](examples.md) - Bonus betting workflows
