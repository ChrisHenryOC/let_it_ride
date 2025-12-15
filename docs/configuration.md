# Configuration Reference

Simulations are configured via YAML files. This document covers all available options.

## File Structure

```yaml
metadata:        # Optional descriptive info
simulation:      # Core simulation parameters
deck:            # Deck and shuffle settings
table:           # Multi-player table settings
dealer:          # Dealer card handling
bankroll:        # Bankroll and betting
strategy:        # Main game strategy
bonus_strategy:  # Three Card Bonus betting
paytables:       # Payout configurations
output:          # Results and reporting
```

## Metadata Section (Optional)

```yaml
metadata:
  name: "My Simulation"           # Descriptive name for this configuration
  description: "Testing basic strategy with conservative limits"
  author: "Your Name"             # Who created this config
  version: "1.0"                  # Config version tracking
```

The metadata section is purely informational and does not affect simulation behavior. It's useful for documenting and organizing configuration files.

## Simulation Section

```yaml
simulation:
  # Number of sessions to run (1 - 100,000,000)
  num_sessions: 100000

  # Maximum hands per session (1 - 10,000)
  hands_per_session: 200

  # Random seed for reproducibility (null for true randomness)
  random_seed: 42

  # Parallel workers: "auto" (all cores) or integer
  workers: "auto"

  # Progress reporting interval
  progress_interval: 10000

  # Detailed per-hand logging (creates large output)
  detailed_logging: false
```

## Deck Section

```yaml
deck:
  # Shuffle algorithm
  # - "fisher_yates": Fast, standard shuffling (default)
  shuffle_algorithm: "fisher_yates"
```

**Note:** RNG settings like `use_crypto` are configured via the `RNGManager` class when using the API directly, not through the deck configuration.

## Table Section

```yaml
table:
  # Number of seats (1-6 players sharing community cards)
  num_seats: 1

  # Track results by seat position
  track_seat_positions: true
```

## Dealer Section

```yaml
dealer:
  # Enable dealer card discard (simulates casino shuffling machines)
  discard_enabled: false

  # Cards to discard before community cards (when enabled)
  discard_cards: 3
```

## Bankroll Section

```yaml
bankroll:
  # Starting bankroll in dollars
  starting_amount: 500.00

  # Base bet per circle (total initial = base_bet * 3)
  base_bet: 5.00

  # Stop conditions (first triggered ends session)
  stop_conditions:
    win_limit: 250.00        # Stop at profit
    loss_limit: 200.00       # Stop at loss
    max_hands: 200           # Max hands per session
    max_duration_minutes: null  # Time limit (null = none)
    stop_on_insufficient_funds: true

  # Betting progression system
  betting_system:
    type: "flat"  # flat, proportional, martingale, etc.
```

### Betting System Types

#### Flat Betting
```yaml
betting_system:
  type: "flat"
  # Uses base_bet always, no additional config needed
```

#### Proportional Betting
```yaml
betting_system:
  type: "proportional"
  proportional:
    bankroll_percentage: 0.03  # 3% of bankroll
    min_bet: 5.00
    max_bet: 100.00
    round_to: 1.00
```

#### Martingale
```yaml
betting_system:
  type: "martingale"
  martingale:
    loss_multiplier: 2.0
    reset_on_win: true
    max_bet: 500.00
    max_progressions: 6
```

#### Reverse Martingale
```yaml
betting_system:
  type: "reverse_martingale"
  reverse_martingale:
    win_multiplier: 2.0
    reset_on_loss: true
    profit_target_streak: 3
    max_bet: 500.00
```

#### Paroli
```yaml
betting_system:
  type: "paroli"
  paroli:
    win_multiplier: 2.0
    wins_before_reset: 3
    max_bet: 500.00
```

#### D'Alembert
```yaml
betting_system:
  type: "dalembert"
  dalembert:
    unit: 5.00
    decrease_unit: 5.00
    min_bet: 5.00
    max_bet: 500.00
```

#### Fibonacci
```yaml
betting_system:
  type: "fibonacci"
  fibonacci:
    unit: 5.00
    win_regression: 2
    max_bet: 500.00
    max_position: 10
```

## Strategy Section

```yaml
strategy:
  type: "basic"  # basic, always_ride, always_pull, conservative, aggressive, custom
```

See [Strategies Guide](strategies.md) for detailed strategy configuration.

## Bonus Strategy Section

```yaml
bonus_strategy:
  enabled: false
  paytable: "paytable_b"  # paytable_a, paytable_b, paytable_c, custom
  limits:
    min_bet: 1.00
    max_bet: 25.00
    increment: 1.00
  type: "never"  # never, always, static, bankroll_conditional, streak_based
```

See [Bonus Strategies Guide](bonus_strategies.md) for detailed configuration.

## Paytables Section

```yaml
paytables:
  main_game:
    type: "standard"  # standard, liberal, tight, custom

  bonus:
    type: "paytable_b"  # paytable_a, paytable_b, paytable_c, custom
```

### Standard Main Game Paytable

| Hand | Payout |
|------|--------|
| Royal Flush | 1000:1 |
| Straight Flush | 200:1 |
| Four of a Kind | 50:1 |
| Full House | 11:1 |
| Flush | 8:1 |
| Straight | 5:1 |
| Three of a Kind | 3:1 |
| Two Pair | 2:1 |
| Pair of 10s+ | 1:1 |

### Bonus Paytable B (Default)

| Hand | Payout |
|------|--------|
| Mini Royal (AKQ suited) | 100:1 |
| Straight Flush | 40:1 |
| Three of a Kind | 30:1 |
| Straight | 5:1 |
| Flush | 4:1 |
| Pair | 1:1 |

## Output Section

```yaml
output:
  directory: "./results"
  prefix: "simulation"
  timestamp_format: "%Y%m%d_%H%M%S"

  formats:
    csv:
      enabled: true
      include_hands: false     # Per-hand details
      include_sessions: true   # Session summaries
      include_aggregate: true  # Overall stats

    json:
      enabled: true
      pretty: true
      include_config: true

    html:
      enabled: false
      include_charts: true
      chart_library: "plotly"  # plotly or matplotlib

  visualizations:
    enabled: true
    charts:
      - type: "session_outcomes_histogram"
        title: "Distribution of Session Outcomes"
      - type: "bankroll_trajectory"
        title: "Sample Bankroll Trajectories"
        sample_sessions: 100
    format: "png"  # png, svg, html
    dpi: 150

  console:
    progress_bar: true
    verbosity: 1  # 0-3
    show_summary: true
```

## Complete Example

See `configs/sample_config.yaml` for a fully-documented configuration file with all options.

## Command Line Overrides

Many settings can be overridden via command line:

```bash
poetry run let-it-ride run config.yaml \
  --sessions 50000 \
  --seed 123 \
  --output ./custom_results \
  --quiet
```

## Next Steps

- [Strategies Guide](strategies.md) - Main game strategy configuration
- [Bonus Strategies](bonus_strategies.md) - Bonus betting configuration
- [Output Formats](output_formats.md) - Understanding output files
