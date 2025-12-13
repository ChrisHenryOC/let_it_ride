# LIR-29: Visualization - Session Outcome Histogram

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/32

## Overview

Implement histogram visualization for session outcomes using matplotlib.

## Tasks

1. Create `src/let_it_ride/analytics/visualizations/__init__.py` - Package initialization
2. Create `src/let_it_ride/analytics/visualizations/histogram.py` - Main implementation
3. Create `tests/integration/test_visualizations.py` - Integration tests
4. Update `src/let_it_ride/analytics/__init__.py` - Export new functions

## Key Types

```python
@dataclass
class HistogramConfig:
    bins: int | str = "auto"
    figsize: tuple[float, float] = (10, 6)
    dpi: int = 150
    show_mean: bool = True
    show_median: bool = True
    show_zero_line: bool = True
    title: str = "Session Outcome Distribution"

def plot_session_histogram(
    results: list[SessionResult],
    config: HistogramConfig = HistogramConfig(),
) -> matplotlib.figure.Figure

def save_histogram(
    results: list[SessionResult],
    path: Path,
    format: Literal["png", "svg"] = "png",
    config: HistogramConfig = HistogramConfig(),
) -> None
```

## Implementation Details

### Data Source
- Use `SessionResult.session_profit` for histogram data
- Calculate win rate from `SessionOutcome.WIN` count

### Visualization Features
- Color bins: green for profit (>0), red for loss (<0)
- Vertical line markers for mean (dashed blue) and median (dashed orange)
- Zero line (break-even) as solid black vertical line
- Win rate annotation in upper right corner
- Title and axis labels (Profit/Loss, Frequency)

### Integration Points
- SessionResult from `simulation/session.py`
- VisualizationsConfig from `config/models.py` (already has `session_outcomes_histogram` type)
- statistics module for mean/median calculations

## Dependencies
- matplotlib ^3.8 (already in pyproject.toml viz group)
- numpy (for histogram calculations)
