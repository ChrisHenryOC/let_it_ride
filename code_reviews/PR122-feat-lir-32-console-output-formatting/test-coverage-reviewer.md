# Test Coverage Review

## Summary

PR #122 introduces the `OutputFormatter` class for Rich-based console output formatting. The test coverage is generally good, with tests for all public methods at multiple verbosity levels. However, there are several notable gaps: no tests for `print_config_summary` method (only tested with mock in diff version), missing edge case tests for zero-value statistics, no tests verifying actual no-color output in rendered console, and the SessionResult fixture in the diff uses outdated constructor parameters that don't match the current dataclass definition.

## Findings

### Critical

1. **SessionResult fixture uses incorrect constructor in diff**
   - File: `tests/unit/cli/test_formatters.py` (diff lines 1117-1142)
   - The diff shows `SessionResult` being constructed with `session_id` and `hand_results` parameters, but the actual `SessionResult` dataclass (in `src/let_it_ride/simulation/session.py:136-163`) uses `outcome`, `stop_reason`, `total_bonus_wagered`, `peak_bankroll`, `max_drawdown`, and `max_drawdown_pct` instead.
   - The current test file (on disk) correctly uses the proper constructor, so this appears to be fixed between diff and final version.

### High

1. **Missing test for `print_config_summary` with actual FullConfig**
   - File: `tests/unit/cli/test_formatters.py`
   - The diff version (lines 941-998) uses `MagicMock` for config objects. The current file correctly uses fixtures with proper `AggregateStatistics` but there is no test for `print_config_summary` at all in the current test file.
   - Impact: The `print_config_summary` method is untested with real configuration objects, missing validation of output format and content.
   - Recommendation: Add a fixture for `FullConfig` or use `MagicMock` with proper attribute structure and add tests for config summary output.

2. **Missing test for zero-session edge case in `print_statistics`**
   - File: `src/let_it_ride/cli/formatters.py:199-208`
   - The code handles `stats.total_sessions > 0` for calculating loss_rate and push_rate, but no test validates behavior when total_sessions is 0.
   - Impact: Potential division by zero not tested.
   - Recommendation: Add test with `total_sessions=0` to verify safe handling.

3. **Missing test for frequencies with zero total count**
   - File: `src/let_it_ride/cli/formatters.py:306-308`
   - The code has a check `if total == 0: return` but this path is not explicitly tested. The empty frequencies test (`{}`) tests a different early return path.
   - Impact: Edge case not validated.
   - Recommendation: Add test with frequencies like `{"high_card": 0, "pair": 0}` where sum is 0.

### Medium

1. **No test for unknown hand rank in hand frequencies**
   - File: `src/let_it_ride/cli/formatters.py:320`
   - The code uses `HAND_RANK_DISPLAY.get(rank, rank)` as fallback, but no test verifies behavior with hand ranks not in `HAND_RANK_ORDER`.
   - Recommendation: Add test with a frequency dict containing an unknown rank like `{"unknown_rank": 100}`.

2. **No explicit test for no-color console rendering**
   - File: `tests/unit/cli/test_formatters.py`
   - While `formatter_no_color` fixture exists and `test_color_with_colors_disabled` tests the helper, no test verifies that console output actually lacks ANSI codes when `use_color=False`.
   - Recommendation: Add test that captures console output with `use_color=False` and verifies no Rich markup codes appear in rendered output.

3. **Missing test for empty session results list in `print_session_details`**
   - File: `src/let_it_ride/cli/formatters.py:326-355`
   - No test for calling `print_session_details([])` to verify it handles empty list gracefully.
   - Recommendation: Add test for empty results list.

4. **Missing test for verbosity level 3 (debug)**
   - File: `src/let_it_ride/cli/formatters.py` docstring mentions verbosity 3 for "future use"
   - No tests verify that verbosity=3 behaves correctly (presumably same as verbosity=2).
   - Recommendation: Add test with verbosity=3 to document expected behavior.

