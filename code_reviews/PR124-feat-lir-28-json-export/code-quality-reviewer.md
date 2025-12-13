# Code Quality Review: PR #124 - LIR-28 JSON Export

## Summary

This PR implements JSON export functionality for simulation results with good overall structure and consistency with the existing CSV export module. The implementation follows established patterns in the codebase, provides comprehensive test coverage, and includes well-documented schema. There are a few medium-priority issues around code duplication, potential memory concerns with large hand exports, and minor API design considerations.

---

## Findings by Severity

### Critical

No critical issues found.

---

### High

No high severity issues found.

---

### Medium

#### M1: Duplicated `_session_result_to_dict` function across CSV and JSON modules

**File:** `src/let_it_ride/analytics/export_json.py:321-344`

The `_session_result_to_dict` function is nearly identical to the one in `export_csv.py` (lines 67-90). This violates the DRY (Don't Repeat Yourself) principle and creates maintenance risk - if `SessionResult` fields change, both files must be updated.

**Recommendation:** Extract the shared conversion logic to a common utility module (e.g., `src/let_it_ride/analytics/converters.py`) or add a `to_dict()` method directly to `SessionResult` (similar to how `HandRecord` already has one).

```python
# Option 1: Add to SessionResult dataclass
def to_dict(self) -> dict[str, Any]:
    return {
        "outcome": self.outcome.value,
        "stop_reason": self.stop_reason.value,
        ...
    }
```

---

#### M2: Hands iterable consumed without memory consideration for streaming

**File:** `src/let_it_ride/analytics/export_json.py:434`

The code converts the entire hands iterable to a list via `[h.to_dict() for h in hands]` before writing. For simulations with millions of hands (which is the stated use case per CLAUDE.md), this could consume significant memory.

While JSON inherently cannot be streamed like CSV, the current approach loads all hand data into memory twice (once as HandRecord objects, once as dicts) before writing.

**Recommendation:** Consider documenting this memory implication clearly in the docstring, or for very large exports, consider JSON Lines format (`.jsonl`) as an alternative streaming-friendly format for the hands section.

```python
# Add to docstring:
"""
Note:
    When include_hands=True with large hand counts, all hand data is
    loaded into memory before writing. For simulations exceeding 1M hands,
    consider using CSV export for hand data or exporting in batches.
"""
```

---

#### M3: Timestamp uses local time without timezone information

**File:** `src/let_it_ride/analytics/export_json.py:377`

The `_build_metadata()` function uses `datetime.now().isoformat()` which produces a timestamp without timezone information. This can cause confusion when JSON files are shared across time zones or systems.

**Recommendation:** Use timezone-aware timestamps:

```python
from datetime import datetime, timezone

def _build_metadata() -> dict[str, Any]:
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "simulator_version": __version__,
    }
```

---

### Low

#### L1: Redundant dataclass encoding in ResultsEncoder

**File:** `src/let_it_ride/analytics/export_json.py:298-318`

The `_dataclass_to_dict` method duplicates type checking logic that already exists in the `default` method. When encountering nested dataclasses, it recursively calls `_dataclass_to_dict` but handles datetime/enum inline rather than delegating to the encoder's own `default` method.

This isn't incorrect, but the duplication means changes to type handling must be made in two places.

**Recommendation:** Consider using `dataclasses.asdict()` with a custom dict_factory, or restructure to avoid duplication:

```python
def _dataclass_to_dict(self, obj: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in fields(obj):
        value = getattr(obj, field.name)
        # Let default() handle type conversion
        try:
            json.dumps(value)  # Check if JSON-serializable
            result[field.name] = value
        except TypeError:
            result[field.name] = self.default(value)
    return result
```

---

#### L2: Import inside function body

**File:** `src/let_it_ride/analytics/export_json.py:403`

The `aggregate_results` function is imported inside `export_json()`. While this avoids circular imports, it's repeated in the test file as well and adds a small performance overhead on every call.

**Recommendation:** This is acceptable for avoiding circular imports, but document why this pattern is necessary with a comment:

```python
# Import here to avoid circular dependency with simulation.aggregation
from let_it_ride.simulation.aggregation import aggregate_results
```

---

#### L3: Test file creates fixtures with hardcoded values that could drift from actual models

**File:** `tests/integration/test_export_json.py:586-627`

The test fixtures manually construct `SessionResult` and `HandRecord` objects with hardcoded field values. If the dataclass fields change, tests may become stale or misleading.

**Recommendation:** Consider using factory functions or pytest-factoryboy to maintain test fixtures, or add a comment noting which version/commit of the dataclasses these fixtures correspond to.

---

#### L4: Empty hands list check could use more efficient pattern

**File:** `src/let_it_ride/analytics/export_json.py:434-436`

The code converts the entire iterable to a list, then checks if empty. For generators, this consumes the entire iterator just to check emptiness.

```python
hands_list = [h.to_dict() for h in hands]
if not hands_list:
    raise ValueError("include_hands is True but hands iterable is empty")
```

**Recommendation:** If supporting generators is important, consider a peek pattern:

```python
hands_iter = iter(hands)
try:
    first = next(hands_iter)
except StopIteration:
    raise ValueError("include_hands is True but hands iterable is empty")
hands_list = [first.to_dict()] + [h.to_dict() for h in hands_iter]
```

However, since the API already accepts `Iterable` which includes lists, the current approach may be acceptable for typical use cases.

---

## Positive Observations

1. **Consistent with existing patterns:** The `JSONExporter` class mirrors the `CSVExporter` class structure, making the codebase cohesive and predictable.

2. **Good use of `__slots__`:** The `JSONExporter` class uses `__slots__` for memory efficiency, consistent with project conventions.

3. **Comprehensive test coverage:** The test suite covers happy paths, error cases, round-trip verification, large data handling, and unicode support.

4. **Well-documented schema:** The `docs/json_schema.md` file provides clear documentation of the JSON output format with examples.

5. **Proper type hints:** All functions have type annotations as required by project standards.

6. **Schema versioning:** Including `schema_version` in metadata is excellent for forward compatibility.

7. **Proper file encoding:** Using `encoding="utf-8"` and `ensure_ascii=False` for international character support.

---

## Recommendations Summary (Prioritized by Impact)

| ID | Priority | Recommendation |
|----|----------|----------------|
| M1 | Medium | Extract shared `_session_result_to_dict` to avoid duplication |
| M2 | Medium | Document memory implications for large hand exports |
| M3 | Medium | Use timezone-aware timestamps in metadata |
| L1 | Low | Consider simplifying dataclass encoding logic |
| L2 | Low | Add comment explaining import placement |
| L3 | Low | Consider test fixture maintenance strategy |
| L4 | Low | Optimize empty check for generator inputs |

---

## Inline Comments for PR

```
INLINE_COMMENT:
- file: src/let_it_ride/analytics/export_json.py
- position: 119
- comment: **M1:** This function duplicates `_session_result_to_dict` from `export_csv.py`. Consider extracting to a shared utility or adding `to_dict()` method to `SessionResult` (like `HandRecord` already has).

INLINE_COMMENT:
- file: src/let_it_ride/analytics/export_json.py
- position: 151
- comment: **M3:** Consider using `datetime.now(timezone.utc).isoformat()` for timezone-aware timestamps. Local time without timezone info can cause confusion when files are shared across systems.

INLINE_COMMENT:
- file: src/let_it_ride/analytics/export_json.py
- position: 208
- comment: **M2:** For large simulations (millions of hands per project targets), this list comprehension loads all hand data into memory. Consider documenting memory implications in the docstring.
```
