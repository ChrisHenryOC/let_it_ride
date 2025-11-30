# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Let It Ride Strategy Simulator - a Python application to simulate the casino card game "Let It Ride" and analyze play/betting strategies to identify approaches that maximize profitable session probability. The simulator supports millions of hands, configurable strategies, bankroll management, and statistical analysis.

## Development Status

This is a greenfield project. See `docs/let_it_ride_implementation_plan.md` for the 40-issue phased implementation plan and `docs/let_it_ride_requirements.md` for complete requirements.

## Commands

Once the project is scaffolded (Issue #1), these commands will be available:

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

# Run simulation (once CLI exists)
poetry run let-it-ride run configs/basic_strategy.yaml
poetry run let-it-ride validate configs/sample_config.yaml
```

## Architecture

```
src/let_it_ride/
├── core/           # Game engine: Card, Deck, Shoe, hand evaluators, game state
├── strategy/       # Strategy implementations: basic, baseline, custom, bonus
├── bankroll/       # Bankroll tracking and betting systems
├── simulation/     # Session management, parallel execution, RNG
├── analytics/      # Statistics, validation, export (CSV/JSON/HTML), visualizations
├── config/         # YAML configuration loading with Pydantic models
└── cli.py          # Command-line interface
```

Key abstractions:
- `Strategy` protocol: `decide_bet1()` and `decide_bet2()` methods for pull/ride decisions
- `BonusStrategy` protocol: `get_bonus_bet()` for three-card bonus betting
- `BettingSystem` protocol: betting progression systems (flat, Martingale, etc.)
- `GameEngine`: orchestrates deck, strategy, paytables for single hands
- `Session`: manages bankroll, stop conditions, runs hands to completion
- `SimulationController`: runs multiple sessions with optional parallelization

## Game Rules Summary

1. Player places 3 equal bets, receives 3 cards
2. **Decision 1**: After viewing 3 cards, pull Bet 1 or let it ride
3. First community card revealed (4 cards visible)
4. **Decision 2**: Pull Bet 2 or let it ride
5. Second community card revealed, hands pay per paytable
6. Optional Three Card Bonus: side bet on player's initial 3 cards

## Configuration

Simulations are configured via YAML files. Key sections:
- `simulation`: num_sessions, hands_per_session, random_seed, workers
- `deck`: num_decks (1/2/4/6/8), penetration
- `bankroll`: starting_amount, base_bet, stop_conditions, betting_system
- `strategy`: type (basic/always_ride/always_pull/conservative/aggressive/custom)
- `bonus_strategy`: type (never/always/static/bankroll_conditional/streak_based)
- `paytables`: main_game and bonus payout tables
- `output`: directory, formats (csv/json/html), visualizations

## Performance Targets

- Throughput: ≥100,000 hands/second
- Memory: <4GB RAM for 10M hands
- Hand evaluation accuracy: 100%
