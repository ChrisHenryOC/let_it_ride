# Security Code Review for PR #140

## Summary

This PR adds multi-seat table configuration support to the CLI, integrating `TableConfig` with `FullConfig` and enabling `TableSession` usage when `num_seats > 1`. The changes are primarily internal simulation logic with minimal external attack surface. No critical security vulnerabilities were identified; the existing input validation via Pydantic models and `yaml.safe_load()` provides adequate protection for the configuration parsing path.

## Findings

### Critical

None identified.

### High

None identified.

### Medium

**M1: Potential Integer Overflow in Composite ID Calculation** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:474-475`

The composite ID calculation `session_id * num_seats + seat_idx` could theoretically overflow with very large `session_id` values (up to 100M sessions) multiplied by `num_seats` (up to 6). While Python handles arbitrary precision integers, this could cause memory issues when pre-allocating result lists.

```python
# Line 474-475
composite_id = session_id * num_seats + seat_idx
results.append((composite_id, seat_result))
```

With `num_sessions=100,000,000` and `num_seats=6`, the maximum composite ID would be ~600M. This is within acceptable bounds for Python list indexing, but the pre-allocated list at line 526 `[None] * expected_results` would attempt to allocate 600M slots, potentially causing memory exhaustion.

**Recommendation**: Consider validating that `num_sessions * num_seats` does not exceed a reasonable threshold, or document the memory implications. The existing validation (`num_sessions <= 100_000_000`) combined with `num_seats <= 6` bounds this to 600M results maximum. CWE-770: Allocation of Resources Without Limits.

### Low

**L1: Output Directory Path from YAML Config** - `/Users/chrishenry/source/let_it_ride/configs/multi_seat_example.yaml:98`

The example configuration includes `directory: "./results/multi_seat"` which is a relative path that gets resolved based on current working directory. This is not a vulnerability in itself since:
1. The path comes from user-provided YAML config files
2. The `Path.mkdir(parents=True, exist_ok=True)` in exporters will create directories
3. No path traversal beyond user intention is possible

The existing code at `cli/app.py:168` properly resolves paths when overridden via CLI: `str(output.resolve())`.

**Recommendation**: No action required. The design appropriately trusts user-provided configuration paths, which is expected for a local CLI tool.

### Info

**I1: Proper Use of yaml.safe_load** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/loader.py:131`

The configuration loader correctly uses `yaml.safe_load()` instead of `yaml.load()`, preventing arbitrary Python object deserialization attacks (CWE-502: Deserialization of Untrusted Data).

**I2: Input Validation via Pydantic** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:107`

The `TableConfig` model properly validates `num_seats` with bounds checking (`ge=1, le=6`) using Pydantic's `Field` constraints. Combined with `model_config = ConfigDict(extra="forbid")`, this prevents injection of unexpected fields.

```python
num_seats: Annotated[int, Field(ge=1, le=6)] = 1
```

**I3: Type Safety in Session Configuration** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/utils.py:124-147`

The new `create_table_session_config()` function properly passes configuration through `TableSessionConfig`, which validates parameters via `validate_session_config()`. No untrusted data flows directly to sensitive operations.

**I4: No Command Injection Vectors**

The PR does not introduce any subprocess calls, shell execution, or dynamic code evaluation. All configuration values are handled as typed data through Pydantic models.

## Security Checklist

| Check | Status | Notes |
|-------|--------|-------|
| SQL/NoSQL Injection | N/A | No database operations |
| Command Injection | Pass | No subprocess/shell calls |
| Path Traversal | Pass | User-controlled paths are expected behavior for CLI tool |
| XSS/CSRF | N/A | No web interface |
| Sensitive Data Exposure | Pass | No credentials or PII handled |
| Input Validation | Pass | Pydantic models with `Field` constraints |
| YAML Deserialization | Pass | Uses `yaml.safe_load()` |
| Resource Exhaustion | Note | See M1 - bounded by existing limits |
| Authentication/Authorization | N/A | Local CLI tool, no auth required |
| IDOR | N/A | No user-scoped resources |

## Conclusion

The PR follows secure coding practices. The main area of note (M1) is a theoretical resource concern bounded by existing configuration limits rather than a true vulnerability. The use of `yaml.safe_load()`, Pydantic validation with strict field constraints, and type-safe data flow through the simulation pipeline demonstrate appropriate security hygiene for a local CLI tool.
