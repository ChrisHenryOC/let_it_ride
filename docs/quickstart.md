# Quick Start

Run your first Let It Ride simulation in 5 minutes.

## Prerequisites

Ensure the simulator is installed ([Installation Guide](installation.md)).

## Your First Simulation

### 1. Run a Basic Simulation

```bash
poetry run let-it-ride run configs/examples/basic_strategy.yaml
```

This runs 100,000 sessions using basic (optimal) strategy with default settings.

### 2. Understanding the Output

The simulation displays progress and summary statistics:

```
Running simulation...
Sessions: 100000 | Progress: 100%

=== Simulation Results ===
Sessions Completed: 100,000
Win Rate: 38.2%
Average Profit: -$12.45
Total Hands: 15,234,567
```

Results are saved to the `./results` directory.

### 3. Customizing Parameters

Override settings from command line:

```bash
# Run fewer sessions for testing
poetry run let-it-ride run configs/examples/basic_strategy.yaml --sessions 1000

# Set specific random seed for reproducibility
poetry run let-it-ride run configs/examples/basic_strategy.yaml --seed 42

# Output to custom directory
poetry run let-it-ride run configs/examples/basic_strategy.yaml --output ./my_results

# Quiet mode (minimal output)
poetry run let-it-ride run configs/examples/basic_strategy.yaml --quiet
```

## Sample Configurations

The `configs/` directory contains pre-built configurations:

| File | Description |
|------|-------------|
| `examples/basic_strategy.yaml` | Optimal basic strategy, flat betting |
| `examples/conservative.yaml` | Conservative strategy, lower variance |
| `examples/aggressive.yaml` | Aggressive strategy, higher variance |
| `examples/bonus_comparison.yaml` | Bonus betting strategy comparison |
| `examples/progressive_betting.yaml` | Progressive betting systems |
| `sample_config.yaml` | Full configuration with all options |

## Creating Your Own Configuration

Create a minimal YAML configuration:

```yaml
# my_config.yaml
simulation:
  num_sessions: 10000
  hands_per_session: 200
  random_seed: 42

bankroll:
  starting_amount: 500
  base_bet: 5
  stop_conditions:
    win_limit: 100
    loss_limit: 100

strategy:
  type: basic
```

Run it:

```bash
poetry run let-it-ride run my_config.yaml
```

## Validating Configuration

Check a configuration file for errors:

```bash
poetry run let-it-ride validate my_config.yaml
```

## Viewing Results

After simulation, check the output directory:

```
results/
  simulation_20241215_143022.json   # Full results in JSON
  simulation_20241215_143022.csv    # Session summaries
  simulation_20241215_143022.html   # HTML report (if enabled)
```

## Next Steps

- [Configuration Reference](configuration.md) - All configuration options
- [Strategies](strategies.md) - Strategy guide with basic strategy charts
- [Examples](examples.md) - Common use cases and workflows
