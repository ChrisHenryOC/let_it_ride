# Let It Ride Strategy Simulator - Configuration Files

This directory contains sample configuration files for the Let It Ride Strategy Simulator. Each file demonstrates different strategies, betting systems, and features.

## Quick Start

Run a simulation with any configuration file:

```bash
poetry run let-it-ride run configs/basic_strategy.yaml
```

Validate a configuration file without running:

```bash
poetry run let-it-ride validate configs/basic_strategy.yaml
```

## Configuration Files

### basic_strategy.yaml

**Purpose:** Baseline configuration using mathematically optimal play

- **Strategy:** Basic (optimal pull/ride decisions based on hand strength)
- **Betting:** Flat betting ($5 per circle)
- **Bonus:** Disabled
- **Use case:** Establish a baseline for comparing other strategies

This configuration represents the theoretical best play for Let It Ride. Use it as a reference point when evaluating alternative strategies.

### conservative.yaml

**Purpose:** Low-risk, conservative approach for risk-averse players

- **Strategy:** Conservative (only ride on strong made hands)
- **Betting:** Flat betting with tight stop conditions
- **Bonus:** Disabled
- **Use case:** Minimize variance, protect bankroll

The conservative strategy pulls bets more often, reducing both upside and downside variance. Suitable for players who prioritize session longevity over big wins.

### aggressive.yaml

**Purpose:** High-variance play chasing bigger payouts

- **Strategy:** Aggressive (ride on draws including gutshots)
- **Betting:** Flat betting with wider stop limits
- **Bonus:** Disabled
- **Use case:** Maximize winning potential at the cost of higher variance

The aggressive strategy lets bets ride on drawing hands, accepting more volatility in exchange for higher potential payouts.

### bonus_comparison.yaml

**Purpose:** Demonstrate Three Card Bonus betting strategies

- **Strategy:** Basic (optimal main game decisions)
- **Betting:** Flat betting
- **Bonus:** Bankroll-conditional with profit-based scaling tiers
- **Use case:** Analyze bonus bet impact on session outcomes

This configuration shows how to use conditional bonus betting that increases bet size as session profit grows. Useful for evaluating whether bonus betting is +EV for your bankroll.

### progressive_betting.yaml

**Purpose:** Demonstrate progressive betting systems

- **Strategy:** Basic
- **Betting:** Martingale progression (configurable)
- **Bonus:** Disabled
- **Use case:** Compare betting systems impact on session outcomes

Includes commented examples for multiple betting systems:
- Martingale (double after loss)
- Paroli (increase after win)
- D'Alembert (linear progression)
- Fibonacci sequence

### multi_seat_example.yaml

**Purpose:** Demonstrate multi-seat table simulation

- **Strategy:** Basic
- **Betting:** Flat betting
- **Table:** 4 seats (multi-player simulation)
- **Bonus:** Static $5 bonus bet
- **Use case:** Simulate multiple players at the same table sharing community cards

Multi-seat simulations share community cards among all seats while each seat has independent bankroll tracking. Useful for analyzing how shared cards affect outcomes across multiple players.

### sample_config.yaml

**Purpose:** Reference showing all available configuration options

This file contains every configurable option with extensive comments. Use it as a reference when creating custom configurations.

## Creating Custom Configurations

Start with the closest sample file and modify as needed:

1. Copy a sample file: `cp configs/basic_strategy.yaml configs/my_strategy.yaml`
2. Edit the configuration
3. Validate: `poetry run let-it-ride validate configs/my_strategy.yaml`
4. Run: `poetry run let-it-ride run configs/my_strategy.yaml`

## Configuration Schema Reference

See `sample_config.yaml` for complete documentation of all options, or refer to `docs/let_it_ride_requirements.md` Section 5 for the full specification.

### Key Sections

| Section | Description |
|---------|-------------|
| `metadata` | Optional name, description, version |
| `simulation` | Sessions, hands per session, seed, workers |
| `table` | Multi-seat configuration (num_seats 1-6) |
| `deck` | Shuffle algorithm (fisher_yates, cryptographic) |
| `bankroll` | Starting amount, base bet, stop conditions, betting system |
| `strategy` | Main game strategy (basic, conservative, aggressive, custom) |
| `bonus_strategy` | Three Card Bonus betting (never, always, conditional, etc.) |
| `paytables` | Main game and bonus payout tables |
| `output` | Results directory, formats (CSV, JSON, HTML), visualizations |

## Defaults

Most configuration options have sensible defaults. An empty YAML file is valid and will use:

- 10,000 sessions of 200 hands each
- $500 starting bankroll with $5 base bet
- Basic strategy, no bonus betting
- Standard paytable
- CSV and JSON output to `./results/`
