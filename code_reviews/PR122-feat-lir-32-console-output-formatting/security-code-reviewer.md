# Security Review

## Summary

PR #122 implements console output formatting using the Rich library for the Let It Ride poker simulator. The changes introduce an `OutputFormatter` class that displays simulation results, statistics, and configuration summaries. From a security perspective, this PR presents **minimal risk** as it primarily deals with displaying internally-generated data (not user input) to the console. No critical or high severity security issues were identified.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

None identified.

### Low

#### 1. File Path Display Without Sanitization
**Location:** `src/let_it_ride/cli/formatters.py:384-385`, `src/let_it_ride/cli/formatters.py:402`

**Description:** File paths are printed directly to the console without any sanitization. While this is not exploitable in the current context (paths come from internal operations, not user input), displaying raw file paths could theoretically leak sensitive directory structure information.

**Code:**
```python
# formatters.py:384-385
for path in paths:
    self.console.print(f"  {path}")

# formatters.py:402
self.console.print(f"Output: {output_dir}")
```

**Impact:** Informational - file paths displayed are output paths controlled by configuration, not arbitrary user input. The risk is minimal since this is a local CLI tool.

**Recommendation:** Consider whether the full path or just the filename should be displayed. For a local CLI tool, this is acceptable behavior.

---

#### 2. Rich Markup Injection Potential (Theoretical)
**Location:** `src/let_it_ride/cli/formatters.py:97-99`

**Description:** The `_color` method wraps text with Rich markup tags. If the `text` parameter ever contained Rich markup characters (square brackets), it could theoretically interfere with rendering or cause unintended formatting.

**Code:**
```python
def _color(self, text: str, color: str) -> str:
    if self.use_color:
        return f"[{color}]{text}[/{color}]"
    return text
```

**Impact:** Very low - all data passed to this method comes from internally-generated statistics (floats, integers, enum values), not user input. The `color` parameter is hardcoded within the class ("green", "red", "yellow", "bold").

**Recommendation:** No action required for current implementation. If this class is ever extended to format user-provided text, consider using Rich's `escape()` function to prevent markup injection.

---

#### 3. Configuration Values Displayed Without Validation Context
**Location:** `src/let_it_ride/cli/formatters.py:142-176`

**Description:** The `print_config_summary` method displays configuration values that originate from YAML files. While these values have already been validated by Pydantic models in the config loader, the formatter assumes all values are safe to display.

**Code:**
```python
table.add_row("Betting System", config.bankroll.betting_system.type)
table.add_row("Strategy", config.strategy.type)
table.add_row("Bonus Strategy", config.bonus_strategy.type)
```

**Impact:** Very low - configuration values are validated by Pydantic before reaching this code. String fields like `type` are constrained to known enum values.

**Recommendation:** No action required. The defense-in-depth approach of validating config at load time is appropriate.

---

### Informational

#### Positive Security Practices Observed

1. **Type Safety:** The code uses type hints throughout, which helps prevent type confusion issues.

2. **Input Validation at Boundaries:** User input (config files) is validated by Pydantic models before reaching the formatter. The formatter only receives strongly-typed objects.

3. **No Dynamic Code Execution:** The formatter does not use `eval()`, `exec()`, or any form of dynamic code execution.

4. **No External Network Calls:** The formatter is purely local - it does not make network requests or load external resources.

5. **No Sensitive Data Exposure:** The displayed data consists of simulation statistics and configuration settings. No passwords, API keys, or other sensitive data is handled.

6. **Safe String Formatting:** All string formatting uses f-strings with format specifiers (e.g., `{value:,.2f}`) rather than `.format()` or `%` formatting, which could be vulnerable to format string attacks if user input were involved.

7. **Division by Zero Protection:** The code properly guards against division by zero in throughput calculations:
   ```python
   # formatters.py:285
   hands_per_sec = stats.total_hands / duration_secs if duration_secs > 0 else 0
   ```

8. **Immutable Constants:** Hand rank constants (`HAND_RANK_ORDER`, `HAND_RANK_DISPLAY`) are defined as module-level constants, preventing runtime modification.

## Recommendations

1. **No immediate security changes required.** The PR is well-implemented from a security standpoint.

2. **Future consideration:** If the formatter is ever extended to handle user-provided text (e.g., custom labels or notes), consider:
   - Using `rich.markup.escape()` to prevent markup injection
   - Adding input validation for string length to prevent DoS via extremely long strings

3. **Documentation suggestion:** Consider adding a note to the class docstring that input data is expected to be validated/sanitized before being passed to the formatter.

## Files Reviewed

- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli/formatters.py` (new file, 403 lines)
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli/app.py` (modified from cli.py)
- `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli/__init__.py` (new file, 10 lines)
- `/Users/chrishenry/source/let_it_ride/tests/unit/cli/test_formatters.py` (new file, 447 lines)
- `/Users/chrishenry/source/let_it_ride/tests/integration/test_cli.py` (modified)

## Conclusion

This PR introduces no security vulnerabilities. The code follows secure coding practices and operates entirely on internally-generated, pre-validated data. The Rich library is used safely for console output formatting. **Approved from a security perspective.**
