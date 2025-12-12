# Issue #34: LIR-31 CLI Entry Point

GitHub Issue: https://github.com/chrishenry/let_it_ride/issues/34

## Tasks

1. [x] Create scratchpad with implementation plan
2. [ ] Implement `run` command with full options
   - `--config` / `-c`: Config file path (positional argument)
   - `--output` / `-o`: Output directory override
   - `--seed`: Random seed override
   - `--sessions`: Session count override
   - `--quiet` / `-q`: Minimal output
   - `--verbose` / `-v`: Detailed output (NOTE: conflicts with existing `-v` for version)
   - Progress bar (disable with --quiet)
3. [ ] Implement `validate` command for config validation
4. [ ] Implement proper exit codes (0 = success, 1 = error)
5. [ ] Write integration tests in `tests/integration/test_cli.py`
6. [ ] Run full test suite, linting, and type checking

## Design Notes

### Version Flag Conflict
The existing CLI uses `-v` for `--version`. The issue requests `-v` for `--verbose`.
Resolution: Keep `-v` for version (existing behavior), use `--verbose` without short flag.

### Command Structure
```
let-it-ride --version
let-it-ride run <config> [options]
let-it-ride validate <config>
```

### Integration Points
- `load_config()` from `config.loader` - handles validation
- `SimulationController` from `simulation.controller` - runs simulation
- `CSVExporter` from `analytics.export_csv` - exports results
- Config exceptions: `ConfigFileNotFoundError`, `ConfigParseError`, `ConfigValidationError`

### Progress Callback
SimulationController accepts `progress_callback: Callable[[int, int], None]`
- Called with (completed_sessions, total_sessions)
- Use Rich Progress for progress bar display

### Output Modes
- Default: Show progress bar, summary at end
- `--quiet`: No progress bar, minimal output (just success/failure)
- `--verbose`: Show per-session details + progress bar + summary

### Exit Codes
- 0: Success
- 1: Error (config error, runtime error, etc.)

## Files to Modify/Create
- `src/let_it_ride/cli.py` - Main implementation
- `tests/integration/test_cli.py` - Integration tests (NEW)
- `tests/unit/test_cli.py` - Update unit tests
