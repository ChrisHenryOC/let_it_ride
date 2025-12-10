# Issue 30: LIR-27 CSV Export

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/30

## Overview

Implement CSV export for session summaries, aggregate statistics, and per-hand detail records.

## Implementation Plan

1. **Create `export_csv.py`** in `src/let_it_ride/analytics/`:
   - `export_sessions_csv()` - Export list[SessionResult] to CSV
   - `export_aggregate_csv()` - Export AggregateStatistics to CSV (flattened)
   - `export_hands_csv()` - Export list[HandRecord] to CSV (large file support)
   - `CSVExporter` class - Orchestrates all exports with output directory

2. **Key Features**:
   - Configurable field selection (None = all fields)
   - UTF-8 encoding with optional BOM for Excel compatibility
   - Proper CSV escaping and quoting via Python's csv module
   - Large file handling for per-hand exports

3. **Update `__init__.py`** to export new functions/classes

4. **Create integration tests** in `tests/integration/test_export_csv.py`:
   - Test file creation and content validation
   - Test field selection
   - Test BOM option
   - Test large file handling

## Data Types

### SessionResult (11 fields)
- outcome, stop_reason (enums → .value)
- hands_played, starting_bankroll, final_bankroll, session_profit
- total_wagered, total_bonus_wagered
- peak_bankroll, max_drawdown, max_drawdown_pct

### HandRecord (15 fields) - already has to_dict()
- hand_id, session_id, shoe_id, cards_player, cards_community
- decision_bet1, decision_bet2, final_hand_rank
- base_bet, bets_at_risk, main_payout
- bonus_bet, bonus_hand_rank, bonus_payout, bankroll_after

### AggregateStatistics (25+ fields) - needs flattening
- Session metrics: total_sessions, winning_sessions, losing_sessions, push_sessions, session_win_rate
- Hand metrics: total_hands
- Financial metrics: total_wagered, total_won, net_result, expected_value_per_hand
- Main/bonus breakdown: main_wagered, main_won, main_ev_per_hand, bonus_wagered, bonus_won, bonus_ev_per_hand
- Hand distribution: hand_frequencies (dict), hand_frequency_pct (dict) → flatten
- Session profit stats: session_profit_mean, session_profit_std, session_profit_median, session_profit_min, session_profit_max
- session_profits (tuple) → exclude from export (internal)

## Technical Notes

- Use `utf-8-sig` encoding for BOM support
- Use `csv.DictWriter` for field selection
- SessionResult and AggregateStatistics need conversion to dicts
- HandRecord already has `to_dict()` method
