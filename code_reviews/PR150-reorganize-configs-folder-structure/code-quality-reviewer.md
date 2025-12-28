# Code Quality Review: PR150 - Reorganize Configs Folder Structure

## Summary

This PR reorganizes the configs folder by moving example configurations into an `examples/` subdirectory and creating a new `walkaway/` directory structure with 51 research configuration files. The folder reorganization is well-structured with clear categorization, though there are several documentation inconsistencies and opportunities to reduce duplication across the highly repetitive YAML files.

## Findings

### Medium

#### M1: Documentation Inconsistency - File Count Mismatch
**File:** `configs/walkaway/README.md:9-11`

The README states the file count as:
- `with_bonus/`: 33 configs
- `no_bonus/`: 15 configs
- `betting_systems/`: 3 configs
- **Total: 51 configs**

However, the actual file counts are:
- `with_bonus/`: 33 configs (correct)
- `no_bonus/`: 15 configs (correct)
- `betting_systems/`: 3 configs (correct)

The total is correct (51), but the `with_bonus/` README table claims:
```markdown
| `bonus_5_*.yaml` | $5 bonus bet strategies | 11 |
| `bonus_15_*.yaml` | $15 bonus bet strategies | 11 |
| `bonus_30_*.yaml` | $30 bonus bet strategies | 11 |
```

This sums to 33, which is correct. However, it omits the Paroli betting configs (`paroli_5_tight.yaml`, `paroli_15_tight.yaml`, `paroli_30_tight.yaml`) from the table, which are included in the 33 count but not documented.

**Recommendation:** Add a row for Paroli configs or update the table to accurately reflect all file patterns.

---

#### M2: Output Directory Structure Inconsistency
**File:** `configs/walkaway/README.md:139-143`

The README example shows nested output directories:
```
results/walkaway/
├── with_bonus/bonus_5_tight/
├── no_bonus/no_bonus_tight_100/
```

But the actual YAML configs use flat directories:
```yaml
output:
  directory: "./results/walkaway/bonus_5_tight"
  directory: "./results/walkaway/no_bonus_tight_100"
```

The results directories do not mirror the config file organization (`with_bonus/`, `no_bonus/`, `betting_systems/`).

**Recommendation:** Either update the README to reflect the actual flat structure, or update the configs to use nested output directories that match the source config organization.

---

#### M3: Paroli Configs Placed in Wrong Directory
**Files:**
- `configs/walkaway/with_bonus/paroli_5_tight.yaml`
- `configs/walkaway/with_bonus/paroli_15_tight.yaml`
- `configs/walkaway/with_bonus/paroli_30_tight.yaml`

Paroli is a betting system (like Martingale, D'Alembert, Fibonacci). The other betting system configs are correctly placed in `betting_systems/`, but the Paroli configs are in `with_bonus/` because they also use bonus bets. This creates organizational ambiguity.

The `betting_systems/` README states:
```markdown
Alternative betting progressions (no bonus)
```

So the placement is technically correct, but the naming pattern `paroli_*_tight.yaml` in `with_bonus/` breaks the pattern where files match `bonus_*_*.yaml`.

**Recommendation:** Consider either:
1. Moving Paroli to `betting_systems/` with bonus enabled, updating the README to reflect that betting systems can have bonuses
2. Renaming to follow the `bonus_*_paroli.yaml` pattern for consistency

---

### Low

#### L1: Inconsistent Visualization Settings Across Similar Configs
**Files:** Multiple walkaway configs

Some configs have visualizations enabled while others have them disabled, without clear rationale:

```yaml
# Enabled: no_bonus_tight_100.yaml, no_bonus_verytight_50.yaml, no_bonus_verytight_75.yaml
# Enabled: All bonus_*_asym_*.yaml, bonus_*_chase.yaml, etc.
# Disabled: All betting_systems/*.yaml, bankroll_*.yaml, basebet_*.yaml
```

**Recommendation:** Document the rationale or standardize visualization settings. If visualizations are only needed for key comparison configs, document this in the README.

---

#### L2: num_sessions Inconsistency in Example Config
**File:** `configs/examples/bonus_5_dollar.yaml:14`

The diff shows this file is modified to change `num_sessions` from 100000 to 10000:
```yaml
simulation:
  num_sessions: 10000  # Changed from 100000
```

All walkaway configs use 100000 sessions, while this example uses 10000. The discrepancy is intentional (examples should be fast to run), but could cause confusion when comparing results.

**Recommendation:** Add a comment explaining the lower session count is for quick demonstrations.

---

#### L3: Same Random Seed Used Across All Configs
**Files:** All 51 walkaway config files

All configs use `random_seed: 42`. While this is fine for reproducibility within a single config, it means cross-config comparisons may have correlated randomness.

```yaml
simulation:
  random_seed: 42  # Same across all files
```

**Recommendation:** If comparative analysis is a goal, consider using unique seeds per config (e.g., based on config name hash) or document that the same seed is intentional for baseline comparison.

---

### Info

#### I1: Good Folder Structure Organization
The new structure is logical and well-organized:
```
configs/
├── README.md
├── sample_config.yaml
├── examples/
└── walkaway/
    ├── with_bonus/
    ├── no_bonus/
    └── betting_systems/
```

This separation of concerns (reference config, examples, research configs) improves discoverability.

---

#### I2: Excellent README Documentation
**Files:** `configs/README.md`, `configs/walkaway/README.md`

Both READMEs provide:
- Clear directory structure overview
- Quick start examples
- Tables describing config purposes
- Shell scripts for batch running
- Research findings summary

---

#### I3: Consistent YAML Formatting
All new YAML files follow consistent formatting:
- Section header comments with `# =============================================================================`
- Consistent indentation (2 spaces)
- Clear section separators with `# -----------------------------------------------------------------------------`
- Descriptive metadata blocks

---

#### I4: Significant Config Duplication (Maintainability Consideration)
The 51 walkaway configs share approximately 90% of their content. While YAML anchors could reduce duplication, the current approach has trade-offs:

**Pros of current approach:**
- Each config is self-contained and readable
- No YAML anchor complexity
- Easy to copy and modify individual files

**Cons:**
- Updates to common settings (e.g., changing default paytable) require editing 51 files
- ~4500 lines of repetitive YAML

Future consideration: A base config + override pattern using YAML anchors or a config generation script could reduce maintenance burden.

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 3 |
| Low | 3 |
| Info | 4 |

## Files Reviewed

- `configs/README.md` (modified)
- `configs/walkaway/README.md` (new)
- `configs/examples/*.yaml` (renamed from `configs/*.yaml`)
- `configs/walkaway/with_bonus/*.yaml` (33 new files)
- `configs/walkaway/no_bonus/*.yaml` (15 new files)
- `configs/walkaway/betting_systems/*.yaml` (3 new files)
