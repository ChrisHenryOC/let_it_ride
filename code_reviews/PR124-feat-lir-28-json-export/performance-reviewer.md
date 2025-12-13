# Performance Review: PR #124 - LIR-28 JSON Export

## Summary

The JSON export implementation is generally well-designed with good use of `__slots__` on the `JSONExporter` class and proper streaming support for hands via `Iterable`. However, there is one **high-severity issue**: when exporting hands, the implementation materializes the entire iterable into a list in memory before writing, which defeats the purpose of accepting an iterable and will cause memory issues with large datasets (10M hands at ~300 bytes each = ~3GB). There are no critical issues that would prevent meeting the throughput target of 100,000 hands/second for the export path.

## Findings by Severity

### Critical

None identified.

### High

#### H1: Memory materialization of hands iterable defeats streaming design

**File:** `src/let_it_ride/analytics/export_json.py`
**Lines:** 434-437 (diff lines 259-262)

**Issue:**
```python
if include_hands:
    if hands is None:
        raise ValueError("include_hands is True but hands is None")
    hands_list = [h.to_dict() for h in hands]  # <-- Full materialization
    if not hands_list:
        raise ValueError("include_hands is True but hands iterable is empty")
    output["hands"] = hands_list
```

The function signature accepts `Iterable[HandRecord]`, suggesting support for generators and streaming, but the implementation immediately materializes the entire iterable into a list via `[h.to_dict() for h in hands]`. For 10M hands:
- Each `HandRecord.to_dict()` creates a new dictionary with ~15 fields (~300 bytes estimated)
- Materializing 10M hands: ~3GB memory just for the hands list
- This exceeds the project's <4GB memory target for 10M hands

**Impact:** Memory exhaustion risk for large simulations; defeats the streaming design established in CSV export.

**Recommendation:** Use streaming JSON encoding with `json.JSONEncoder` and `iterencode()`, or consider JSON Lines format for large datasets. However, since JSON requires the array to be complete before closing, a pragmatic solution is to:

1. For standard JSON output with hands included, document the memory limitation
2. Add a `max_hands` parameter with a reasonable default (e.g., 100,000)
3. Or implement a separate JSON Lines export for large hand datasets

---

### Medium

#### M1: Redundant dictionary creation in `_dataclass_to_dict`

**File:** `src/let_it_ride/analytics/export_json.py`
**Lines:** 298-318 (diff lines 72-92)

**Issue:**
The `_dataclass_to_dict` method in `ResultsEncoder` creates dictionaries that will then be re-processed by `json.JSONEncoder`. The method iterates through fields manually when `dataclasses.asdict()` could be used (though it has its own issues with deep recursion).

More importantly, the `ResultsEncoder.default()` method calls `_dataclass_to_dict()` which returns a dict, but that dict may contain nested dataclasses that won't be further processed by the encoder's `default()` method since the return value is a plain dict.

**Impact:** Minor memory overhead from intermediate dictionaries; potential correctness issue with deeply nested dataclasses.

**Recommendation:** For `HandRecord` objects specifically, the code correctly uses `h.to_dict()` which is efficient. The encoder is primarily used for edge cases. Consider removing unused code paths or documenting expected usage.

---

#### M2: Synchronous file I/O without buffering consideration

**File:** `src/let_it_ride/analytics/export_json.py`
**Lines:** 441-444 (diff lines 215-218)

**Issue:**
```python
with path.open("w", encoding="utf-8") as f:
    json.dump(output, f, cls=ResultsEncoder, indent=indent, ensure_ascii=False)
    if pretty:
        f.write("\n")
```

The code uses default buffering for file writes. For large JSON outputs (especially with pretty printing which can 2-3x the file size), this could result in many small write syscalls.

**Impact:** Suboptimal I/O performance for large exports; not a blocking issue for meeting throughput targets since export is typically a one-time operation post-simulation.

**Recommendation:** Consider explicit buffering for large outputs:
```python
with path.open("w", encoding="utf-8", buffering=65536) as f:
```

---

### Low

#### L1: `datetime.now()` called without timezone in metadata

**File:** `src/let_it_ride/analytics/export_json.py`
**Lines:** 377-378 (diff lines 151-152)

**Issue:**
```python
return {
    "schema_version": JSON_SCHEMA_VERSION,
    "generated_at": datetime.now().isoformat(),
    ...
}
```

Using `datetime.now()` without timezone creates a naive datetime. While not a performance issue, it's noted here as it appears in the same code section.

**Impact:** No performance impact; minor data quality consideration.

---

#### L2: Test creates 10,000 hand records in memory for large data test

**File:** `tests/integration/test_export_json.py`
**Lines:** 1283-1316 (diff lines 722-755)

**Issue:**
```python
def test_large_hand_count(self, tmp_path: Path, sample_simulation_results) -> None:
    """Verify export handles many hand records."""
    num_hands = 10000
    hand_records = [
        HandRecord(...) for i in range(num_hands)
    ]
```

The test creates 10,000 `HandRecord` objects in a list, which is reasonable for testing but doesn't validate the streaming behavior since the production code also materializes to a list.

**Impact:** Test doesn't catch the H1 memory issue; test resource usage is acceptable.

**Recommendation:** Consider a generator-based test to verify streaming support once H1 is addressed.

---

## Positive Observations

1. **Good use of `__slots__`** on `JSONExporter` class (line 483/diff 257) - reduces memory footprint for exporter instances.

2. **Proper use of `Iterable` type hint** - demonstrates intent for streaming support, though implementation needs adjustment.

3. **Efficient session result conversion** - `_session_result_to_dict()` creates minimal dictionaries with explicit field mapping rather than reflection.

4. **Reuse of `EXCLUDED_AGGREGATE_FIELDS`** from CSV module - good code reuse pattern.

5. **UTF-8 encoding with `ensure_ascii=False`** - avoids unnecessary escaping overhead for standard ASCII content.

## Performance Impact on Project Targets

| Target | Status | Notes |
|--------|--------|-------|
| Throughput >= 100,000 hands/sec | Not Affected | Export is post-simulation; does not impact hand processing speed |
| Memory < 4GB for 10M hands | At Risk | H1 could cause 3GB+ memory spike during hands export |

## Recommendations Summary

| ID | Priority | Effort | Impact |
|----|----------|--------|--------|
| H1 | High | Medium | Add streaming support or document memory limitations for hands export |
| M1 | Medium | Low | Clean up encoder or document usage |
| M2 | Medium | Low | Add explicit buffering for large outputs |
| L1 | Low | Low | Use timezone-aware datetime |
| L2 | Low | Low | Add generator-based test once H1 is fixed |
