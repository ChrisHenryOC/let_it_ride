# Security Review - PR #120

## Summary

This PR implements a CLI entry point for the Let It Ride simulation tool using Typer. The implementation follows secure coding practices overall: it uses `yaml.safe_load()` for YAML parsing, applies Pydantic validation for configuration, and avoids common injection vulnerabilities. One medium-severity concern exists around potential information disclosure via verbose error messages, and there are minor informational items regarding path handling.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

#### 1. Potential Information Disclosure via Error Messages

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli.py` (lines 60-74)

**Description:** The `_load_config_with_errors()` function outputs error details directly to the console, including the full absolute path and detailed exception messages. While helpful for debugging, this could disclose sensitive filesystem information in shared environments or CI/CD logs.

**Relevant Code:**
```python
except ConfigFileNotFoundError as e:
    error_console.print(f"[red]Error:[/red] {e.message}")
    if e.details:
        error_console.print(f"[dim]{e.details}[/dim]")
```

The details from `ConfigFileNotFoundError` include the absolute path:
```python
# From loader.py line 112:
details=f"Please ensure the file exists at: {config_path.absolute()}"
```

**Impact:** In multi-user systems or shared hosting, absolute paths could reveal usernames, directory structures, or deployment details.

**Remediation:** Consider providing verbose error output only when `--verbose` is enabled. In default/quiet mode, use a less detailed message.

**CWE Reference:** CWE-209 (Generation of Error Message Containing Sensitive Information)

### Low

#### 1. Output Directory Creation Without Explicit Permission Handling

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/export_csv.py` (lines 273-275)

**Description:** The `CSVExporter._ensure_output_dir()` method creates directories with default permissions:

```python
def _ensure_output_dir(self) -> None:
    """Create output directory if it doesn't exist."""
    self._output_dir.mkdir(parents=True, exist_ok=True)
```

**Impact:** On systems with permissive umask settings, this could create directories accessible to other users. For a simulation tool writing non-sensitive statistical data, this is low risk.

**Remediation:** If security-sensitive data were ever written, consider setting explicit permissions:
```python
self._output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
```

**CWE Reference:** CWE-276 (Incorrect Default Permissions)

#### 2. User-Controlled Output Path Without Canonicalization

**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli.py` (lines 160-164)

**Description:** The `--output` option accepts a user-provided path that is used directly without path canonicalization:

```python
if output is not None:
    out_config = cfg.output
    cfg = cfg.model_copy(
        update={"output": out_config.model_copy(update={"directory": str(output)})}
    )
```

**Impact:** While not exploitable as a path traversal attack in this context (the user is intentionally specifying their output location), symbolic link attacks could theoretically redirect output. This is a local CLI tool with no elevated privileges, so the practical risk is minimal.

**Remediation:** For defense-in-depth, consider using `Path.resolve()` to canonicalize the path:
```python
cfg = cfg.model_copy(
    update={"output": out_config.model_copy(update={"directory": str(output.resolve())})}
)
```

**CWE Reference:** CWE-22 (Path Traversal)

## Informational

### Positive Security Practices Observed

1. **Safe YAML Loading:** The `load_config()` function in `config/loader.py` uses `yaml.safe_load()` rather than `yaml.load()`, preventing arbitrary Python object deserialization attacks (CWE-502).

2. **Input Validation via Pydantic:** All configuration values are validated through Pydantic models with strict constraints (`extra="forbid"`, type annotations, and range validators). This provides robust defense against malformed input.

3. **No Shell Command Execution:** The CLI does not invoke shell commands or use `subprocess` with user input, avoiding command injection risks.

4. **No eval() or exec():** Despite the project having "custom" strategy options with "expression" fields, the CLI itself does not execute arbitrary code from user input.

5. **Proper Exit Codes:** The CLI properly uses exit code 1 for errors and 0 for success, allowing proper integration with shell scripts and CI/CD pipelines.

6. **Error to stderr:** Error messages are directed to `error_console` (stderr) rather than stdout, following Unix conventions.

7. **No Sensitive Data Handling:** The CLI does not handle passwords, API keys, or other credentials.

8. **Integer Type for Seed:** The `--seed` option uses `int | None` type, preventing injection through the seed parameter.

### Note on Custom Expression Fields

The configuration models include `expression` fields for custom betting systems and strategies (e.g., `CustomBettingConfig.expression`, `CustomBonusStrategyConfig.expression`). These could potentially be executed with `eval()` elsewhere in the codebase. However:

- The CLI code reviewed in this PR does not execute these expressions
- This is noted for completeness; a separate review of the execution layer is recommended

## Recommendations

1. **Medium Priority:** Consider suppressing full filesystem paths in error messages when not in verbose mode to reduce information disclosure risk.

2. **Low Priority:** Add `Path.resolve()` when processing the `--output` option for defense-in-depth path canonicalization.

3. **Future Consideration:** If the simulator ever handles sensitive data (e.g., actual gambling accounts), implement explicit file permissions on output directories.

4. **Documentation:** Document that config files should be treated as code since they can contain expressions that may be evaluated.
