# Security Code Review: PR #124 - LIR-28 JSON Export

## Summary

The JSON export functionality (LIR-28) introduces a clean, well-structured module for exporting simulation results to JSON format. The implementation follows established patterns from the existing CSV export module and uses Python's built-in `json` library safely. **No critical or high-severity security vulnerabilities were identified.** The code handles serialization properly without using unsafe deserialization methods.

## Findings by Severity

### Critical

No critical security issues identified.

### High

No high-severity security issues identified.

### Medium

No medium-severity security issues identified.

### Low

#### L1: Path Traversal - Accepts User-Controlled Paths Without Validation

**File:** `src/let_it_ride/analytics/export_json.py`
**Lines:** 156-163 (`export_json` function), 299-321 (`JSONExporter.export` method)

**Description:**
The `export_json()` function and `JSONExporter` class accept file paths directly without validation or sanitization. While this is consistent with the existing CSV export pattern and the paths are controlled by application code rather than direct user input, the function documentation does not warn about path traversal risks.

**Impact:**
If these functions are exposed to user-controlled input in future integrations (e.g., web API, expanded CLI options), an attacker could potentially write JSON files to arbitrary locations on the filesystem using path traversal sequences (e.g., `../../etc/malicious.json`).

**Current Mitigations:**
- Paths are currently controlled by application configuration, not direct user input
- The CLI uses `output.resolve()` (line 168 in `cli/app.py`) which normalizes paths
- The `JSONExporter` class constructs filenames internally using the prefix

**Recommendation:**
Consider adding path validation as a defensive measure, especially if these exports may be exposed to less trusted inputs in the future:

```python
def _validate_output_path(path: Path, base_dir: Path | None = None) -> None:
    """Validate output path is safe for writing.

    Args:
        path: The output path to validate.
        base_dir: Optional base directory to restrict writes to.

    Raises:
        ValueError: If path would escape base_dir or contains suspicious patterns.
    """
    resolved = path.resolve()
    if base_dir is not None:
        base_resolved = base_dir.resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise ValueError(f"Path {path} escapes base directory {base_dir}")
```

**Severity Rationale:** Low because paths are currently application-controlled, not user-input, and this follows the existing codebase pattern.

**References:** CWE-22 (Path Traversal)

---

#### L2: Directory Creation with `parents=True` May Create Unintended Directories

**File:** `src/let_it_ride/analytics/export_json.py`
**Line:** 297

**Description:**
The `_ensure_output_dir()` method creates directories with `parents=True`:

```python
self._output_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
```

While this is convenient and matches the CSV exporter pattern, it could create an unintended deep directory hierarchy if the path is malformed or contains path traversal sequences.

**Impact:**
Minimal impact in current usage since output directories come from validated configuration. However, if combined with user-controlled input, this could create arbitrary directories.

**Recommendation:**
This is acceptable for the current use case. The existing pattern is consistent with the CSV exporter. No changes required unless the API is exposed to less trusted inputs.

**References:** CWE-73 (External Control of File Name or Path)

---

### Informational

#### I1: Positive Security Practice - Uses `json.dump()` Not `pickle`

**File:** `src/let_it_ride/analytics/export_json.py`
**Line:** 216

The implementation correctly uses `json.dump()` for serialization rather than `pickle`, which avoids the serious security risks associated with pickle deserialization of untrusted data. This is the correct approach for data interchange formats.

---

#### I2: Positive Security Practice - `load_json()` Only Returns Dictionary

**File:** `src/let_it_ride/analytics/export_json.py`
**Lines:** 221-246

The `load_json()` function correctly returns a plain dictionary rather than attempting to reconstruct complex objects. This design choice explicitly avoids any potential for object injection or unsafe deserialization:

```python
def load_json(path: Path) -> dict[str, Any]:
    """Load simulation results from JSON file.

    Returns a dictionary rather than attempting to reconstruct the full
    SimulationResults object, since that would require re-instantiating
    all Pydantic models and dataclasses with their validation.
    ...
    """
```

This is a good security practice that keeps the attack surface minimal.

---

#### I3: Positive Security Practice - No `eval()`, `exec()`, or Dynamic Code Execution

The implementation does not use `eval()`, `exec()`, `compile()`, or any form of dynamic code execution. All serialization is performed through safe, static methods.

---

#### I4: UTF-8 Encoding Specified Explicitly

**File:** `src/let_it_ride/analytics/export_json.py`
**Lines:** 215, 244

Both write and read operations explicitly specify UTF-8 encoding:
```python
with path.open("w", encoding="utf-8") as f:
with path.open("r", encoding="utf-8") as f:
```

This prevents potential encoding-related issues and ensures consistent behavior across platforms.

---

#### I5: `ensure_ascii=False` Used Safely

**File:** `src/let_it_ride/analytics/export_json.py`
**Line:** 216

The use of `ensure_ascii=False` in `json.dump()` allows non-ASCII characters to be written directly rather than escaped. This is safe because:
1. The file is explicitly opened with UTF-8 encoding
2. The data being serialized is internally generated simulation data, not user input

---

## Files Reviewed

| File | Status |
|------|--------|
| `src/let_it_ride/analytics/export_json.py` | Reviewed - No significant issues |
| `tests/integration/test_export_json.py` | Reviewed - Test code only |
| `docs/json_schema.md` | Reviewed - Documentation only |

## Conclusion

The JSON export implementation is well-designed from a security perspective. It follows secure coding practices by:
- Using safe serialization (JSON, not pickle)
- Returning plain dictionaries instead of reconstructing objects
- Explicitly handling encoding
- Avoiding dynamic code execution

The only minor concern (L1) relates to accepting paths without validation, but this is consistent with the existing CSV export module and is mitigated by the fact that paths are currently controlled by application configuration rather than direct user input.

**Recommendation:** Approve the PR from a security standpoint. Consider the defensive path validation suggestion (L1) as a future enhancement if the export APIs are exposed to less trusted inputs.
