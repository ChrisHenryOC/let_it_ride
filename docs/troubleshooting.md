# Troubleshooting

Common issues and solutions.

## Installation Issues

### Poetry not found

**Problem:** `poetry: command not found`

**Solution:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Add to shell config (~/.bashrc or ~/.zshrc)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Python version error

**Problem:** `Python 3.10 or higher required`

**Solution:**
```bash
# Check version
python --version

# Install Python 3.10+ using pyenv
pyenv install 3.10.0
pyenv local 3.10.0

# Or use your system package manager
# macOS: brew install python@3.10
# Ubuntu: sudo apt install python3.10
```

### Dependency conflicts

**Problem:** `SolverProblemError` during `poetry install`

**Solution:**
```bash
# Clear cache and reinstall
poetry cache clear pypi --all
poetry env remove --all
poetry install
```

## Configuration Errors

### Invalid YAML syntax

**Problem:** `yaml.scanner.ScannerError`

**Solution:** Check YAML formatting:
- Use spaces, not tabs
- Proper indentation (2 spaces)
- Quote strings with special characters

Validate your config:
```bash
poetry run let-it-ride validate config.yaml
```

### Unknown configuration key

**Problem:** `Extra inputs are not permitted`

**Solution:** Check spelling of configuration keys. Refer to [Configuration Reference](configuration.md).

### Invalid value range

**Problem:** `Value error, num_sessions must be >= 1`

**Solution:** Check value ranges:
- `num_sessions`: 1 - 100,000,000
- `hands_per_session`: 1 - 10,000
- `num_seats`: 1 - 6
- `base_bet`: > 0
- `starting_amount`: > 0

## Runtime Errors

### Out of memory

**Problem:** Process killed or `MemoryError`

**Solution:**
```yaml
# Reduce memory usage
simulation:
  num_sessions: 1000000  # Reduce from larger number
  workers: 1             # Single worker uses less memory

output:
  formats:
    csv:
      include_hands: false     # Don't store per-hand data
      include_sessions: false  # Don't store per-session data
```

### Simulation too slow

**Problem:** Simulation taking hours

**Solution:**
```yaml
# Enable parallel execution
simulation:
  workers: auto  # Use all CPU cores

# Or specify cores
simulation:
  workers: 8
```

Check CPU usage during simulation to ensure parallelization is working.

### Reproducibility issues

**Problem:** Different results with same seed

**Solution:**
```yaml
# Ensure deterministic settings
simulation:
  random_seed: 42
  workers: 1  # Parallel execution can affect ordering

deck:
  shuffle_algorithm: fisher_yates
  use_crypto: false  # Cryptographic seeding is non-deterministic
```

## Output Issues

### No output files generated

**Problem:** Results directory is empty

**Solution:**
```yaml
# Check output is enabled
output:
  formats:
    csv:
      enabled: true
    json:
      enabled: true
```

Check the output directory path exists:
```bash
ls -la ./results/
```

### Charts not generating

**Problem:** `ModuleNotFoundError: No module named 'matplotlib'`

**Solution:**
```bash
# Install visualization dependencies
poetry install --with viz
```

### Large output files

**Problem:** Output files are gigabytes in size

**Solution:**
```yaml
# Disable detailed output
output:
  formats:
    csv:
      include_hands: false      # Per-hand data is very large
      include_sessions: false   # Per-session can also be large
      include_aggregate: true   # Just keep aggregate stats
```

## Strategy Issues

### Custom strategy not working

**Problem:** Custom conditions not matching

**Solution:** Debug by testing conditions:
```yaml
strategy:
  type: custom
  custom:
    bet1_rules:
      # Add debug condition first to see what's matching
      - condition: "has_paying_hand"
        action: "ride"
      - condition: "default"  # Always matches
        action: "pull"
```

Check available conditions in [Strategies Guide](strategies.md).

### Invalid condition syntax

**Problem:** `ConditionParseError`

**Solution:** Check condition syntax:
- Boolean conditions: `has_paying_hand`, `is_flush_draw`
- Comparisons: `high_cards >= 2`, `session_profit > 50`
- Compound: `is_flush_draw and high_cards >= 2`

Valid operators: `and`, `or`, `>=`, `<=`, `>`, `<`, `==`

## Performance Issues

### Not achieving target throughput

**Problem:** Less than 100,000 hands/second

**Solution:**
1. Enable parallel execution: `workers: auto`
2. Disable detailed logging: `detailed_logging: false`
3. Disable per-hand output: `include_hands: false`
4. Use Fisher-Yates shuffle (faster): `shuffle_algorithm: fisher_yates`

### High memory during parallel execution

**Problem:** Memory spikes with many workers

**Solution:**
```yaml
simulation:
  workers: 4  # Reduce from auto
```

## Getting Help

### Check version

```bash
poetry run let-it-ride --version
```

### Verbose mode

```bash
poetry run let-it-ride run config.yaml --verbose
```

### Validate configuration

```bash
poetry run let-it-ride validate config.yaml
```

### Run tests

```bash
poetry run pytest -v
```

### Report issues

File issues at: https://github.com/ChrisHenryOC/let_it_ride/issues

Include:
- Python version
- Operating system
- Configuration file (sanitized)
- Full error message
- Steps to reproduce
