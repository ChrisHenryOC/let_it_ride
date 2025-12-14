# Documentation Accuracy Review: PR #134 (feat: LIR-39 HTML Report Generation)

## Summary

This PR introduces HTML report generation with embedded Plotly visualizations. The documentation is generally comprehensive with well-structured docstrings for all public classes and functions. However, there are discrepancies between the theoretical hand frequencies documented in `export_html.py` and the existing validation module, as well as some minor documentation accuracy issues regarding return types and missing type hints.

## Findings

### Medium

#### 1. Inconsistent Theoretical Hand Frequency Values
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:29-43`

The `THEORETICAL_HAND_FREQUENCIES` dictionary uses values that differ significantly from the canonical values in `validation.py`:

```python
# export_html.py (new code)
THEORETICAL_HAND_FREQUENCIES: dict[str, float] = {
    "royal_flush": 0.000154,      # Claims 0.0154%
    "straight_flush": 0.00139,    # Claims 0.139%
    "four_of_a_kind": 0.024,      # Claims 2.4%
    "full_house": 0.144,          # Claims 14.4%
    ...
}
```

Compare to `validation.py` (existing code):
```python
# validation.py (correct mathematical values)
THEORETICAL_HAND_PROBS: dict[str, float] = {
    "royal_flush": 4 / 2598960,        # 0.000154% (not 0.0154%)
    "straight_flush": 36 / 2598960,    # 0.00139% (not 0.139%)
    "four_of_a_kind": 624 / 2598960,   # 0.024% (not 2.4%)
    "full_house": 3744 / 2598960,      # 0.144% (not 14.4%)
    ...
}
```

The values in `export_html.py` appear to already be multiplied by 100 (percentage form), but this is inconsistent with how they are used. In `_create_hand_frequency_chart()` at line 333-334, the code does:
```python
actual_values = [actual_freq.get(h, 0) * 100 for h in hands]  # Converts to %
theoretical_values = [THEORETICAL_HAND_FREQUENCIES.get(h, 0) for h in hands]  # Already in %?
```

This creates a mismatch: actual values are multiplied by 100, but theoretical values are not. The comment at line 29-30 states "These are the expected frequencies for standard poker hands" but does not clarify the unit (decimal vs percentage).

**Recommendation:** Either:
1. Use the exact mathematical probabilities from `validation.py` and multiply by 100 in the chart code, OR
2. Import `THEORETICAL_HAND_PROBS` from `validation.py` to avoid duplication and inconsistency

---

#### 2. Missing Documentation for Hand Frequency Keys
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:29-43`

The `THEORETICAL_HAND_FREQUENCIES` dictionary uses keys like `pair_tens_or_better` and `pair_under_tens` which are simulator-specific categories, but the docstring does not explain this distinction. The `validation.py` module handles this with `_normalize_hand_frequencies()` but `export_html.py` does not document this design decision.

```python
"pair_tens_or_better": 16.91,  # Paying pair (10s+)
"pair_under_tens": 12.93,      # Non-paying pair (under 10s)
```

The inline comments help, but a docstring explaining why Let It Ride uses different pair categories than standard poker would improve clarity.

---

### Low

#### 3. Docstring Return Type Mismatch for `generate_html_report`
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:710-738`

The function signature shows `-> None` but the docstring does not explicitly state "Returns: None" - it only has Args and Example sections. While this is minor, other functions in the same file (e.g., `HTMLExporter.export`) document their return values explicitly.

```python
def generate_html_report(
    results: SimulationResults,
    stats: DetailedStatistics,
    output_path: Path,
    config: HTMLReportConfig | None = None,
) -> None:
    """Generate an HTML report and save to file.
    ...
    # Missing "Returns: None." line
    """
```

---

#### 4. Scratchpad Documentation Not Aligned with Implementation
**File:** `/Users/chrishenry/source/let_it_ride/scratchpads/issue-42-html-report-generation.md:27-30`

The scratchpad states:
```markdown
- Use Plotly's `to_html()` with `full_html=False, include_plotlyjs='cdn'` for embedding
- Self-contained option uses `include_plotlyjs=True` for offline viewing
```

However, the implementation at line 533 uses:
```python
include_plotlyjs: bool | str = True if self._config.self_contained else "cdn"
```

This is a type mismatch in the documentation - the code correctly uses `True` (boolean) for self-contained mode, not the string `'True'`. The scratchpad documentation is technically correct but could be clearer about the boolean vs string distinction.

---

#### 5. Test File Docstring Could Be More Specific
**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_export_html.py:1-5`

The module docstring is generic:
```python
"""Integration tests for HTML report generation functionality.

Tests file creation, content validation, chart generation, template rendering,
responsive design elements, and various configuration options.
"""
```

It would be more useful to mention which specific classes/functions are under test (HTMLExporter, HTMLReportGenerator, HTMLReportConfig, generate_html_report) to help developers quickly understand test coverage.

---

#### 6. HTMLReportConfig Attribute Documentation Uses "Only"
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_html.py:52`

```python
chart_library: Literal["plotly"] = "plotly"  # Only Plotly for now
```

The docstring states `chart_library: Chart library to use (only "plotly" supported).` This is accurate but the `Literal["plotly"]` type annotation already enforces this constraint. The comment "Only Plotly for now" suggests future expansion but no roadmap is documented. Consider noting in the docstring whether other chart libraries are planned.

---

#### 7. README Not Updated with HTML Export Feature
**File:** `/Users/chrishenry/source/let_it_ride/README.md:19`

The README currently states:
```markdown
- **Export Options**: CSV, JSON, and HTML report generation (in progress)
```

Since HTML report generation is now implemented, this should be updated to remove "(in progress)" for the HTML portion.

---

## Documentation Quality Notes

### Positive Observations

1. **Comprehensive docstrings**: All public classes and functions have detailed docstrings with Args, Returns, and Attributes sections.

2. **Example in main entry point**: The `generate_html_report()` function includes a usage example in its docstring.

3. **Well-documented dataclasses**: `HTMLReportConfig`, `_ChartData`, and `_ReportContext` all have clear attribute documentation.

4. **Template documentation**: The Jinja2 template includes CSS comments explaining responsive breakpoints and print styles.

5. **Test docstrings**: All test methods have single-line docstrings explaining what they verify.
