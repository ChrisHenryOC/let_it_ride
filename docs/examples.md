# Examples and Workflows

Common use cases and example configurations.

## Strategy Comparison

Compare basic, conservative, and aggressive strategies:

### Configuration Files

Create three configs varying only the strategy:

```yaml
# basic_comparison.yaml
simulation:
  num_sessions: 100000
  hands_per_session: 200
  random_seed: 42

bankroll:
  starting_amount: 500
  base_bet: 5
  stop_conditions:
    win_limit: 100
    loss_limit: 200

strategy:
  type: basic
```

```yaml
# conservative_comparison.yaml
# (same settings, different strategy)
strategy:
  type: conservative
```

```yaml
# aggressive_comparison.yaml
strategy:
  type: aggressive
```

### Running Comparison

```bash
# Run each strategy
poetry run let-it-ride run basic_comparison.yaml --output ./results/basic
poetry run let-it-ride run conservative_comparison.yaml --output ./results/conservative
poetry run let-it-ride run aggressive_comparison.yaml --output ./results/aggressive

# Compare results
```

## Bonus Betting Analysis

### Test: Bonus Only When Ahead

```yaml
# bonus_when_ahead.yaml
simulation:
  num_sessions: 100000
  hands_per_session: 200
  random_seed: 42

bankroll:
  starting_amount: 500
  base_bet: 5
  stop_conditions:
    win_limit: 150
    loss_limit: 200

strategy:
  type: basic

bonus_strategy:
  enabled: true
  paytable: paytable_b
  type: bankroll_conditional
  bankroll_conditional:
    base_amount: 1.00
    min_session_profit: 50.00
    max_drawdown: 0.25
```

### Test: Scaled Bonus Betting

```yaml
# bonus_scaled.yaml
bonus_strategy:
  enabled: true
  type: bankroll_conditional
  bankroll_conditional:
    base_amount: 1.00
    min_session_profit: 25.00
    scaling:
      enabled: true
      tiers:
        - min_profit: 25
          max_profit: 75
          bet_amount: 1.00
        - min_profit: 75
          max_profit: 150
          bet_amount: 3.00
        - min_profit: 150
          max_profit: null
          bet_amount: 5.00
```

## Bankroll Management Studies

### Stop Limit Comparison

Test different win/loss limits:

```yaml
# tight_limits.yaml
bankroll:
  starting_amount: 500
  base_bet: 5
  stop_conditions:
    win_limit: 50
    loss_limit: 50
```

```yaml
# wide_limits.yaml
bankroll:
  starting_amount: 500
  base_bet: 5
  stop_conditions:
    win_limit: 200
    loss_limit: 200
```

```yaml
# asymmetric_limits.yaml
bankroll:
  starting_amount: 500
  base_bet: 5
  stop_conditions:
    win_limit: 100
    loss_limit: 300  # More loss tolerance
```

### Betting System Comparison

```yaml
# flat_betting.yaml
bankroll:
  betting_system:
    type: flat

# martingale.yaml
bankroll:
  betting_system:
    type: martingale
    martingale:
      loss_multiplier: 2.0
      max_bet: 100.00
      max_progressions: 4

# paroli.yaml
bankroll:
  betting_system:
    type: paroli
    paroli:
      win_multiplier: 2.0
      wins_before_reset: 3
      max_bet: 100.00
```

## Multi-Player Table Analysis

### Chair Position Study

```yaml
# multi_seat.yaml
simulation:
  num_sessions: 100000
  hands_per_session: 200
  random_seed: 42

table:
  num_seats: 6
  track_seat_positions: true

dealer:
  discard_enabled: true
  discard_cards: 3

bankroll:
  starting_amount: 500
  base_bet: 5
  stop_conditions:
    win_limit: 100
    loss_limit: 200

strategy:
  type: basic
```

### Analyzing Seat Results

```python
import json

with open("results/multi_seat.json") as f:
    results = json.load(f)

# Compare win rates by seat position
for seat in results["seat_statistics"]:
    print(f"Seat {seat['position']}: {seat['win_rate']:.1%}")
```

## Custom Strategy Development

### Progressive Ride Strategy

Ride more aggressively when ahead:

```yaml
# progressive_ride.yaml
strategy:
  type: custom
  custom:
    bet1_rules:
      - condition: "has_paying_hand"
        action: "ride"
      - condition: "is_royal_draw"
        action: "ride"
      # More aggressive when profitable
      - condition: "session_profit > 50 and is_flush_draw"
        action: "ride"
      - condition: "session_profit > 50 and is_straight_draw"
        action: "ride"
      - condition: "default"
        action: "pull"

    bet2_rules:
      - condition: "has_paying_hand"
        action: "ride"
      - condition: "is_flush_draw"
        action: "ride"
      - condition: "session_profit > 50 and is_inside_straight_draw"
        action: "ride"
      - condition: "default"
        action: "pull"
```

### Conservative When Losing

Pull more when behind:

```yaml
# conservative_when_losing.yaml
strategy:
  type: custom
  custom:
    bet1_rules:
      - condition: "has_paying_hand"
        action: "ride"
      # When losing, only ride on strong hands
      - condition: "session_profit < -50"
        action: "pull"
      - condition: "is_royal_draw"
        action: "ride"
      - condition: "is_straight_flush_draw and gaps <= 1"
        action: "ride"
      - condition: "default"
        action: "pull"

    bet2_rules:
      - condition: "has_paying_hand"
        action: "ride"
      - condition: "session_profit < -50"
        action: "pull"
      - condition: "is_flush_draw"
        action: "ride"
      - condition: "default"
        action: "pull"
```

## Large-Scale Simulation

### 10 Million Sessions

```yaml
# large_scale.yaml
simulation:
  num_sessions: 10000000
  hands_per_session: 200
  workers: auto  # Use all CPU cores
  progress_interval: 100000

bankroll:
  starting_amount: 500
  base_bet: 5
  stop_conditions:
    win_limit: 100
    loss_limit: 200

strategy:
  type: basic

output:
  formats:
    csv:
      include_hands: false      # Don't output per-hand (too large)
      include_sessions: false   # Don't output per-session (too large)
      include_aggregate: true   # Just aggregate stats
    json:
      enabled: true
```

Run with quiet mode:

```bash
poetry run let-it-ride run large_scale.yaml --quiet
```

## Quick A/B Test

Test a hypothesis with minimal setup:

```bash
# Test A: Standard config
poetry run let-it-ride run configs/examples/basic_strategy.yaml --sessions 50000 --seed 42 --output ./test_a

# Test B: Modified config
poetry run let-it-ride run modified.yaml --sessions 50000 --seed 42 --output ./test_b

# Compare JSON results
python -c "
import json
with open('./test_a/simulation.json') as f: a = json.load(f)
with open('./test_b/simulation.json') as f: b = json.load(f)
print(f'A win rate: {a[\"summary\"][\"session_win_rate\"]:.1%}')
print(f'B win rate: {b[\"summary\"][\"session_win_rate\"]:.1%}')
"
```

## Reproducible Research

### Setting Seeds

For reproducible results:

```yaml
simulation:
  random_seed: 42  # Fixed seed

deck:
  shuffle_algorithm: fisher_yates  # Deterministic shuffle
  use_crypto: false  # Don't use cryptographic entropy
```

### Validating RNG

```yaml
deck:
  validate_rng_quality: true  # Run chi-square and runs tests
```

## Next Steps

- [Configuration Reference](configuration.md) - All available options
- [Strategies Guide](strategies.md) - Strategy details
- [API Documentation](api.md) - Programmatic usage
