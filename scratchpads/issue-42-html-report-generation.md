# Issue #42: LIR-39 HTML Report Generation

**GitHub Issue:** https://github.com/chrishenry/let_it_ride/issues/42

## Objective
Implement HTML report generation with embedded Plotly visualizations for simulation results.

## Acceptance Criteria
- [x] Self-contained HTML report (no external dependencies)
- [x] Embedded Plotly charts for interactivity
- [x] Configuration summary section
- [x] Statistics tables with formatting
- [x] Hand frequency comparison (actual vs theoretical)
- [x] Session outcome histogram
- [x] Bankroll trajectory samples
- [x] Template-based generation using Jinja2
- [x] Responsive design (mobile-friendly)
- [x] Integration tests for report generation

## Implementation Tasks
1. [x] Add Jinja2 dependency to pyproject.toml
2. [x] Create `HTMLReportConfig` dataclass
3. [x] Create Jinja2 HTML template (`report.html.j2`)
4. [x] Create CSS styles (embedded in template)
5. [x] Implement `HTMLReportGenerator` class
   - [x] Session outcome histogram (Plotly)
   - [x] Bankroll trajectory samples (Plotly)
   - [x] Hand frequency bar chart (Plotly)
6. [x] Implement `generate_html_report()` function
7. [x] Update `__init__.py` exports
8. [x] Add integration tests

## Files to Create/Modify
- `src/let_it_ride/analytics/export_html.py` (new)
- `src/let_it_ride/analytics/templates/report.html.j2` (new)
- `src/let_it_ride/analytics/__init__.py` (modify - add exports)
- `tests/integration/test_export_html.py` (new)
- `pyproject.toml` (add Jinja2 dependency)

## Key Data Structures

### Input Types
- `SimulationResults` - from `simulation/controller.py`
- `DetailedStatistics` - from `analytics/statistics.py`

### Configuration
```python
@dataclass
class HTMLReportConfig:
    title: str = "Let It Ride Simulation Report"
    include_charts: bool = True
    chart_library: Literal["plotly"] = "plotly"  # Only Plotly for now
    include_config: bool = True
    include_raw_data: bool = False
    trajectory_sample_size: int = 10  # Number of sessions to show in trajectory
```

## Architecture Notes
- Follow existing export patterns from `export_csv.py` and `export_json.py`
- Plotly is already in dev dependencies (`viz` group)
- Use Plotly's `to_html()` with `full_html=False, include_plotlyjs='cdn'` for embedding
- Self-contained option uses `include_plotlyjs=True` for offline viewing
- Template uses Jinja2 for clean separation of HTML structure from Python code
