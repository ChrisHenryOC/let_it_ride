# Test Coverage Review: PR 150 - Reorganize Configs Folder Structure

## Summary

This PR reorganizes the `configs/` directory by moving example configurations into `configs/examples/` and adding a new `configs/walkaway/` directory with 51 configuration files for walk-away strategy research. **Critical test failures will occur** because existing tests hardcode paths that reference the old config locations (e.g., `configs/basic_strategy.yaml`), but these files have been moved to `configs/examples/basic_strategy.yaml`. The tests have not been updated to reflect the new directory structure.

## Findings

### Critical

**C1: Integration tests hardcode old config paths that no longer exist**

**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_sample_configs.py:30-37`

The `SAMPLE_CONFIG_FILES` list references config files at the root of `configs/`, but these have been moved to `configs/examples/`:

```python
SAMPLE_CONFIG_FILES = [
    "basic_strategy.yaml",      # Now at configs/examples/basic_strategy.yaml
    "conservative.yaml",         # Now at configs/examples/conservative.yaml
    "aggressive.yaml",           # Now at configs/examples/aggressive.yaml
    "bonus_comparison.yaml",     # Now at configs/examples/bonus_comparison.yaml
    "progressive_betting.yaml",  # Now at configs/examples/progressive_betting.yaml
    "sample_config.yaml",        # Still at configs/sample_config.yaml (OK)
]
```

This will cause 33+ test failures across:
- `TestSampleConfigsExist::test_config_file_exists` (5 failures)
- `TestSampleConfigsLoad::test_config_loads_successfully` (5 failures)
- `TestSampleConfigsLoad::test_config_has_valid_simulation` (5 failures)
- `TestSampleConfigsLoad::test_config_has_valid_bankroll` (5 failures)
- `TestBasicStrategyConfig` class (4 failures)
- `TestConservativeConfig` class (3 failures)
- `TestAggressiveConfig` class (3 failures)
- `TestBonusComparisonConfig` class (4 failures)
- `TestProgressiveBettingConfig` class (3 failures)
- `TestSampleConfigsRunSimulation` class (7 failures)
- `TestMalformedConfigs` class (3 failures)
- `TestConfigRelationships` class (3 failures)

---

**C2: E2E tests also hardcode old config paths**

**File:** `/Users/chrishenry/source/let_it_ride/tests/e2e/test_sample_configs.py:25-32`

Same issue as C1 - the `SAMPLE_CONFIG_FILES` list needs updating:

```python
SAMPLE_CONFIG_FILES = [
    "basic_strategy.yaml",
    "conservative.yaml",
    "aggressive.yaml",
    "bonus_comparison.yaml",
    "progressive_betting.yaml",
    "sample_config.yaml",
]
```

This will cause 20+ E2E test failures including:
- `TestSampleConfigsExecution` (3 parameterized tests x 6 configs)
- `TestSampleConfigsReproducibility` (1 parameterized test x 6 configs)
- `TestSampleConfigsParallel` (2 parameterized tests x 6 configs)
- `TestSpecificConfigValidation` (5 tests)
- `TestSampleConfigsLargeScale` (2 tests)

---

### High

**H1: Missing integration tests for new walkaway config directory**

**File:** N/A (missing tests)

The PR adds 51 new configuration files in `configs/walkaway/` subdirectories:
- `configs/walkaway/betting_systems/` (3 files)
- `configs/walkaway/no_bonus/` (15 files)
- `configs/walkaway/with_bonus/` (33 files)

There are no tests validating that:
1. These configuration files load without errors
2. The configurations are schema-valid
3. The configurations can execute minimal simulations

**Recommendation:** Add parameterized tests for walkaway configs similar to existing sample config tests:

```python
WALKAWAY_CONFIG_FILES = [
    "walkaway/betting_systems/martingale_nobonus_tight.yaml",
    "walkaway/betting_systems/fibonacci_nobonus_tight.yaml",
    "walkaway/betting_systems/dalembert_nobonus_tight.yaml",
    # ... remaining files
]

@pytest.mark.parametrize("config_file", WALKAWAY_CONFIG_FILES)
def test_walkaway_config_loads(config_file: str) -> None:
    config = load_config(CONFIGS_DIR / config_file)
    assert isinstance(config, FullConfig)
```

---

**H2: No test for README.md mentions updated config paths**

**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_sample_configs.py:247-258`

The `test_readme_mentions_all_configs` test checks if `configs/README.md` mentions all config files. However, the README has been updated to reference the new `examples/` subdirectory. The test should verify that the README mentions the correct paths:

```python
def test_readme_mentions_all_configs(self) -> None:
    """Test that README.md mentions all config files."""
    readme_path = CONFIGS_DIR / "README.md"
    content = readme_path.read_text().lower()

    for config_file in SAMPLE_CONFIG_FILES:
        # Currently checks for file basename
        # Should also verify examples/ path for moved files
```

---

### Medium

**M1: Fixtures referencing old config paths**

**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_sample_configs.py:97`

Class-level fixtures hardcode paths to config files:

```python
@pytest.fixture(scope="class")
def config(self) -> FullConfig:
    """Load basic_strategy.yaml once per test class."""
    return load_config(CONFIGS_DIR / "basic_strategy.yaml")  # Path broken
```

Same pattern repeated at:
- Line 123: `CONFIGS_DIR / "conservative.yaml"`
- Line 147: `CONFIGS_DIR / "aggressive.yaml"`
- Line 169: `CONFIGS_DIR / "bonus_comparison.yaml"`
- Line 216: `CONFIGS_DIR / "progressive_betting.yaml"`

---

**M2: No test coverage for new configs/walkaway/README.md**

**File:** `/Users/chrishenry/source/let_it_ride/configs/walkaway/README.md` (new file)

A new README.md was added to the walkaway directory with documentation about the research configurations. There is no test verifying:
1. The README exists
2. The README is not empty
3. The README correctly describes the walkaway configs

---

### Low

**L1: Multi-seat config moved but no specific test for new location**

**File:** `configs/examples/multi_seat_example.yaml`

The `multi_seat_example.yaml` was moved from `configs/` to `configs/examples/`. While this file is not in `SAMPLE_CONFIG_FILES`, the integration test `tests/integration/test_multi_seat.py` may have implicit dependencies or developers may expect it to be tested.

---

### Info

**I1: Large number of new config files without explicit test coverage**

The PR adds 51 new YAML configuration files. While these are research/example configurations, having at least basic schema validation tests would ensure they remain valid as the config schema evolves.

**I2: Config README documentation updated correctly**

The main `configs/README.md` has been updated with correct paths (`configs/examples/basic_strategy.yaml`) and documents the new directory structure properly.

---

## Recommended Actions

1. **[Critical]** Update `tests/integration/test_sample_configs.py`:
   - Change `SAMPLE_CONFIG_FILES` to use `examples/` prefix for moved files
   - Update all fixture paths referencing moved configs

2. **[Critical]** Update `tests/e2e/test_sample_configs.py`:
   - Same changes as integration tests

3. **[High]** Add new test file `tests/integration/test_walkaway_configs.py`:
   - Parameterized tests for all 51 walkaway config files
   - Basic load and validation tests

4. **[Medium]** Add test for walkaway README.md existence and content

5. **[Low]** Run full test suite to verify no other implicit path dependencies exist
