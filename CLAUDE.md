# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Let It Ride Strategy Simulator - a Python application to simulate the casino card game "Let It Ride" and analyze play/betting strategies to identify approaches that maximize profitable session probability. The simulator supports millions of hands, configurable strategies, bankroll management, and statistical analysis.

## Development Status

This project is approximately 45% complete. Core game engine, strategies, betting systems, and session management are implemented. CLI execution, parallel simulation, and analytics/export features are in progress. See `docs/let_it_ride_implementation_plan.md` for the phased implementation plan and `docs/let_it_ride_requirements.md` for complete requirements.

## Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest
poetry run pytest tests/unit/  # unit tests only
poetry run pytest -k "test_name"  # single test

# Type checking
poetry run mypy src/

# Linting and formatting
poetry run ruff check src/ tests/
poetry run ruff format src/ tests/

# CLI commands
poetry run let-it-ride --version
poetry run let-it-ride run configs/basic_strategy.yaml
poetry run let-it-ride run configs/basic_strategy.yaml --quiet
poetry run let-it-ride run configs/basic_strategy.yaml --seed 42 --sessions 100
poetry run let-it-ride validate configs/sample_config.yaml
```

## Architecture

```
src/let_it_ride/
├── core/           # Game engine: Card, Deck, Table, hand evaluators, hand processing
├── strategy/       # Strategy implementations: basic, baseline, custom, bonus
├── bankroll/       # Bankroll tracking and betting systems
├── simulation/     # Session and TableSession management, parallel execution, RNG
├── analytics/      # Statistics, validation, export (CSV/JSON/HTML), visualizations
├── config/         # YAML configuration loading with Pydantic models
└── cli.py          # Command-line interface
```

Key abstractions:
- `Strategy` protocol: `decide_bet1()` and `decide_bet2()` methods for pull/ride decisions
- `BonusStrategy` protocol: `get_bonus_bet()` for three-card bonus betting
- `BettingSystem` protocol: betting progression systems (Flat, Martingale, Paroli, D'Alembert, Fibonacci, Reverse Martingale)
- `GameEngine`: orchestrates deck, strategy, paytables for single-player hands
- `Table`: multi-player table (1-6 seats) sharing community cards
- `Session`: manages bankroll, stop conditions, runs hands to completion
- `TableSession`: manages multi-seat table sessions with per-seat tracking
- `DealerConfig`: optional dealer discard (burn cards) before community cards

## Game Rules

Let It Ride: 3 equal bets, 3 player cards, 2 community cards. Two decision points to pull bets or let them ride. Pays on pair of 10s+. See `.claude/references/let-it-ride-game-rules.md` for full rules and paytables.

## Configuration

Simulations are configured via YAML files. Key sections:
- `simulation`: num_sessions, hands_per_session, random_seed, workers
- `table`: num_seats (1-6 for multi-player simulation)
- `dealer`: discard_enabled, discard_cards (burn cards before community)
- `deck`: shuffle_algorithm (fisher_yates/cryptographic), use_crypto (high-entropy seeds)
- `bankroll`: starting_amount, base_bet, stop_conditions, betting_system
- `strategy`: type (basic/always_ride/always_pull/conservative/aggressive/custom)
- `bonus_strategy`: type (never/always/static/bankroll_conditional)
- `paytables`: main_game and bonus payout tables
- `output`: directory, formats (csv/json/html), visualizations

### RNG Management

The `RNGManager` class provides centralized seed management for reproducible simulations:
- `use_crypto=True`: Use secrets module for high-entropy seeding (non-reproducible)
- `validate_rng_quality()`: Run chi-square uniformity and Wald-Wolfowitz runs tests
- State serialization supports checkpointing and resume

## Performance Targets

- Throughput: ≥100,000 hands/second
- Memory: <4GB RAM for 10M hands
- Hand evaluation accuracy: 100%

## GitHub CLI Tips

For PR inline comments, use `position` (diff line offset from `@@` header), not `line`. Use `-F` for integer values. See `.claude/memories/github-cli-pr-comments.md` for detailed syntax and examples.

## Issue Numbering Convention

**CRITICAL:** This project uses **LIR-prefixed identifiers** to distinguish implementation plan items from GitHub issue numbers. These are NOT the same:

- **LIR-N**: Implementation plan item number (e.g., "LIR-15" for Custom Strategy Configuration)
- **GitHub #N**: The actual GitHub issue number (e.g., GitHub #15 might be a completely different issue)

GitHub issue titles use the format `LIR-N: Title` (e.g., "LIR-12: Custom Strategy Configuration Parser").

### When the user requests work on an issue:

1. **If user says "LIR-N"**: Look up the GitHub issue by searching for the title prefix `LIR-N:` using `gh issue list --search "LIR-N in:title"`. Do NOT assume GitHub issue #N is the same as LIR-N.

2. **If user says "issue N" or "#N"**: Clarify whether they mean LIR-N (implementation plan) or GitHub #N (GitHub issue number).

3. **Always verify**: Before starting work, confirm you have the correct issue by checking the title contains the expected LIR identifier.

### Example:
- User says: "Work on LIR-15"
- Correct action: `gh issue list --search "LIR-15 in:title"` to find the GitHub issue
- WRONG action: Assuming GitHub issue #15 is what they want

When referencing issues:
- Use `LIR-4` when discussing the implementation plan item
- Use `GitHub #7` when discussing the GitHub issue itself
- Use `LIR-4 (GitHub #7)` when both contexts are relevant

## Scratchpads

Scratchpad files are placed in /scratchpads
