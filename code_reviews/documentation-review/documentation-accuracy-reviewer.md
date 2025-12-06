# Documentation Accuracy Review: README.md and CLAUDE.md

**Review Date:** 2025-12-06
**Files Reviewed:**
- `/Users/chrishenry/source/let_it_ride/README.md`
- `/Users/chrishenry/source/let_it_ride/CLAUDE.md`

---

## Summary

The README.md and CLAUDE.md files are generally accurate but contain several outdated sections and missing documentation for newer features. The most significant issues are:

1. **CLAUDE.md incorrectly describes the project as "greenfield"** when 22 of 49 implementation items are complete (45%)
2. **Multi-player table support (Table, TableSession) is not documented** in either file
3. **Dealer discard configuration is not documented** in README.md
4. **CLI commands are documented but the underlying functionality is marked as "not yet implemented"**
5. **Several bonus strategies are documented in config but not yet implemented in code**

---

## Findings by Severity

### Critical Issues

#### 1. CLAUDE.md Development Status is Inaccurate
**File:** `/Users/chrishenry/source/let_it_ride/CLAUDE.md`
**Lines:** 9-11

**Current State:**
```markdown
## Development Status

This is a greenfield project. See `docs/let_it_ride_implementation_plan.md` for the 40-issue phased implementation plan...
```

