# Documentation Accuracy Review: PR 150 - Reorganize Configs Folder Structure

## Summary

This PR reorganizes the configs folder by moving example configurations to `configs/examples/` and adding a new `configs/walkaway/` directory with 51 walk-away strategy research configurations. The `configs/README.md` was updated to reflect the new structure, and a new `configs/walkaway/README.md` was added with comprehensive documentation. However, the PR does not update numerous external documentation files that still reference the old paths (e.g., `configs/basic_strategy.yaml` instead of `configs/examples/basic_strategy.yaml`), resulting in multiple stale path references throughout the project.

## Findings by Severity

### Critical

None.

### High

#### H1: CLAUDE.md references stale config paths

**File:** `/Users/chrishenry/source/let_it_ride/CLAUDE.md:33-36`

The project's main Claude instructions file references the old config paths that no longer exist at the root `configs/` directory:

```markdown
poetry run let-it-ride run configs/basic_strategy.yaml
poetry run let-it-ride run configs/basic_strategy.yaml --quiet
poetry run let-it-ride run configs/basic_strategy.yaml --seed 42 --sessions 100
poetry run let-it-ride validate configs/sample_config.yaml
```

These should be updated to:
- `configs/examples/basic_strategy.yaml` for the first three
- `configs/sample_config.yaml` remains correct (sample_config.yaml was not moved)

#### H2: README.md references stale config paths

**File:** `/Users/chrishenry/source/let_it_ride/README.md:52-67`

The project's main README has multiple references to the old paths:

```markdown
poetry run let-it-ride run configs/basic_strategy.yaml
poetry run let-it-ride run configs/basic_strategy.yaml --output ./results --seed 42
poetry run let-it-ride run configs/basic_strategy.yaml --quiet
poetry run let-it-ride run configs/basic_strategy.yaml --verbose
poetry run let-it-ride run configs/basic_strategy.yaml --sessions 1000
```

These paths are now invalid since `basic_strategy.yaml` was moved to `configs/examples/`.

### Medium

#### M1: docs/quickstart.md references stale config paths

**File:** `/Users/chrishenry/source/let_it_ride/docs/quickstart.md:14-51`

Multiple CLI examples reference the old paths:

```markdown
poetry run let-it-ride run configs/basic_strategy.yaml
poetry run let-it-ride run configs/basic_strategy.yaml --sessions 1000
poetry run let-it-ride run configs/basic_strategy.yaml --seed 42
poetry run let-it-ride run configs/basic_strategy.yaml --output ./my_results
poetry run let-it-ride run configs/basic_strategy.yaml --quiet
```

Additionally, lines 56-65 list config files without the `examples/` subdirectory prefix.

#### M2: docs/installation.md references stale config paths

**File:** `/Users/chrishenry/source/let_it_ride/docs/installation.md:87-90`

The installation verification steps reference old paths:

```markdown
poetry run let-it-ride validate configs/sample_config.yaml
poetry run let-it-ride run configs/basic_strategy.yaml --sessions 100
```

Note: `sample_config.yaml` path is correct, but `basic_strategy.yaml` needs updating.

#### M3: docs/api.md references stale config paths

**File:** `/Users/chrishenry/source/let_it_ride/docs/api.md:262,343`

Code examples in the API documentation reference old paths:

```python
config = load_config("configs/basic_strategy.yaml")
config: SimulationConfig = load_config("configs/basic_strategy.yaml")
```

#### M4: docs/strategies.md references stale config paths

**File:** `/Users/chrishenry/source/let_it_ride/docs/strategies.md:218-224`

Strategy comparison examples reference old paths:

```bash
poetry run let-it-ride run configs/basic_strategy.yaml --output ./results/basic
poetry run let-it-ride run configs/conservative.yaml --output ./results/conservative
poetry run let-it-ride run configs/aggressive.yaml --output ./results/aggressive
```

#### M5: docs/examples.md references stale config path

**File:** `/Users/chrishenry/source/let_it_ride/docs/examples.md:328`

```bash
poetry run let-it-ride run configs/basic_strategy.yaml --sessions 50000 --seed 42 --output ./test_a
```

### Low

#### L1: walkaway/README.md references non-existent results file

**File:** `/Users/chrishenry/source/let_it_ride/configs/walkaway/README.md:24,140`

The walkaway README references `results/walkaway/ANALYSIS_SUMMARY.md` which does not exist in the repository. This appears to be a results file that would be generated after running simulations, but this may confuse users who expect it to exist.

Lines 140-143 also show a results directory structure that does not match the actual output directory paths specified in the config files (configs use flat `./results/walkaway/config_name` paths, not nested `results/walkaway/with_bonus/config_name` paths).

#### L2: walkaway/README.md file count descriptions could be more precise

**File:** `/Users/chrishenry/source/let_it_ride/configs/walkaway/README.md:90,96-98`

The README states `with_bonus/` contains 33 files with each bonus amount having 11 files. However:
- `bonus_5_*.yaml`: 10 files (tight, protect, chase, loose, asym_2x-5x, verytight_50, verytight_75)
- `bonus_15_*.yaml`: 10 files (same pattern)
- `bonus_30_*.yaml`: 10 files (same pattern)
- `paroli_*_tight.yaml`: 3 files

This totals 33, but the breakdown showing "11 each" is misleading since there are also 3 paroli files not mentioned in the table.

#### L3: walkaway/README.md missing paroli strategy documentation

**File:** `/Users/chrishenry/source/let_it_ride/configs/walkaway/README.md:100-106`

The strategy variations list does not include the `paroli_*_tight.yaml` files that exist in `with_bonus/`. These 3 files (paroli_5_tight.yaml, paroli_15_tight.yaml, paroli_30_tight.yaml) are part of the 33-file count but not documented in the variations list.

### Info

#### I1: configs/README.md updates are well-structured

**File:** `/Users/chrishenry/source/let_it_ride/configs/README.md`

The updated configs/README.md properly documents the new directory structure, updates the quick start paths to use `configs/examples/`, and provides a clear overview table of the example configurations. This is a good model for how the other documentation files should be updated.

#### I2: New walkaway/README.md is comprehensive

**File:** `/Users/chrishenry/source/let_it_ride/configs/walkaway/README.md`

The new walkaway README provides excellent documentation including:
- Directory structure overview
- Key research findings with data
- Bash scripts for running configs by category
- Detailed breakdown of configuration patterns
- Expected output structure

## Files Requiring Updates (Not Modified by PR)

The following files contain stale references to the old config paths and should be updated:

| File | Lines with Stale Paths |
|------|------------------------|
| `/Users/chrishenry/source/let_it_ride/CLAUDE.md` | 33-35 |
| `/Users/chrishenry/source/let_it_ride/README.md` | 52-64 |
| `/Users/chrishenry/source/let_it_ride/docs/quickstart.md` | 14, 42, 45, 48, 51, 56-65 |
| `/Users/chrishenry/source/let_it_ride/docs/installation.md` | 90 |
| `/Users/chrishenry/source/let_it_ride/docs/api.md` | 262, 343 |
| `/Users/chrishenry/source/let_it_ride/docs/strategies.md` | 218, 221, 224 |
| `/Users/chrishenry/source/let_it_ride/docs/examples.md` | 328 |

## Recommendation

Before merging this PR, update all documentation files listed above to use the new path `configs/examples/basic_strategy.yaml` instead of `configs/basic_strategy.yaml`. The same applies to `conservative.yaml`, `aggressive.yaml`, and other moved config files. This ensures users following the documentation will not encounter "file not found" errors.
