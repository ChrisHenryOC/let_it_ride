# LIR-32: Console Output Formatting

**GitHub Issue:** https://github.com/chrishenry/let_it_ride/issues/35

## Overview

Implement formatted console output for results summary using Rich library. This includes progress bars with ETA, colorized statistics tables, and hand frequency displays.

## Acceptance Criteria

- [x] Progress bar with ETA during simulation (already exists in cli.py)
- [x] Summary statistics table after completion
- [x] Colorized win/loss indicators (green/red)
- [x] Hand frequency table
- [x] Configuration summary at start
- [x] Elapsed time and throughput display
- [x] Verbosity levels (0=minimal, 1=normal, 2=detailed)
- [x] No-color mode via `use_color=False` (Note: Rich library is still required; true Rich-free fallback was descoped)
- [x] Unit tests for formatters

## Files to Create

- `src/let_it_ride/cli/formatters.py` - Main output formatting module
- `src/let_it_ride/cli/__init__.py` - Package init
- `tests/unit/cli/test_formatters.py` - Unit tests

## Implementation Plan

### 1. Create cli package structure

Create `src/let_it_ride/cli/` directory with:
- `__init__.py` - exports OutputFormatter
- `formatters.py` - OutputFormatter class

### 2. OutputFormatter Class Design

```python
from rich.console import Console
from rich.table import Table

class OutputFormatter:
    """Formats simulation output for console display."""

    def __init__(self, verbosity: int = 1, use_color: bool = True, console: Console | None = None):
        self.verbosity = verbosity
        self.use_color = use_color
        self.console = console or Console(no_color=not use_color)

    def print_config_summary(self, config: FullConfig) -> None:
        """Display configuration summary at start of simulation."""

    def print_statistics(self, stats: AggregateStatistics, duration_secs: float) -> None:
        """Display summary statistics table after completion."""

    def print_hand_frequencies(self, frequencies: dict[str, int]) -> None:
        """Display hand frequency distribution table."""

    def print_session_details(self, results: list[SessionResult]) -> None:
        """Display per-session details (verbose mode only)."""

    def print_completion(self, total_hands: int, duration_secs: float) -> None:
        """Display completion message with throughput stats."""

    def print_exported_files(self, paths: list[Path]) -> None:
        """Display list of exported files."""
```

### 3. Table Designs

**Configuration Summary Table:**
- Simulation settings (sessions, hands, seed)
- Bankroll settings (starting amount, base bet, betting system)
- Strategy settings (type)

**Statistics Summary Table:**
- Session outcomes (winning, losing, push, win rate)
- Financial summary (wagered, won, net result)
- Expected value per hand

**Hand Frequency Table:**
- Columns: Hand Rank | Count | Percentage
- Sorted by hand strength (Royal Flush to No Pair)

### 4. Verbosity Levels

- **0 (minimal):** Only essential completion message
- **1 (normal):** Config summary, results summary, exported files
- **2 (detailed):** Add per-session details, hand distribution, profit distribution

### 5. Color Scheme

- Green: Wins, positive profits
- Red: Losses, negative profits
- Yellow: Breakeven/push
- Bold: Headers and key metrics

### 6. Progress Bar (Already Implemented)

The existing progress bar in cli.py is adequate. The issue mentions ProgressTracker class but since Rich's Progress is already integrated, we'll focus on the formatters.

## Integration Points

The OutputFormatter will be used in `cli.py`:
1. After loading config: `formatter.print_config_summary(cfg)`
2. After simulation: `formatter.print_statistics(stats, duration_secs)`
3. In verbose mode: `formatter.print_session_details(results.session_results)`
4. After export: `formatter.print_exported_files(exported_files)`

## Dependencies

- rich (already in pyproject.toml as ^13.0)
- Imports: AggregateStatistics, SessionResult, FullConfig

## Test Strategy

1. Test each formatting method produces valid output
2. Test verbosity filtering
3. Test color/no-color modes
4. Test with edge cases (empty data, all wins, all losses)
