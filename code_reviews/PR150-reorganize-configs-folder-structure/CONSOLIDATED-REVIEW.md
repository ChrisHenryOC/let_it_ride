# Consolidated Review for PR #150

## Summary

This PR reorganizes the `configs/` folder by moving example configurations to `configs/examples/` and adding 51 new walk-away strategy research configurations under `configs/walkaway/`. While the folder structure is well-organized and includes comprehensive documentation, the PR has **critical issues** with test paths that will cause test failures, and **high-severity documentation issues** with stale path references across multiple project files.

## Issue Matrix

| # | Severity | Issue | File:Line | Reviewer(s) | In PR Scope? | Actionable? |
|---|----------|-------|-----------|-------------|--------------|-------------|
| 1 | Critical | Integration tests hardcode old config paths - will cause 33+ test failures | `tests/integration/test_sample_configs.py:30-37` | Test Coverage | No | Yes |
| 2 | Critical | E2E tests hardcode old config paths - will cause 20+ test failures | `tests/e2e/test_sample_configs.py:25-32` | Test Coverage | No | Yes |
| 3 | High | CLAUDE.md references stale config paths | `CLAUDE.md:33-35` | Documentation | No | Yes |
| 4 | High | README.md references stale config paths | `README.md:52-67` | Documentation | No | Yes |
| 5 | High | Missing integration tests for 51 new walkaway configs | N/A | Test Coverage | No | No |
| 6 | Medium | Paroli config files undocumented in walkaway README | `configs/walkaway/README.md:96-98` | Code Quality, Documentation | Yes | Yes |
| 7 | Medium | Output directory structure in README doesn't match actual configs | `configs/walkaway/README.md:139-143` | Code Quality | Yes | Yes |
| 8 | Medium | Paroli configs placed in with_bonus/ instead of betting_systems/ | `configs/walkaway/with_bonus/paroli_*.yaml` | Code Quality | Yes | Yes |
| 9 | Medium | docs/quickstart.md references stale config paths | `docs/quickstart.md:14-51` | Documentation | No | Yes |
| 10 | Medium | docs/installation.md references stale config path | `docs/installation.md:90` | Documentation | No | Yes |
| 11 | Medium | docs/api.md references stale config paths | `docs/api.md:262,343` | Documentation | No | Yes |
| 12 | Medium | docs/strategies.md references stale config paths | `docs/strategies.md:218-224` | Documentation | No | Yes |
| 13 | Medium | docs/examples.md references stale config path | `docs/examples.md:328` | Documentation | No | Yes |
| 14 | Medium | Test fixtures hardcode old config paths | `tests/integration/test_sample_configs.py:97,123,147,169,216` | Test Coverage | No | Yes |
| 15 | Low | Inconsistent visualization settings across configs | Various walkaway configs | Code Quality | Yes | Yes |
| 16 | Low | num_sessions reduced in example config without comment | `configs/examples/bonus_5_dollar.yaml:14` | Code Quality | Yes | Yes |
| 17 | Low | Same random seed (42) used across all 51 configs | All walkaway configs | Code Quality | Yes | No |
| 18 | Low | walkaway README references non-existent results file | `configs/walkaway/README.md:24` | Documentation | Yes | Yes |

## Actionable Issues

Issues where both "In PR Scope" AND "Actionable" are Yes:

| # | Issue | Recommendation |
|---|-------|----------------|
| 6 | Paroli config files undocumented | Add paroli files to the walkaway README table |
| 7 | Output directory structure mismatch | Update README to show flat structure matching actual configs |
| 8 | Paroli configs organization | Either move to betting_systems/ or rename to follow bonus_* pattern |
| 15 | Inconsistent visualizations | Document rationale or standardize settings |
| 16 | Reduced num_sessions | Add comment explaining lower count for demo purposes |
| 18 | Non-existent results file reference | Update README to clarify this is generated output |

## Deferred Issues

Issues where either "In PR Scope" OR "Actionable" is No:

| # | Issue | Reason for Deferral |
|---|-------|---------------------|
| 1-2 | Test file path updates | Tests not in PR scope but **MUST be fixed** before merge |
| 3-4 | Project README/CLAUDE.md updates | Not in PR scope but **MUST be fixed** before merge |
| 5 | Missing tests for new configs | Requires new test file creation |
| 9-13 | Docs updates | Files not in PR scope but **SHOULD be fixed** before merge |
| 14 | Test fixture path updates | Tests not in PR scope but **MUST be fixed** before merge |
| 17 | Same random seed | Design decision, document if intentional |

## Reviewer Summary

| Reviewer | Critical | High | Medium | Low | Info |
|----------|----------|------|--------|-----|------|
| Code Quality | 0 | 0 | 3 | 3 | 4 |
| Performance | 0 | 0 | 0 | 0 | 4 |
| Test Coverage | 2 | 2 | 2 | 1 | 2 |
| Documentation | 0 | 2 | 5 | 3 | 2 |
| Security | 0 | 0 | 0 | 0 | 3 |

## Recommendation

**Do not merge** until the following are addressed:

1. **Critical**: Update test files to use new `configs/examples/` paths
   - `tests/integration/test_sample_configs.py`
   - `tests/e2e/test_sample_configs.py`

2. **High**: Update documentation with new paths
   - `CLAUDE.md`
   - `README.md`
   - `docs/quickstart.md`
   - `docs/installation.md`
   - `docs/api.md`
   - `docs/strategies.md`
   - `docs/examples.md`

3. **Optional improvements**:
   - Fix walkaway README documentation gaps (paroli files, output structure)
   - Add tests for new walkaway config files
