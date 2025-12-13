# LIR-30: Visualization - Bankroll Trajectory

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/33

## Summary

Implement bankroll trajectory line charts showing N sample session trajectories over time, with color-coded outcomes and reference lines for limits.

## Key Design Decisions

1. **Function Signature**: The issue specifies `bankroll_histories: list[list[float]]` as a separate parameter from `results: list[SessionResult]`. This design keeps history data separate from SessionResult (which doesn't include history), allowing flexibility for callers.

2. **Color Gradient by Outcome**: Using the established color scheme:
   - Green (#2ecc71) for winning sessions
   - Red (#e74c3c) for losing sessions
   - Gray (#95a5a6) for push sessions

3. **Reference Lines**: Win limit and loss limit will be calculated relative to starting bankroll.

## Implementation Tasks

### 1. Create TrajectoryConfig dataclass
- sample_sessions: int = 20
- figsize: tuple[float, float] = (12, 6)
- dpi: int = 150
- show_limits: bool = True
- alpha: float = 0.6
- title: str = "Bankroll Trajectories"
- random_seed: int | None = None (for reproducible sampling)
- xlabel: str = "Hands Played"
- ylabel: str = "Bankroll ($)"

### 2. Implement plot_bankroll_trajectories function
- Validate inputs (non-empty results, matching lengths)
- Sample N sessions if more than sample_sessions available
- Plot each trajectory as a line with outcome-based color
- Add horizontal reference lines (starting bankroll, win limit, loss limit)
- Add legend with session outcomes
- Style consistently with histogram.py

### 3. Implement save_trajectory_chart function
- Similar pattern to save_histogram
- Support PNG and SVG formats
- Auto-create directories
- Handle extension normalization

### 4. Update module exports
- Add to visualizations/__init__.py
- Add to analytics/__init__.py

### 5. Write tests
- Test figure creation and type
- Test empty results error
- Test default and custom config
- Test file saving (PNG/SVG)
- Test directory creation
- Test session sampling
- Test reference lines
- Test color coding by outcome

## Files to Create/Modify

**Create:**
- `src/let_it_ride/analytics/visualizations/trajectory.py`

**Modify:**
- `src/let_it_ride/analytics/visualizations/__init__.py`
- `src/let_it_ride/analytics/__init__.py`
- `tests/integration/test_visualizations.py`
