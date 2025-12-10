# Security Code Review: PR #119 - LIR-27 CSV Export

## Summary

This PR adds CSV export functionality for simulation results including session summaries, aggregate statistics, and per-hand detail records. The implementation is well-structured and uses Python's standard `csv` module with proper escaping. Given this is a local simulation tool without user-controlled inputs (data comes from internal simulation objects, not external sources), the security posture is appropriate for its use case.

## Findings by Severity

### Low Severity

#### 1. Prefix Parameter Not Sanitized for Filesystem Characters

**Location:** `src/let_it_ride/analytics/export_csv.py:224` (CSVExporter.__init__)

**Description:** The `prefix` parameter is used directly in filename construction without validation. While currently only called with hardcoded values internally, if this is extended to accept user configuration via CLI or config files, special characters in the prefix could cause issues.

**Impact:** Potential for unexpected behavior if prefix contains path separators or invalid filename characters (e.g., `/`, `\`, `:`, etc.). In the current context where prefixes come from trusted code, this is minimal risk.

**Code Reference:**
```python
# Line 272
path = self._output_dir / f"{self._prefix}_sessions.csv"
```

**Remediation:** Consider adding prefix validation if this class will accept user-provided values in the future:
```python
def __init__(self, output_dir: Path, prefix: str = "simulation", ...):
    # Validate prefix contains only safe characters
    if not prefix.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"Prefix must be alphanumeric with underscores/hyphens: {prefix}")
    self._prefix = prefix
```

**CWE Reference:** CWE-20 (Improper Input Validation)

---

#### 2. Directory Creation with parents=True

**Location:** `src/let_it_ride/analytics/export_csv.py:255`

**Description:** The `_ensure_output_dir()` method creates directories with `parents=True`, which will create all intermediate directories. While convenient, this could create unintended directory structures if `output_dir` contains unexpected path components.

**Impact:** In the current local CLI tool context, this is expected and useful behavior. The risk is minimal since paths come from configuration files or code, not untrusted input.

**Code Reference:**
```python
# Line 255
self._output_dir.mkdir(parents=True, exist_ok=True)
```

**Recommendation:** No action required for current use case. If the tool is extended to accept output paths from untrusted sources, consider:
- Validating the output path is within an expected base directory
- Using `resolve()` and checking for path traversal

---

### Informational

#### 1. Good Practice: Using Python's csv Module

**Location:** `src/let_it_ride/analytics/export_csv.py:143-148, 169-172, 203-207`

The implementation correctly uses Python's `csv.DictWriter` which automatically handles:
- Proper escaping of commas, quotes, and newlines in field values
- Consistent quoting behavior

This mitigates CSV injection concerns. The test at line 352-382 in `tests/integration/test_export_csv.py` (`test_special_characters_escaped`) verifies this behavior.

---

#### 2. CSV Injection Mitigation Assessment

**Context:** CSV injection (formula injection) occurs when cell values starting with `=`, `+`, `-`, or `@` are interpreted as formulas by spreadsheet applications.

**Analysis:** In this implementation:
- Data exported comes from internal simulation objects (SessionResult, HandRecord, AggregateStatistics)
- Field values are:
  - Numeric values (bankroll, payouts, etc.)
  - Predefined enum values ("win", "loss", "push", "ride", "pull")
  - Card representation strings ("Ah Kh Qh")
  - Hand rank names ("royal_flush", "three_of_a_kind")

None of these fields are user-controlled text that could contain formula injection payloads. The data is generated programmatically from game simulation, not from untrusted user input.

**Verdict:** CSV injection is not a practical concern for this module given the data sources.

---

#### 3. Good Practice: UTF-8 with BOM Option

**Location:** `src/let_it_ride/analytics/export_csv.py:142, 168, 202`

The implementation correctly:
- Uses `utf-8-sig` encoding when BOM is requested (Excel compatibility)
- Uses `utf-8` encoding when BOM is disabled
- Specifies `newline=""` to prevent double newlines on Windows

---

#### 4. Good Practice: Field Validation

**Location:** `src/let_it_ride/analytics/export_csv.py:137-140, 197-200`

The implementation validates field names against an allowlist before export, preventing unexpected field injection:
```python
invalid_fields = set(field_names) - set(SESSION_RESULT_FIELDS)
if invalid_fields:
    raise ValueError(f"Invalid field names: {invalid_fields}")
```

---

## Security Positive Practices Observed

1. **Allowlist-based field validation** - Only predefined fields can be exported
2. **Proper CSV escaping** - Using standard library handles special characters correctly
3. **Type safety** - Type hints and dataclass usage provide compile-time safety
4. **No eval/exec usage** - No dynamic code execution
5. **No subprocess calls** - No shell command injection vectors
6. **No pickle deserialization** - No untrusted deserialization
7. **Encoding explicitly specified** - Prevents encoding-related issues

## Recommendations Summary

| Priority | Recommendation | Effort |
|----------|---------------|--------|
| Low | Add prefix validation if accepting user input in future | Minimal |
| None | Current implementation is appropriate for local simulation tool | N/A |

## Conclusion

This PR implements CSV export in a secure manner appropriate for a local simulation tool. The code uses Python's standard CSV module for proper escaping, validates field names against allowlists, and operates only on internally-generated simulation data. No critical or high-severity security issues were identified. The low-severity finding regarding prefix validation is a defensive recommendation for future extensibility rather than a current vulnerability.

**Review Status:** APPROVED - No blocking security issues
