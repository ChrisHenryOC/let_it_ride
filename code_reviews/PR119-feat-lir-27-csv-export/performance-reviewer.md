# Performance Review: PR #119 - LIR-27 CSV Export

## Summary

The CSV export implementation is functional and well-structured with proper use of `__slots__` on the `CSVExporter` class. However, the **critical issue** is that `export_hands_csv()` requires a complete `list[HandRecord]` in memory, which will exceed the project's 4GB memory target when exporting 10M hands. The function should accept an `Iterable[HandRecord]` to enable streaming/generator-based exports. Secondary concerns include a minor redundant dictionary creation in the write loop.

## Findings by Severity

### Critical

**1. Memory: `export_hands_csv()` requires full list in memory - blocks 10M hand exports**

- **File**: `src/let_it_ride/analytics/export_csv.py`
- **Lines**: 275-307 (function signature at line 275)
- **Impact**: With 10M hands at approximately 400 bytes per HandRecord, the list alone consumes ~4GB, leaving no headroom for the application. This directly violates the `<4GB RAM for 10M hands` requirement.

**Current Code**:
```python
def export_hands_csv(
    hands: list[HandRecord],  # <-- Requires full list in memory
    path: Path,
    ...
) -> None:
```

**Recommendation**: Change the signature to accept `Iterable[HandRecord]` and use a generator pattern:

```python
from collections.abc import Iterable

def export_hands_csv(
    hands: Iterable[HandRecord],  # Accept generator/iterator
    path: Path,
    fields_to_export: list[str] | None = None,
    include_bom: bool = True,
) -> None:
    """Export hand records to CSV file.

    Args:
        hands: Iterable of HandRecord objects (can be generator for memory efficiency).
        ...
    """
    field_names = fields_to_export or HAND_RECORD_FIELDS

    # Validate fields upfront (no change needed)
    invalid_fields = set(field_names) - set(HAND_RECORD_FIELDS)
    if invalid_fields:
        raise ValueError(f"Invalid field names: {invalid_fields}")

    encoding = "utf-8-sig" if include_bom else "utf-8"
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_names, extrasaction="ignore")
        writer.writeheader()

        count = 0
        for hand in hands:  # Iterates without loading all into memory
            writer.writerow(hand.to_dict())
            count += 1

        if count == 0:
            raise ValueError("Cannot export empty hands iterable")
```

**Note**: The empty check must move to post-iteration. Alternatively, use `itertools.chain` with a sentinel or `peekable` pattern if the empty check must be upfront.

---

### High

**2. CSVExporter.export_hands() also requires list - propagates memory issue**

- **File**: `src/let_it_ride/analytics/export_csv.py`
- **Lines**: 390-406 (method signature at line 390)
- **Impact**: The class method signature also requires `list[HandRecord]`, preventing callers from using generators.

**Recommendation**: Update to accept `Iterable[HandRecord]`:

```python
def export_hands(
    self,
    hands: Iterable[HandRecord],  # Changed from list
    fields_to_export: list[str] | None = None,
) -> Path:
```

---

### Medium

**3. Test validates large file with full in-memory read - masks real-world memory issues**

- **File**: `tests/integration/test_export_csv.py`
- **Lines**: 841-872 (test_large_file_handling)
- **Impact**: The test creates 10,000 records (not representative of 10M target) and reads the entire CSV back into memory via `list(reader)`. This does not validate that large exports can complete within memory constraints.

**Current Test**:
```python
def test_large_file_handling(self, tmp_path: Path) -> None:
    # Create 10,000 hand records - still fits in memory easily
    hands = [
        HandRecord(...) for i in range(10000)
    ]
    # ...
    rows = list(reader)  # Reads all back into memory
    assert len(rows) == 10000
```

**Recommendation**:
1. Add a streaming test that uses a generator to create records and verifies file size/line count without reading all into memory
2. Consider a memory profiling test or at minimum a docstring noting that 10K is a reduced test set

---

### Low

**4. Minor: Redundant dict creation in export_sessions_csv loop**

- **File**: `src/let_it_ride/analytics/export_csv.py`
- **Lines**: 246-248
- **Impact**: Each iteration creates a full dictionary even when `fields_to_export` selects a subset. The `extrasaction="ignore"` handles this, but it is slightly wasteful.

**Current Code**:
```python
for result in results:
    row = _session_result_to_dict(result)  # Creates all 11 fields
    writer.writerow(row)  # extrasaction="ignore" filters to selected fields
```

**Recommendation**: This is a minor optimization and may not be worth the code complexity. The overhead is negligible for session-level exports (typically hundreds to thousands of sessions). No action required unless profiling shows it as a hotspot.

---

## Positive Observations

1. **`__slots__` on CSVExporter** (line 319): Good practice for reducing memory overhead on frequently instantiated classes.

2. **HandRecord already has `__slots__`** (frozen dataclass with slots=True): The underlying data structure is memory-efficient.

3. **Use of `csv.DictWriter`**: Proper CSV escaping and quoting is handled by the standard library.

4. **Buffered file I/O**: Python's file operations use buffered I/O by default, which is appropriate for sequential writes.

---

## Performance Impact Assessment

| Issue | Impact on 100K hands/sec | Impact on 10M hand memory |
|-------|--------------------------|---------------------------|
| List-based export_hands_csv | None (I/O bound) | **Blocking** - exceeds 4GB |
| Test coverage gaps | None | None (test-only) |
| Redundant dict creation | Negligible | Negligible |

---

## Recommended Actions

1. **[Critical]** Refactor `export_hands_csv()` to accept `Iterable[HandRecord]` before merging
2. **[High]** Update `CSVExporter.export_hands()` method signature accordingly
3. **[Medium]** Add streaming-aware test or document test limitations
4. **[Low]** No action needed for dict creation optimization

---

## Files Reviewed

- `src/let_it_ride/analytics/export_csv.py` (new file, 351 lines)
- `tests/integration/test_export_csv.py` (new file, 627 lines)
- `src/let_it_ride/analytics/__init__.py` (modified, exports added)
