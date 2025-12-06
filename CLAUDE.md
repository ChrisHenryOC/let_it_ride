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

# CLI (run/validate commands not yet implemented)
poetry run let-it-ride --version
# poetry run let-it-ride run configs/basic_strategy.yaml  # TODO: LIR-35
# poetry run let-it-ride validate configs/sample_config.yaml  # TODO: LIR-35
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
- `table`: num_seats (1-6 for multi-player simulation)
- `dealer`: discard_enabled, discard_cards (burn cards before community)
- `deck`: shuffle_algorithm (fisher_yates/cryptographic)
- `bankroll`: starting_amount, base_bet, stop_conditions, betting_system
- `strategy`: type (basic/always_ride/always_pull/conservative/aggressive/custom)
- `bonus_strategy`: type (never/always/static/bankroll_conditional)
- `paytables`: main_game and bonus payout tables
- `output`: directory, formats (csv/json/html), visualizations

## Performance Targets

- Throughput: ≥100,000 hands/second
- Memory: <4GB RAM for 10M hands
- Hand evaluation accuracy: 100%

## GitHub CLI Tips

### Posting PR Inline Comments

Use `position` (integer) not `line` or `subject_type`. The position is the line number **within the diff hunk**, not the file line number.

**Calculating the correct position:**

1. Save the PR diff: `gh pr diff PR_NUMBER > /tmp/pr.diff`
2. Find where the target file's diff starts (look for `diff --git a/path/to/file`)
3. Find the `@@` hunk header line number in the combined diff
4. Calculate: `position = target_line_in_diff - hunk_header_line`

**Example:** If a file's `@@` line is at line 182 in the diff, and you want to comment on what appears at line 223, the position is `223 - 181 = 42` (the @@ line itself is position 1).

```bash
# First, examine the diff to find correct positions
gh pr diff PR_NUMBER > /tmp/pr.diff
cat -n /tmp/pr.diff | grep -A 5 "the code you want to comment on"

# Then post with the calculated position
gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments \
  --method POST \
  -f body="Comment text" \
  -f path="path/to/file.py" \
  -f commit_id="$(gh pr view PR_NUMBER --json headRefOid -q .headRefOid)" \
  -F position=42
```

**Important:**
- Use `-F position=42` (capital F) to pass as integer, not `-f position=42` (string)
- The position is relative to the diff hunk, NOT the absolute file line number
- Always verify positions by examining the actual diff output before posting comments

### Responding to PR Review Comments

When making changes in response to a PR review comment (especially those tagged with `@claude`):

1. Make the requested code changes
2. **Reply to the original comment** explaining what was changed
3. Commit and push the changes

To reply to an inline comment:

```bash
# Find the comment ID
gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments --jq '.[] | {id, body: .body[:50]}'

# Reply to the comment
gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments/COMMENT_ID/replies \
  --method POST \
  -f body="Done. Updated X to do Y. See commit abc123."
```

Keep replies concise - briefly state what was changed and reference the commit if helpful.

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
