# LIR-28: JSON Export (GitHub #31)

## Issue Link
https://github.com/ChrisHenryOC/let_it_ride/issues/31

## Summary
Implement JSON export with full configuration preservation, pretty-print and compact options, and round-trip import capability.

## Planned Tasks

1. **Create `src/let_it_ride/analytics/export_json.py`**
   - `ResultsEncoder(json.JSONEncoder)` - custom encoder for dataclasses, enums, datetime, Pydantic models
   - `_session_result_to_dict()` - convert SessionResult to JSON-serializable dict
   - `_aggregate_stats_to_dict()` - convert AggregateStatistics (preserve nested dicts unlike CSV)
   - `export_json()` - main export function with pretty/compact option
   - `load_results_json()` - import JSON back to SimulationResults (round-trip)
   - `JSONExporter` class - orchestrator similar to CSVExporter

2. **Update `src/let_it_ride/analytics/__init__.py`**
   - Export new functions and classes

3. **Create `docs/json_schema.md`**
   - Document JSON structure
   - Include example output

4. **Create `tests/integration/test_export_json.py`**
   - File creation tests
   - Content validation tests
   - Pretty-print vs compact tests
   - Config inclusion/exclusion tests
   - Round-trip tests (export then import)
   - Large data tests
   - Error cases (empty data)

## JSON Structure Design

```json
{
  "metadata": {
    "schema_version": "1.0",
    "generated_at": "2025-01-15T10:30:00Z",
    "simulator_version": "0.1.0"
  },
  "config": { ... },  // optional, included when include_config=True
  "aggregate_statistics": {
    "total_sessions": 1000,
    "winning_sessions": 450,
    // ... all AggregateStatistics fields
    "hand_frequencies": { "royal_flush": 1, "flush": 100, ... },  // nested dict preserved
    "hand_frequency_pct": { ... }
  },
  "session_results": [
    {
      "outcome": "win",
      "stop_reason": "win_limit",
      // ... all SessionResult fields
    }
  ],
  "hands": [  // optional, only when include_hands=True
    {
      "hand_id": 0,
      "session_id": 0,
      // ... all HandRecord fields
    }
  ]
}
```

## Key Implementation Details

1. **Datetime handling**: Use `.isoformat()` for datetime serialization
2. **Enum handling**: Use `.value` attribute for string representation
3. **Pydantic handling**: Use `config.model_dump()` for FullConfig serialization
4. **Exclude internal fields**: `session_profits` tuple from AggregateStatistics (like CSV)
5. **Preserve nested dicts**: Unlike CSV's flattening, keep `hand_frequencies` nested

## API Signatures

```python
def export_json(
    results: SimulationResults,
    path: Path,
    pretty: bool = True,
    include_config: bool = True,
    include_hands: bool = False,
    hands: Iterable[HandRecord] | None = None,
) -> None

def load_results_json(path: Path) -> dict[str, Any]
# Returns dict since we can't fully reconstruct SimulationResults without
# re-instantiating all Pydantic models and dataclasses

class ResultsEncoder(json.JSONEncoder):
    """Custom encoder for simulation data types"""
    def default(self, obj: Any) -> Any

class JSONExporter:
    """Orchestrates JSON export similar to CSVExporter"""
    def export_full(self, results: SimulationResults, ...) -> Path
```