5. **No test for very large numbers in formatting**
   - File: `src/let_it_ride/cli/formatters.py:116-128`
   - Currency and number formatting uses `:,` for thousands separators but no test verifies behavior with very large values (e.g., 1 billion).
   - Recommendation: Add edge case test with large currency values.

6. **Integration test assertions are weakened**
   - File: `tests/integration/test_cli.py` (diff lines 722-780)
   - Several integration test assertions were changed from exact string matches (e.g., `"Sessions: 1"`) to partial matches (`"Sessions"`). This reduces test specificity.
   - Impact: Tests may pass even if output format changes unexpectedly.
   - Recommendation: Consider using regex patterns or more specific assertions where possible.

### Low

1. **Test class naming inconsistency**
   - File: `tests/unit/cli/test_formatters.py`
   - Diff version uses `TestColorHelpers` (line 857), current version uses `TestColorHelper`. Minor inconsistency in pluralization.
   - Recommendation: Use consistent naming convention.

2. **No test for `_format_percent` with very small values**
   - File: `src/let_it_ride/cli/formatters.py:130-140`
   - Tests cover 0%, 50%, 100% but not very small percentages like 0.001%.
   - Recommendation: Add test for small values to verify precision handling.

3. **Unused TYPE_CHECKING import in test file**
   - File: `tests/unit/cli/test_formatters.py` (diff line 827)
   - The `TYPE_CHECKING` import and `if TYPE_CHECKING: pass` block appears unused.
   - Recommendation: Remove or use the TYPE_CHECKING block appropriately.

4. **Missing property-based testing opportunities**
   - File: `tests/unit/cli/test_formatters.py`
   - The `_format_currency` and `_format_percent` methods are pure functions ideal for property-based testing with hypothesis.
   - Recommendation: Consider adding hypothesis tests to verify properties like: formatted currency always starts with `$`, formatted percent always ends with `%`.

## Recommendations

### Immediate Actions (Before Merge)

1. **Add `print_config_summary` tests**: Create a fixture using either a real `FullConfig` object or a properly structured mock, and add tests verifying:
   - Output at verbosity 1 includes all expected config fields
   - Output at verbosity 0 produces no output
   - Seed is omitted when `random_seed` is None

2. **Add zero-value edge case tests**:
   ```python
   def test_statistics_zero_sessions(self, formatter: OutputFormatter) -> None:
       """Test statistics handles zero sessions gracefully."""
       stats = create_stats_with_zero_sessions()
       # Should not raise ZeroDivisionError
       formatter.print_statistics(stats, duration_secs=1.0)
   ```

3. **Add empty session results test**:
   ```python
   def test_session_details_empty_list(self, formatter_verbose: OutputFormatter) -> None:
       """Test session details with empty results list."""
       formatter_verbose.print_session_details([])
       output = get_console_output(formatter_verbose.console)
       # Should either print empty table or nothing
   ```

### Post-Merge Improvements

1. **Add property-based tests** for formatter helper methods using hypothesis library.

2. **Add snapshot/golden file tests** for formatted output to detect unintended formatting changes.

3. **Consider extracting table-building logic** into separate testable functions for better unit test isolation.

4. **Add performance test** for formatting large datasets (e.g., 10,000 session results) to ensure formatting doesn't become a bottleneck.

## Coverage Summary

| Method | Tested | Edge Cases |
|--------|--------|------------|
| `__init__` | Yes | Basic params only |
| `_color` | Yes | Both enabled/disabled |
| `_profit_color` | Yes | Positive/negative/zero |
| `_format_currency` | Yes | Sign variants, missing large values |
| `_format_percent` | Yes | Basic cases, missing small values |
| `print_config_summary` | No | - |
| `print_statistics` | Yes | Missing zero sessions |
| `print_hand_frequencies` | Yes | Empty dict, missing zero-sum |
| `print_session_details` | Yes | Missing empty list |
| `print_completion` | Yes | Including zero duration |
| `print_exported_files` | Yes | Empty list covered |
| `print_minimal_completion` | Yes | Basic test only |

**Overall Coverage Assessment**: Good foundation with approximately 80% method coverage. Critical gaps in `print_config_summary` testing and some edge cases for statistical calculations with zero values.
