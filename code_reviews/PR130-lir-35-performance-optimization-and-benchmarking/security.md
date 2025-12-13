# Security Review for PR #130

## Summary

This PR adds a performance benchmarking suite with throughput, memory, and profiling tools. From a security perspective, the changes are low-risk as this is internal benchmarking tooling with no user-facing input handling, network operations, or sensitive data processing. The deck optimization changes are safe and do not introduce security concerns.

## Findings by Severity

### Critical

None.

### High

None.

### Medium

**1. Arbitrary File Write via `--output` Argument** - `benchmarks/profile_hotspots.py:117-143`

The `profile_to_file()` function accepts a user-provided path via command line argument and writes profiling data to that location without any path validation or sanitization.

```python
def profile_to_file(
    output_path: str = "profile_output.prof",  # Line 117
    ...
) -> None:
    ...
    profiler.dump_stats(output_path)  # Line 141
```

While this is an internal benchmarking tool not exposed to external users, allowing arbitrary file paths could lead to:
- Overwriting existing files (no confirmation)
- Writing to sensitive directories if run with elevated privileges
- Path traversal if invoked programmatically with untrusted input

**CWE-22: Path Traversal**

**Recommendation**: Consider adding path validation to ensure output stays within expected directories, or at minimum add a check that the file does not already exist.

### Low

**1. Integer Overflow on Large Iterations** - `benchmarks/benchmark_throughput.py:50,76`

The benchmark functions accept an `iterations: int` parameter with no upper bound validation. While Python handles large integers natively, extremely large values could cause memory exhaustion when pre-generating hands in memory:

```python
# Line 60: Pre-generates all hands in memory before timing
hands = [rng.sample(all_cards, 5) for _ in range(iterations)]
```

This is low severity as this is a developer tool with hardcoded defaults.

**2. Profile Stats Internal API Usage** - `benchmarks/profile_hotspots.py:167`

The code accesses `stats.stats` which is an internal pstats attribute:

```python
stats_dict = stats.stats  # type: ignore[attr-defined]  # Line 167
```

While not a security issue per se, relying on internal APIs could break with Python version updates. The `type: ignore` comment acknowledges this is non-public API.

---

## Notes

The following aspects were reviewed and found to be secure:

1. **No injection vulnerabilities**: No SQL, command injection, or template injection patterns present.
2. **No unsafe deserialization**: No `pickle`, `yaml.unsafe_load`, or `eval`/`exec` usage.
3. **No subprocess calls**: No shell command execution.
4. **No network operations**: All operations are local file/memory based.
5. **No authentication/authorization concerns**: Internal benchmarking tool.
6. **Deck changes are safe**: The optimization from manual Fisher-Yates to `random.shuffle()` is cryptographically equivalent when using the same RNG instance.
