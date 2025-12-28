# Walk-Away Strategy Research Configurations

This folder contains 51 configuration files used to research optimal walk-away strategies for Let It Ride.

## Directory Structure

```
walkaway/
├── with_bonus/        # 33 configs using bonus bets
├── no_bonus/          # 15 configs without bonus bets
└── betting_systems/   # 3 alternative betting progression configs
```

## Key Findings

After running 100,000 sessions per configuration:

| Goal | Best Strategy | Win Rate | Avg Loss |
|------|---------------|----------|----------|
| Highest Win Rate | Fibonacci + no bonus + $100/$100 | **36.00%** | -$6.04 |
| Lowest Loss | No bonus + $25/$25 limits | 34.55% | **-$1.44** |
| Most Winning Sessions | Reverse asymmetric $50/$150 | **53.58%** | -$14.57 |

See `results/walkaway/ANALYSIS_SUMMARY.md` for complete analysis.

## Running Simulations

### Run All Walkaway Configs

```bash
for config in configs/walkaway/**/*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done
```

### Run by Category

```bash
# No-bonus configs only
for config in configs/walkaway/no_bonus/*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done

# With-bonus configs only
for config in configs/walkaway/with_bonus/*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done

# Betting system comparison
for config in configs/walkaway/betting_systems/*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done
```

### Run by Bonus Amount

```bash
# $5 bonus configs
for config in configs/walkaway/with_bonus/bonus_5_*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done

# $15 bonus configs
for config in configs/walkaway/with_bonus/bonus_15_*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done

# $30 bonus configs
for config in configs/walkaway/with_bonus/bonus_30_*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done
```

### Run by Strategy Type

```bash
# Very tight limits only ($50/$50, $75/$75)
for config in configs/walkaway/with_bonus/*verytight*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done

# Asymmetric strategies
for config in configs/walkaway/with_bonus/*asym*.yaml; do
  poetry run let-it-ride run "$config" --quiet
done
```

## Configuration Categories

### with_bonus/ (33 files)

Configurations that include bonus betting:

| Pattern | Description | Count |
|---------|-------------|-------|
| `bonus_5_*.yaml` | $5 bonus bet strategies | 11 |
| `bonus_15_*.yaml` | $15 bonus bet strategies | 11 |
| `bonus_30_*.yaml` | $30 bonus bet strategies | 11 |

Strategy variations:
- `*_tight.yaml` - $100/$100 win/loss limits
- `*_protect.yaml` - $150/$100 limits (protect profits)
- `*_chase.yaml` - $400/$150 limits (chase wins)
- `*_loose.yaml` - $500/$400 limits (extended play)
- `*_asym_*.yaml` - Asymmetric limits (2x, 3x, 4x, 5x ratios)
- `*_verytight_*.yaml` - $50/$50 or $75/$75 limits

### no_bonus/ (15 files)

Configurations without bonus betting:

| Pattern | Description |
|---------|-------------|
| `no_bonus_tight_*.yaml` | Standard tight limits |
| `no_bonus_verytight_*.yaml` | Very tight limits ($50, $75) |
| `no_bonus_ultratight_*.yaml` | Ultra tight limits ($25, $30) |
| `no_bonus_short_*.yaml` | Shorter sessions (50/100 hands) |
| `no_bonus_reverse_asym_*.yaml` | Tight win, loose loss limits |
| `bankroll_*.yaml` | Different starting bankrolls |
| `basebet_*.yaml` | Different base bet sizes |
| `multiseat_*.yaml` | Multi-seat table tests |
| `dealer_*.yaml` | Dealer burn card tests |

### betting_systems/ (3 files)

Alternative betting progressions (no bonus):

| File | System |
|------|--------|
| `martingale_nobonus_tight.yaml` | Double after loss |
| `dalembert_nobonus_tight.yaml` | +1 unit after loss |
| `fibonacci_nobonus_tight.yaml` | Fibonacci sequence progression |

## Results

Results are written to `results/walkaway/` with subdirectories matching config names:

```
results/walkaway/
├── ANALYSIS_SUMMARY.md          # Complete analysis
├── with_bonus/bonus_5_tight/    # Results for each config
├── no_bonus/no_bonus_tight_100/
└── ...
```

Each result directory contains:
- `*_aggregate.csv` - Summary statistics
- `*_sessions.csv` - Per-session results
- `*_results.json` - Full results in JSON
