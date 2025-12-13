# Test Coverage Review: PR #124 - LIR-28 JSON Export

## Summary

The test suite for the JSON export feature is comprehensive, covering the main functionality, error handling, round-trip serialization, and large dataset handling. However, there are a few notable gaps: the `INSUFFICIENT_FUNDS` stop reason is not tested in session results, generator/iterator handling for the `hands` parameter lacks explicit testing, and the `ResultsEncoder._dataclass_to_dict` method has limited coverage for nested dataclasses containing Pydantic models or other complex types.

## Findings by Severity

### High

#### H1: Missing Test for INSUFFICIENT_FUNDS Stop Reason
**File:** `tests/integration/test_export_json.py`
**Lines:** 586-629 (sample_session_results fixture)

The sample session results fixture only covers three stop reasons: `WIN_LIMIT`, `LOSS_LIMIT`, and `MAX_HANDS`. The fourth stop reason, `INSUFFICIENT_FUNDS`, is not tested in any JSON export scenario.

**Impact:** If the enum serialization for `INSUFFICIENT_FUNDS` behaves differently (unlikely but possible), it would not be caught by tests.

**Recommendation:** Add a session result with `StopReason.INSUFFICIENT_FUNDS` to the test fixture:
```python
SessionResult(
    outcome=SessionOutcome.LOSS,
    stop_reason=StopReason.INSUFFICIENT_FUNDS,
    hands_played=5,
    starting_bankroll=500.0,
    final_bankroll=50.0,
    session_profit=-450.0,
    total_wagered=450.0,
    total_bonus_wagered=0.0,
    peak_bankroll=510.0,
    max_drawdown=460.0,
    max_drawdown_pct=0.90,
),
```

---

### Medium

#### M1: No Test for Generator/Iterator Behavior with `hands` Parameter
**File:** `src/let_it_ride/analytics/export_json.py:388` and `tests/integration/test_export_json.py`

The `export_json` function accepts `hands: Iterable[HandRecord]`, which means it should work with generators (single-pass iterables). However, all tests pass list objects. The implementation converts to a list with `hands_list = [h.to_dict() for h in hands]` (line 434), which would consume a generator. This is correct behavior but should be tested.

**Impact:** If a future refactor changes how hands are processed (e.g., streaming to file), tests would not catch regressions in generator handling.

**Recommendation:** Add a test that passes a generator instead of a list:
```python
def test_include_hands_with_generator(
    self, tmp_path: Path, sample_simulation_results, sample_hand_records
) -> None:
    """Verify hands work when passed as a generator."""
    path = tmp_path / "results.json"
    hand_generator = (h for h in sample_hand_records)  # Generator, not list
    export_json(
        sample_simulation_results,
        path,
        include_hands=True,
        hands=hand_generator,
    )
    data = load_json(path)
    assert len(data["hands"]) == 3
```

---

#### M2: ResultsEncoder Does Not Test Nested Dataclass with Pydantic Model Field
**File:** `tests/integration/test_export_json.py:722-768` (TestResultsEncoder class)

The `ResultsEncoder._dataclass_to_dict` method handles nested dataclasses recursively, but the tests only verify simple dataclasses (HandRecord). If a dataclass contained a Pydantic model field or another dataclass with enum fields, this recursive path is not tested.

**Impact:** Complex nested structures may not serialize correctly.

**Recommendation:** Add a test with a nested dataclass containing an enum:
```python
def test_encodes_dataclass_with_nested_enum(self) -> None:
    """Verify dataclass with enum field is encoded correctly."""
    from let_it_ride.simulation.session import SessionResult, SessionOutcome, StopReason

    result = SessionResult(
        outcome=SessionOutcome.WIN,
        stop_reason=StopReason.WIN_LIMIT,
        hands_played=10,
        starting_bankroll=500.0,
        final_bankroll=600.0,
        session_profit=100.0,
        total_wagered=300.0,
        total_bonus_wagered=0.0,
        peak_bankroll=610.0,
        max_drawdown=10.0,
        max_drawdown_pct=0.02,
    )
    encoded = json.dumps({"result": result}, cls=ResultsEncoder)
    data = json.loads(encoded)
    assert data["result"]["outcome"] == "win"
    assert data["result"]["stop_reason"] == "win_limit"
```

