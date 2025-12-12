# Test Coverage Review - PR #121

## Summary

This PR adds sample configuration files demonstrating various simulator features (basic strategy, conservative, aggressive, bonus comparison, progressive betting) along with comprehensive integration tests validating that all configs load correctly. The test file (`tests/integration/test_sample_configs.py`) provides good schema validation coverage but lacks end-to-end simulation execution tests to verify configs work correctly at runtime.

## Critical Issues

None.

## High Severity

### 1. Missing End-to-End Simulation Execution Tests
**File:** `tests/integration/test_sample_configs.py`

The tests verify that configuration files load and validate correctly through Pydantic, but do not test that the configurations can actually run a simulation successfully. This is an important gap because:

- A config could be schema-valid but cause runtime errors during simulation
- Strategy/betting system combinations may have incompatibilities only discovered at runtime
- The aggressive strategy with `include_gutshots` and `include_backdoor_flush` options should be verified to function correctly

**Recommendation:** Add at least one test per config that runs a small simulation (e.g., 3 sessions, 10 hands each) to verify end-to-end functionality:

```python
@pytest.mark.parametrize("config_file", SAMPLE_CONFIG_FILES)
def test_config_runs_simulation(self, config_file: str) -> None:
    """Test that config can execute a minimal simulation."""
    config = load_config(CONFIGS_DIR / config_file)
    # Override for fast test execution
    config.simulation.num_sessions = 3
    config.simulation.hands_per_session = 10
    # Run simulation and verify no exceptions
    controller = SimulationController(config)
    results = controller.run()
    assert len(results.session_results) == 3
```

### 2. No Negative Testing for Config Schema Variations
**File:** `tests/integration/test_sample_configs.py`

The tests do not verify that malformed versions of these configs are properly rejected. For new users copying and modifying sample configs, it would be valuable to ensure error messages are clear.

**Recommendation:** Add tests that intentionally break each config type and verify appropriate errors are raised.

## Medium Severity

### 1. Missing Tests for Config Relationships/Constraints
**File:** `tests/integration/test_sample_configs.py`

Some configs have implicit relationships that should be tested:

- `aggressive.yaml:186-189`: The wider stop conditions (win_limit: 400, loss_limit: 300) should be verified as larger than basic_strategy's limits
- `progressive_betting.yaml:852-860`: The max_bet (500) should be verified against starting_amount (1000) to ensure at least 2 full progressions are possible

**Recommendation:** Add comparative tests that verify config relationships:

```python
def test_aggressive_has_wider_limits_than_basic(self) -> None:
    basic = load_config(CONFIGS_DIR / "basic_strategy.yaml")
    aggressive = load_config(CONFIGS_DIR / "aggressive.yaml")
    assert aggressive.bankroll.stop_conditions.win_limit > basic.bankroll.stop_conditions.win_limit
    assert aggressive.bankroll.stop_conditions.loss_limit > basic.bankroll.stop_conditions.loss_limit
```

### 2. bonus_comparison.yaml Tier Validation Missing
**File:** `tests/integration/test_sample_configs.py:163-169`

The test `test_has_scaling_tiers` only verifies that at least one tier exists. It does not verify:
- Tier profit ranges are contiguous (no gaps)
- Tier profit ranges do not overlap
- Bet amounts increase with profit level (logical progression)

**Recommendation:** Enhance the test to validate tier structure:

```python
def test_scaling_tiers_are_valid(self) -> None:
    config = load_config(CONFIGS_DIR / "bonus_comparison.yaml")
    tiers = config.bonus_strategy.bankroll_conditional.scaling.tiers
    assert len(tiers) >= 2  # Need multiple tiers for meaningful scaling
    # Verify tiers are ordered by min_profit
    for i in range(len(tiers) - 1):
        assert tiers[i].min_profit < tiers[i + 1].min_profit
```

### 3. Output Configuration Not Validated
**File:** `tests/integration/test_sample_configs.py`

None of the tests verify that output configurations are valid:
- Output directories are valid path patterns
- Visualization chart types exist
- Format combinations are valid

**Recommendation:** Add output configuration validation tests.

## Low Severity

### 1. README.md Test Could Be More Comprehensive
**File:** `tests/integration/test_sample_configs.py:193-218`

The `TestConfigReadmeExists` class verifies README existence but does not validate:
- All CLI examples in README are syntactically correct
- Quick start command actually works

**Recommendation:** Consider adding a test that extracts and validates CLI examples from README.

### 2. Missing Test for random_seed Consistency
**File:** `tests/integration/test_sample_configs.py`

All sample configs use `random_seed: 42` for reproducibility. There's no test verifying that running the same config twice produces identical results.

**Recommendation:** Add a determinism test:

```python
def test_seed_produces_reproducible_results(self) -> None:
    """Verify that running with same seed produces same results."""
    config = load_config(CONFIGS_DIR / "basic_strategy.yaml")
    config.simulation.num_sessions = 5
    config.simulation.hands_per_session = 10
    # Run twice and compare
    results1 = run_simulation(config)
    results2 = run_simulation(config)
    assert results1.aggregate.total_hands == results2.aggregate.total_hands
```

### 3. Type Checking Import Cleanup Not Tested
**Files:** `src/let_it_ride/simulation/controller.py:1133-1146`, `src/let_it_ride/simulation/parallel.py:1150-1167`

The code changes moving imports to `TYPE_CHECKING` blocks are good practice but the PR tests do not verify these modules still function correctly. This is covered by existing tests but worth noting.

## Recommendations

1. **Priority 1:** Add minimal simulation execution tests for each sample config to catch runtime incompatibilities

2. **Priority 2:** Add property-based testing using `hypothesis` library to generate edge-case configurations and verify they either validate correctly or produce clear error messages

3. **Priority 3:** Add comparative tests between related configs (conservative vs aggressive, basic vs progressive) to ensure documented differences are enforced

4. **Priority 4:** Consider adding a smoke test that runs the CLI `validate` command against each sample config to test the user-facing validation path

### Test Structure Observation

The test file is well-organized with clear class groupings per config file. The parametrized tests for common validations (existence, loading, simulation settings, bankroll settings) are an efficient pattern. Consider extracting the repeated `load_config(CONFIGS_DIR / config_file)` pattern into a fixture to reduce redundancy and improve test performance through caching.
