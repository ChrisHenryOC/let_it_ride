# Let It Ride Strategy Simulator - Configuration Files

This directory contains configuration files for the Let It Ride Strategy Simulator.

## Directory Structure

```
configs/
├── README.md              # This file
├── sample_config.yaml     # Complete reference with all options
├── examples/              # Demo configs for getting started
└── walkaway/              # Walk-away strategy research configs
    ├── with_bonus/        # Strategies using bonus bets
    ├── no_bonus/          # Strategies without bonus bets
    └── betting_systems/   # Alternative betting progressions
```

## Quick Start

Run a simulation with any configuration file:

```bash
poetry run let-it-ride run configs/examples/basic_strategy.yaml
```

Validate a configuration file without running:

```bash
poetry run let-it-ride validate configs/examples/basic_strategy.yaml
```

## Example Configurations

Located in `examples/`:

| File | Description |
|------|-------------|
| `basic_strategy.yaml` | Baseline config using optimal play (basic strategy) |
| `conservative.yaml` | Low-risk approach, pulls bets more often |
| `aggressive.yaml` | High-variance play, rides on drawing hands |
| `bonus_comparison.yaml` | Demonstrates bonus betting with profit-based scaling |
| `progressive_betting.yaml` | Shows Martingale and other betting systems |
| `multi_seat_example.yaml` | Multi-player table simulation (4 seats) |
| `bonus_5_dollar.yaml` | $5 static bonus bet configuration |
| `bonus_15_dollar.yaml` | $15 static bonus bet configuration |
| `bonus_30_dollar.yaml` | $30 static bonus bet configuration |

## Walk-Away Strategy Research

Located in `walkaway/`. See [walkaway/README.md](walkaway/README.md) for details.

These configs were used to research optimal walk-away strategies (win/loss limits). Key findings:
- **Best win rate**: Fibonacci betting + no bonus + $100/$100 limits (36% win rate)
- **Lowest losses**: No bonus + $25/$25 limits (-$1.44 avg loss)

## Reference Configuration

`sample_config.yaml` contains every available option with documentation. Use it as a reference when creating custom configurations.

## Creating Custom Configurations

1. Copy a sample file: `cp configs/examples/basic_strategy.yaml configs/my_strategy.yaml`
2. Edit the configuration
3. Validate: `poetry run let-it-ride validate configs/my_strategy.yaml`
4. Run: `poetry run let-it-ride run configs/my_strategy.yaml`

## Configuration Sections

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

Most options have sensible defaults. A minimal config will use:

- 10,000 sessions of 200 hands each
- $500 starting bankroll with $5 base bet
- Basic strategy, no bonus betting
- Standard paytable
- CSV and JSON output to `./results/`