---

### Low

#### L1: No Test for Write Permission Errors
**File:** `src/let_it_ride/analytics/export_json.py:441-444`

The `export_json` function opens files for writing but does not explicitly handle permission errors. While Python will raise `PermissionError`, there is no test verifying this behavior.

**Impact:** Low - standard Python behavior, but explicit testing documents expected behavior.

**Recommendation:** Consider adding a test that attempts to write to a read-only location (platform-dependent, may be skipped on some systems):
```python
@pytest.mark.skipif(os.name == 'nt', reason="Permission handling differs on Windows")
def test_permission_error_raises(self, tmp_path: Path, sample_simulation_results) -> None:
    """Verify PermissionError when writing to read-only location."""
    path = tmp_path / "readonly.json"
    path.touch(mode=0o444)
    with pytest.raises(PermissionError):
        export_json(sample_simulation_results, path)
```

---

#### L2: No Explicit Test for Trailing Newline in Compact Mode
**File:** `tests/integration/test_export_json.py:941-949` (test_compact_format)

The test for compact format verifies no indentation exists but does not verify whether a trailing newline is present or absent in compact mode. The implementation omits the trailing newline for compact output (line 443-444).

**Impact:** Low - behavior is implied but not explicitly verified.

**Recommendation:** Add assertion:
```python
def test_compact_format(self, tmp_path: Path, sample_simulation_results) -> None:
    """Verify pretty=False produces compact output."""
    path = tmp_path / "results.json"
    export_json(sample_simulation_results, path, pretty=False)

    content = path.read_text()
    # Compact has no indentation
    assert "\n  " not in content
    # Compact has no trailing newline
    assert not content.endswith("\n")
```

---

#### L3: JSONExporter Does Not Test include_config=False
**File:** `tests/integration/test_export_json.py:1187-1196` (test_include_config_option)

The test only verifies `include_config=True` via the exporter class. The `include_config=False` path is tested only through the `export_json` function directly, not through the `JSONExporter.export()` method.

**Impact:** Low - the code path is tested elsewhere.

**Recommendation:** Add verification for both cases in the same test:
```python
def test_include_config_option(self, tmp_path: Path, sample_simulation_results) -> None:
    """Verify include_config option works."""
    exporter = JSONExporter(tmp_path)

    # With config
    path_with = exporter.export(sample_simulation_results, include_config=True)
    data_with = load_json(path_with)
    assert "config" in data_with

    # Without config (need different filename)
    exporter2 = JSONExporter(tmp_path, prefix="no_config")
    path_without = exporter2.export(sample_simulation_results, include_config=False)
    data_without = load_json(path_without)
    assert "config" not in data_without
```

---

## Recommendations Summary

| ID | Severity | Effort | Recommendation |
|----|----------|--------|----------------|
| H1 | High | Low | Add `INSUFFICIENT_FUNDS` to test fixture |
| M1 | Medium | Low | Add test for generator input to `hands` parameter |
| M2 | Medium | Low | Add test for dataclass with enum fields via ResultsEncoder |
| L1 | Low | Medium | Add permission error test (platform-specific) |
| L2 | Low | Low | Assert no trailing newline in compact mode |
| L3 | Low | Low | Test `include_config=False` via JSONExporter |

## Test Coverage Assessment

**Current Coverage:** Good - The test suite covers the primary happy paths, error conditions, formatting options, and large data handling.

**Estimated Line Coverage:** ~90% (based on code path analysis)

**Areas Well Covered:**
- File creation and valid JSON output
- Metadata, timing, and aggregate statistics
- Session results serialization with enum handling
- Hand records inclusion/exclusion
- Pretty vs compact formatting
- Round-trip export/load
- Large dataset handling (1000 sessions, 10000 hands)
- Error conditions (missing hands, empty hands)

**Areas Needing Improvement:**
- All StopReason enum variants (only 3 of 4 tested)
- Generator/iterator consumption for hands
- Nested type handling in ResultsEncoder