**Problem:** The project has 22 completed implementation items out of 49 total (45% complete). According to `docs/implementation_todo.md`, the project has completed:
- Core game components (Card, Deck, Hand Evaluation)
- Configuration system (YAML loader, Pydantic models)
- All betting systems (Flat, Martingale, Paroli, D'Alembert, Fibonacci, Reverse Martingale)
- Session management (Session, TableSession)
- Table abstraction for multi-player support
- Bonus strategies (Never, Always, Static, BankrollConditional)

**Recommendation:** Update to reflect the current state:
```markdown
## Development Status

This project is in active development (Phase 3.5 complete). Core game mechanics,
strategies, betting systems, and session management are implemented. Remaining work
includes simulation controller, analytics, and CLI integration. See
`docs/implementation_todo.md` for the 49-issue phased implementation plan with 22
completed, 25 remaining.
```

---

### High Severity Issues

#### 2. Multi-Player Table Support Not Documented
**Files:** README.md, CLAUDE.md
**Missing from both files**

**Problem:** The codebase includes significant multi-player support functionality:
- `src/let_it_ride/core/table.py` - Table class for multi-seat orchestration
- `src/let_it_ride/simulation/table_session.py` - TableSession for multi-player sessions
- `src/let_it_ride/config/models.py:95-107` - TableConfig with `num_seats` (1-6)

Neither README.md nor CLAUDE.md mentions this capability.

**Recommendation for README.md Features section:**
```markdown
- **Multi-Player Tables**: Support for 1-6 player seats with shared community cards
```

**Recommendation for CLAUDE.md Architecture section:**
Add to Key abstractions:
```markdown
- `Table`: orchestrates multiple player seats with shared deck/community cards
- `TableSession`: multi-player session management with per-seat bankroll tracking
- `TableConfig`: configuration for number of seats (1-6)
```

---

#### 3. Dealer Discard Configuration Not Documented
**File:** README.md:137-148 (Configuration section)
**Also missing from:** CLAUDE.md:68-77

**Problem:** The configuration system supports dealer discard mechanics via `DealerConfig`:
- `discard_enabled: bool` - Enable dealer discard before player deal
- `discard_cards: int` (1-10) - Number of cards dealer discards

This is implemented in `src/let_it_ride/config/models.py:77-93` but not documented in either README or CLAUDE.md.

**Recommendation:** Add to README.md Configuration section:
```markdown
- `dealer`: Dealer card handling (discard_enabled, discard_cards)
```

Add to CLAUDE.md Configuration section:
```markdown
- `dealer`: discard_enabled (boolean), discard_cards (1-10)
```

---

#### 4. CLI Commands Show "Not Yet Implemented"
**File:** README.md:42-55 (Usage section)
**Actual implementation:** `src/let_it_ride/cli.py:37-52`

**Problem:** README documents CLI commands as usable:
```bash
poetry run let-it-ride run configs/basic_strategy.yaml
poetry run let-it-ride validate configs/sample_config.yaml
```

But the actual implementation shows:
```python
@app.command()
def run(...) -> None:
    console.print("[yellow]Simulation not yet implemented[/yellow]")

@app.command()
def validate(...) -> None:
    console.print("[yellow]Validation not yet implemented[/yellow]")
```

**Recommendation:** Add a note to README.md Usage section:
```markdown
### Command Line Interface

> **Note:** CLI commands exist but simulation and validation functionality is not
> yet fully implemented. These commands are part of the phased development plan.
```

---

### Medium Severity Issues

#### 5. CLAUDE.md Architecture Missing "Shoe" Component
**File:** CLAUDE.md:40-48

**Current State:**
```markdown
├── core/           # Game engine: Card, Deck, Shoe, hand evaluators, game state
```

**Problem:** The "Shoe" component mentioned in the architecture description was cancelled (LIR-3 is marked as cancelled in implementation_todo.md). The Deck implementation handles single-deck play. Multi-deck shoe was deemed unnecessary.

**Recommendation:** Update architecture description:
```markdown
├── core/           # Game engine: Card, Deck, hand evaluators, game state, Table
```

---

#### 6. Missing Betting Systems in README Features
**File:** README.md:14

**Current State:**
```markdown
- **Bankroll Management**: Various betting progression systems (flat, Martingale, Paroli, etc.)
```

**Problem:** This is accurate but vague. The implemented systems are:
- Flat (constant bet)
- Martingale (double on loss)
- Reverse Martingale / Anti-Martingale (increase on win)
- Paroli (increase on win with reset)
- D'Alembert (add unit on loss, subtract on win)
- Fibonacci (Fibonacci sequence on loss)

All are implemented in `src/let_it_ride/bankroll/betting_systems.py`.

**Recommendation:** The current wording is acceptable but could be more specific:
```markdown
- **Bankroll Management**: Six betting progression systems (Flat, Martingale,
  Reverse Martingale, Paroli, D'Alembert, Fibonacci)
```

---

#### 7. Sample Config YAML Missing `table` and `dealer` Sections
**File:** `configs/sample_config.yaml`

**Problem:** The sample config demonstrates most configuration options but is missing:
- `table:` section with `num_seats` for multi-player configuration
- `dealer:` section with `discard_enabled` and `discard_cards`

**Recommendation:** Add these sections to sample_config.yaml after the `deck:` section:
```yaml
# ------------------------------------------------------------------
# DEALER - Dealer card handling mechanics
# ------------------------------------------------------------------
dealer:
  # Enable dealer discard before dealing community cards
  discard_enabled: false
  # Number of cards to discard (1-10, default 3)
  discard_cards: 3

# ------------------------------------------------------------------
# TABLE - Multi-player table configuration
# ------------------------------------------------------------------
table:
  # Number of player seats at the table (1-6)
  num_seats: 1
```

---

#### 8. CLAUDE.md Commands Section References Outdated Issue
**File:** CLAUDE.md:13-15

**Current State:**
```markdown
## Commands

Once the project is scaffolded (Issue #1), these commands will be available:
```

**Problem:** Issue #1 (LIR-1 Project Scaffolding) is complete. The phrasing suggests these commands are not yet available.

**Recommendation:**
```markdown
## Commands

The following commands are available:
```

---

### Low Severity Issues

#### 9. Bonus Strategies Implementation Status
**File:** README.md:13, CLAUDE.md:75

**Problem:** Documentation mentions these bonus strategy types:
- never, always, static, bankroll_conditional, streak_based, session_conditional, combined, custom

But `src/let_it_ride/strategy/bonus.py:368-376` shows:
```python
if strategy_type in (
    "streak_based",
    "session_conditional",
    "combined",
    "custom",
):
    raise NotImplementedError(
        f"Bonus strategy type '{strategy_type}' is not yet implemented"
    )
```

**Impact:** Low - the configuration models support these types for future implementation.

**Recommendation:** This is acceptable as documented since the config models support them. Could add a note that some strategies are planned but not yet implemented.

---

#### 10. CLAUDE.md Missing SimulationController Status
**File:** CLAUDE.md:55-57

**Current State:**
```markdown
Key abstractions:
...
- `SimulationController`: runs multiple sessions with optional parallelization
```

**Problem:** SimulationController is listed but not yet implemented (LIR-20 is in "Remaining Issues" in implementation_todo.md).

**Recommendation:** Update to:
```markdown
- `SimulationController` (planned): runs multiple sessions with optional parallelization
```

Or remove until implemented.

---

#### 11. README.md Project Structure Missing `table.py`
**File:** README.md:118-135

**Current State:**
```markdown
let_it_ride/
├── src/let_it_ride/
│   ├── core/           # Game engine: Card, Deck, hand evaluators, hand processing
```

**Problem:** The core/ directory description doesn't mention Table, which is a key component.

**Recommendation:**
```markdown
│   ├── core/           # Game engine: Card, Deck, hand evaluators, Table, hand processing
```

---

## Accuracy Verification Summary

### Features Listed vs Implementation Status

| Feature (README.md) | Status | Notes |
|---------------------|--------|-------|
| Accurate Game Simulation | Implemented | GameEngine, Table |
| Multiple Strategies | Implemented | Basic, AlwaysRide, AlwaysPull, Conservative, Aggressive, Custom |
| Bonus Betting | Partially Implemented | Never, Always, Static, BankrollConditional work; streak_based, combined, custom not yet |
| Bankroll Management | Implemented | All 6 betting systems |
| Statistical Analysis | Not Implemented | LIR-25 pending |
| Multi-deck Support | Implemented | Single deck with shuffle; Shoe cancelled |
| Parallel Execution | Not Implemented | LIR-21 pending |
| Export Options | Not Implemented | LIR-27, LIR-28, LIR-39 pending |
| Visualizations | Not Implemented | LIR-29, LIR-30 pending |

### Configuration Options Accuracy

| Config Section | Documented | Implemented | Match |
|---------------|------------|-------------|-------|
| simulation | Yes | Yes | Match |
| deck | Yes | Yes | Match |
| dealer | No | Yes | Missing from docs |
| table | No | Yes | Missing from docs |
| bankroll | Yes | Yes | Match |
| strategy | Yes | Yes | Match |
| bonus_strategy | Yes | Partial | 4 of 8 types implemented |
| paytables | Yes | Yes | Match |
| output | Yes | Not Yet | Config exists, export not implemented |

---

## Recommendations

### Immediate Actions (Before Next Release)

1. **Update CLAUDE.md Development Status** - Change from "greenfield" to reflect actual progress
2. **Add multi-player table documentation** to both README.md and CLAUDE.md
3. **Document dealer configuration** in README.md and CLAUDE.md
4. **Add CLI implementation status note** in README.md

### Future Actions (Can be Deferred)

1. Update sample_config.yaml with table and dealer sections
2. Add note about unimplemented bonus strategies
3. Update architecture diagram when SimulationController is implemented
4. Revise README features section when analytics/export are implemented

---

## Files Changed Summary

No files were changed. This is an analysis document only.
