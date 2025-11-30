# Issue #4: Project Scaffolding and Development Environment

**Issue Link:** https://github.com/ChrisHenryOC/let_it_ride/issues/4

## Overview

This issue sets up the foundational Python project structure using Poetry, configures development tooling (pytest, mypy, ruff), and establishes the package hierarchy.

## Acceptance Criteria

- [ ] Poetry project initialized with Python 3.10+ requirement
- [ ] Package structure created (`src/let_it_ride/` with subpackages)
- [ ] pytest configured with coverage reporting
- [ ] mypy configured with strict type checking
- [ ] ruff configured for linting
- [ ] Basic `__init__.py` files with version info
- [ ] README.md with project description
- [ ] `make` or `just` commands for common tasks (test, lint, format)

## Files to Create

1. `pyproject.toml` - Poetry project configuration with all dependencies and tool configs
2. `src/let_it_ride/__init__.py` - Main package with version info
3. `src/let_it_ride/core/__init__.py` - Game engine subpackage
4. `src/let_it_ride/strategy/__init__.py` - Strategy implementations subpackage
5. `src/let_it_ride/bankroll/__init__.py` - Bankroll management subpackage
6. `src/let_it_ride/simulation/__init__.py` - Simulation orchestration subpackage
7. `src/let_it_ride/analytics/__init__.py` - Statistics and reporting subpackage
8. `src/let_it_ride/config/__init__.py` - Configuration handling subpackage
9. `tests/conftest.py` - pytest configuration and fixtures
10. `Makefile` - Common development commands

## Implementation Plan

### Step 1: Create pyproject.toml
- Initialize Poetry project
- Set Python >=3.10 requirement
- Add dependencies:
  - Core: `pydantic` (config validation), `pyyaml` (config loading)
  - Dev: `pytest`, `pytest-cov`, `mypy`, `ruff`
  - Visualization (optional): `matplotlib`, `plotly`
  - CLI: `typer` or `click`, `rich`
- Configure tool settings inline

### Step 2: Create Package Structure
- Create all directories
- Add `__init__.py` files with docstrings and version info

### Step 3: Configure Testing
- Create `tests/conftest.py` with basic fixtures
- Configure pytest in pyproject.toml

### Step 4: Create Makefile
Commands to include:
- `make install` - Install dependencies
- `make test` - Run pytest with coverage
- `make lint` - Run ruff check
- `make format` - Run ruff format
- `make typecheck` - Run mypy
- `make all` - Run all checks

### Step 5: Update README.md
- Add project description
- Add installation instructions
- Add usage instructions
- Add development commands

## Technical Decisions

1. **Poetry** for dependency management (as specified in CLAUDE.md)
2. **src layout** for cleaner imports and testing
3. **ruff** for linting (fast, comprehensive)
4. **mypy strict mode** for type safety
5. **Makefile** (vs justfile) for broad compatibility

## Dependencies

None - this is the first issue.

## Estimated Scope

~150 lines of configuration
