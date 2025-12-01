# LIR-8: YAML Configuration Schema and Loader

**GitHub Issue:** [#11](https://github.com/ChrisHenryOC/let_it_ride/issues/11)
**Status:** In Progress

## Summary

Implement YAML configuration loading with validation using Pydantic models. This is a foundational issue that will enable all subsequent simulation configuration.

## Files to Create

1. `src/let_it_ride/config/models.py` - Pydantic models for all config sections
2. `src/let_it_ride/config/loader.py` - YAML loading and validation
3. `tests/unit/config/test_models.py` - Model validation tests
4. `tests/unit/config/test_loader.py` - Loader tests
5. `configs/sample_config.yaml` - Sample configuration demonstrating all options

## Configuration Sections

Based on the requirements doc (Section 5):

### 1. MetadataConfig
- `name`: str (optional)
- `description`: str (optional)
- `version`: str (optional)
- `author`: str (optional)
- `created`: str (optional)

### 2. SimulationConfig
- `num_sessions`: int (1 to 100M)
- `hands_per_session`: int (1 to 10,000)
- `random_seed`: int | None
- `workers`: int | Literal["auto"]
- `progress_interval`: int = 10000
- `detailed_logging`: bool = False

### 3. DeckConfig
- `shuffle_algorithm`: Literal["fisher_yates", "cryptographic"] = "fisher_yates"

### 4. BankrollConfig
- `starting_amount`: float > 0
- `base_bet`: float > 0
- `stop_conditions`: StopConditionsConfig
- `betting_system`: BettingSystemConfig

### 5. StopConditionsConfig
- `win_limit`: float | None
- `loss_limit`: float | None
- `max_hands`: int | None
- `max_duration_minutes`: int | None
- `stop_on_insufficient_funds`: bool = True

### 6. BettingSystemConfig
- `type`: Literal["flat", "proportional", "martingale", ...]
- Nested configs for each type

### 7. StrategyConfig
- `type`: Literal["basic", "always_ride", "always_pull", "conservative", "aggressive", "custom"]
- Nested configs for conservative, aggressive, custom types

### 8. BonusStrategyConfig
- `enabled`: bool
- `paytable`: str
- `limits`: BonusLimitsConfig
- `type`: Literal["never", "always", "static", ...]
- Nested configs for each type

### 9. PaytablesConfig
- `main_game`: MainGamePaytableConfig
- `bonus`: BonusPaytableConfig

### 10. OutputConfig
- `directory`: str
- `prefix`: str
- `timestamp_format`: str
- `formats`: OutputFormatsConfig
- `visualizations`: VisualizationsConfig
- `console`: ConsoleConfig

### 11. FullConfig (root)
- `metadata`: MetadataConfig
- `simulation`: SimulationConfig
- `deck`: DeckConfig
- `bankroll`: BankrollConfig
- `strategy`: StrategyConfig
- `bonus_strategy`: BonusStrategyConfig
- `paytables`: PaytablesConfig
- `output`: OutputConfig

## Implementation Notes

1. Use Pydantic v2 with `model_validator` for cross-field validation
2. All config sections should have sensible defaults where appropriate
3. Error messages should be descriptive and actionable
4. The loader should handle:
   - File not found
   - Invalid YAML syntax
   - Pydantic validation errors with context

## Test Cases

### Valid Configurations
- Minimal config (all defaults)
- Full config with all options specified
- Various strategy types
- Various betting systems

### Invalid Configurations
- Missing required fields
- Out-of-range values
- Invalid enum values
- Type mismatches
- Cross-field validation failures (e.g., bet > bankroll)

## Dependencies

- LIR-1 (Project Scaffolding) - COMPLETE
- PyYAML (add to pyproject.toml)
