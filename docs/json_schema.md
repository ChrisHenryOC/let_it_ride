# JSON Export Schema

This document describes the JSON schema for exported simulation results.

## Schema Version

Current version: `1.0`

## Top-Level Structure

```json
{
  "metadata": { ... },
  "config": { ... },
  "simulation_timing": { ... },
  "aggregate_statistics": { ... },
  "session_results": [ ... ],
  "hands": [ ... ]
}
```

## Sections

### metadata

Always included. Contains information about the export.

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Version of this JSON schema (e.g., "1.0") |
| `generated_at` | string | ISO 8601 timestamp when file was generated |
| `simulator_version` | string | Version of let-it-ride simulator |

Example:
```json
{
  "schema_version": "1.0",
  "generated_at": "2025-01-15T10:30:00.123456",
  "simulator_version": "0.1.0"
}
```

### config

Optional (controlled by `include_config` parameter). Contains the full simulation configuration as nested objects.

Top-level keys:
- `simulation`: Core parameters (num_sessions, hands_per_session, random_seed, workers)
- `bankroll`: Financial settings (starting_amount, base_bet, stop_conditions, betting_system)
- `strategy`: Main game strategy configuration
- `bonus_strategy`: Bonus betting configuration
- `paytables`: Payout table settings
- `output`: Output format settings

See `configs/sample_config.yaml` for complete structure.

### simulation_timing

Always included. Contains timing information about the simulation run.

| Field | Type | Description |
|-------|------|-------------|
| `start_time` | string | ISO 8601 timestamp when simulation started |
| `end_time` | string | ISO 8601 timestamp when simulation completed |
| `total_hands` | integer | Total hands played across all sessions |

### aggregate_statistics

Always included. Contains aggregate statistics across all sessions.

| Field | Type | Description |
|-------|------|-------------|
| `total_sessions` | integer | Total number of sessions |
| `winning_sessions` | integer | Sessions with positive profit |
| `losing_sessions` | integer | Sessions with negative profit |
| `push_sessions` | integer | Sessions with zero profit |
| `session_win_rate` | float | Fraction of profitable sessions (0.0-1.0) |
| `total_hands` | integer | Total hands played |
| `total_wagered` | float | Total amount wagered |
| `total_won` | float | Total amount won |
| `net_result` | float | Net profit/loss |
| `expected_value_per_hand` | float | Average profit/loss per hand |
| `main_wagered` | float | Main game amount wagered |
| `main_won` | float | Main game amount won |
| `main_ev_per_hand` | float | Main game expected value per hand |
| `bonus_wagered` | float | Bonus amount wagered |
| `bonus_won` | float | Bonus amount won |
| `bonus_ev_per_hand` | float | Bonus expected value per hand |
| `hand_frequencies` | object | Count of each hand rank |
| `hand_frequency_pct` | object | Percentage of each hand rank |
| `session_profit_mean` | float | Mean session profit |
| `session_profit_std` | float | Standard deviation of session profits |
| `session_profit_median` | float | Median session profit |
| `session_profit_min` | float | Minimum session profit |
| `session_profit_max` | float | Maximum session profit |

Example `hand_frequencies`:
```json
{
  "royal_flush": 1,
  "straight_flush": 5,
  "four_of_a_kind": 25,
  "full_house": 150,
  "flush": 300,
  "straight": 400,
  "three_of_a_kind": 500,
  "two_pair": 1200,
  "tens_or_better": 4500,
  "high_card": 2919
}
```

Note: `tens_or_better` represents pairs of tens or higher (the minimum paying hand in Let It Ride). Lower pairs are counted as `high_card` since they don't pay.

### session_results

Always included. Array of session result objects.

| Field | Type | Description |
|-------|------|-------------|
| `outcome` | string | "win", "loss", or "push" |
| `stop_reason` | string | "win_limit", "loss_limit", "max_hands", or "insufficient_funds" |
| `hands_played` | integer | Hands played in session |
| `starting_bankroll` | float | Initial bankroll |
| `final_bankroll` | float | Final bankroll |
| `session_profit` | float | Net profit/loss |
| `total_wagered` | float | Total main game wagers |
| `total_bonus_wagered` | float | Total bonus wagers |
| `peak_bankroll` | float | Highest bankroll during session |
| `max_drawdown` | float | Maximum peak-to-trough decline |
| `max_drawdown_pct` | float | Max drawdown as percentage of peak |

### hands

Optional (controlled by `include_hands` parameter). Array of hand record objects.

| Field | Type | Description |
|-------|------|-------------|
| `hand_id` | integer | Hand identifier within session |
| `session_id` | integer | Parent session identifier |
| `shoe_id` | integer or null | Shoe identifier (null for single-deck) |
| `cards_player` | string | Player's 3 cards (e.g., "Ah Kd Qs") |
| `cards_community` | string | 2 community cards |
| `decision_bet1` | string | "ride" or "pull" |
| `decision_bet2` | string | "ride" or "pull" |
| `final_hand_rank` | string | Hand rank (e.g., "flush") |
| `base_bet` | float | Base bet per circle |
| `bets_at_risk` | float | Total amount wagered |
| `main_payout` | float | Main game payout |
| `bonus_bet` | float | Bonus bet amount |
| `bonus_hand_rank` | string or null | Bonus hand rank |
| `bonus_payout` | float | Bonus payout |
| `bankroll_after` | float | Bankroll after hand |

## Export Options

### Pretty Print (`pretty=True`)

Formats JSON with 2-space indentation for readability. Adds trailing newline.

### Compact (`pretty=False`)

No indentation, suitable for smaller file size and programmatic consumption.

### Include Config (`include_config=True`)

Embeds the full configuration used for the simulation, enabling reproducibility.

### Include Hands (`include_hands=True`)

Includes detailed per-hand records. Use with caution for large simulations as this significantly increases file size.

## Example Usage

```python
from pathlib import Path
from let_it_ride.analytics import export_json, load_json, JSONExporter

# Export with defaults:
#   pretty=True, include_config=True, include_hands=False
export_json(results, Path("results.json"))

# Export compact without config
export_json(results, Path("results.json"), pretty=False, include_config=False)

# Export with hand records
export_json(results, Path("results.json"), include_hands=True, hands=hand_records)

# Load exported JSON
data = load_json(Path("results.json"))
print(data["aggregate_statistics"]["session_win_rate"])

# Using JSONExporter class
exporter = JSONExporter(Path("./output"), prefix="my_sim", pretty=True)
path = exporter.export(results, include_config=True)
```
