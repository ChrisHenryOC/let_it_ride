# Let It Ride Strategy Simulator - Implementation Plan

## Overview

This document outlines a phased implementation plan for the Let It Ride Strategy Simulator. The plan is structured as GitHub issues sized appropriately for Claude Code execution—each issue is scoped to be completable in a single focused session (typically 30-90 minutes of agent work).

## Issue Sizing Philosophy

**Optimal Issue Characteristics for Claude Code:**

1. **Single Responsibility**: Each issue tackles one component or feature
2. **Clear Acceptance Criteria**: Testable outcomes defined upfront
3. **Minimal External Dependencies**: Can be developed without waiting on other work
4. **~200-500 lines of code**: Large enough to be meaningful, small enough to be reviewable
5. **Includes Tests**: Every issue includes unit tests for the code produced

## Recommended GitHub Project Structure

```
let-it-ride-simulator/
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── implementation_task.md
├── src/
│   └── let_it_ride/
│       ├── __init__.py
│       ├── core/           # Game engine components
│       ├── strategy/       # Strategy implementations
│       ├── bankroll/       # Bankroll management
│       ├── simulation/     # Simulation orchestration
│       ├── analytics/      # Statistics and reporting
│       └── config/         # Configuration handling
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── configs/                # Sample YAML configurations
├── docs/
└── pyproject.toml
```

---

## Phase 1: Foundation (Issues 1-8)

### Issue #1: Project Scaffolding and Development Environment

**Labels:** `foundation`, `priority-critical`, `setup`

**Description:**
Set up the Python project structure with Poetry, configure development tooling (pytest, mypy, ruff), and establish the package structure.

**Acceptance Criteria:**
- [ ] Poetry project initialized with Python 3.10+ requirement
- [ ] Package structure created (`src/let_it_ride/` with subpackages)
- [ ] pytest configured with coverage reporting
- [ ] mypy configured with strict type checking
- [ ] ruff configured for linting
- [ ] Basic `__init__.py` files with version info
- [ ] README.md with project description
- [ ] `make` or `just` commands for common tasks (test, lint, format)

**Files to Create:**
- `pyproject.toml`
- `src/let_it_ride/__init__.py`
- `src/let_it_ride/core/__init__.py`
- `src/let_it_ride/strategy/__init__.py`
- `src/let_it_ride/bankroll/__init__.py`
- `src/let_it_ride/simulation/__init__.py`
- `src/let_it_ride/analytics/__init__.py`
- `src/let_it_ride/config/__init__.py`
- `tests/conftest.py`
- `Makefile` or `justfile`

**Estimated Scope:** ~150 lines

---

### Issue #2: Card and Deck Implementation

**Labels:** `foundation`, `priority-critical`, `game-engine`

**Description:**
Implement the fundamental card representation and single-deck management with Fisher-Yates shuffling.

**Acceptance Criteria:**
- [ ] `Card` dataclass with rank, suit, and comparison methods
- [ ] `Deck` class with shuffle (Fisher-Yates), deal, reset methods
- [ ] Deck tracks dealt cards for statistical validation
- [ ] Comprehensive unit tests for card creation and deck operations
- [ ] Shuffling produces statistically uniform distribution (test with chi-square)

**Dependencies:** Issue #1

**Files to Create:**
- `src/let_it_ride/core/card.py`
- `src/let_it_ride/core/deck.py`
- `tests/unit/core/test_card.py`
- `tests/unit/core/test_deck.py`

**Key Types:**
```python
@dataclass(frozen=True)
class Card:
    rank: Rank  # Enum: TWO through ACE
    suit: Suit  # Enum: CLUBS, DIAMONDS, HEARTS, SPADES

class Deck:
    def shuffle(self, rng: random.Random) -> None
    def deal(self, count: int = 1) -> list[Card]
    def cards_remaining(self) -> int
    def dealt_cards(self) -> list[Card]
    def reset(self) -> None
```

**Estimated Scope:** ~250 lines

---

### ~~Issue #3: Multi-Deck Shoe Implementation~~ [CANCELLED]

**Status:** CANCELLED - Not needed. Each hand uses a freshly shuffled single deck.

**Original Description:**
Extend deck handling to support multi-deck shoes (2, 4, 6, 8 decks) with penetration-based reshuffle triggers.

**Cancellation Reason:**
After analysis, multi-deck shoes are not a realistic scenario for Let It Ride simulation. In practice, each hand is dealt from a freshly shuffled single deck.

---

### Issue #4: Five-Card Hand Evaluation

**Labels:** `foundation`, `priority-critical`, `game-engine`

**Description:**
Implement accurate 5-card poker hand evaluation for the main game payouts.

**Acceptance Criteria:**
- [ ] `HandRank` enum with all poker hands (Royal Flush through High Card)
- [ ] `evaluate_five_card_hand()` function returning rank and kickers
- [ ] Correctly identifies all hand types including edge cases
- [ ] Unit tests covering all 10 hand ranks with multiple examples
- [ ] Performance: evaluate 100,000 hands in under 1 second

**Dependencies:** Issue #2

**Files to Create:**
- `src/let_it_ride/core/hand_evaluator.py`
- `tests/unit/core/test_hand_evaluator.py`
- `tests/fixtures/hand_samples.py`

**Key Types:**
```python
class FiveCardHandRank(Enum):
    ROYAL_FLUSH = 10
    STRAIGHT_FLUSH = 9
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 7
    FLUSH = 6
    STRAIGHT = 5
    THREE_OF_A_KIND = 4
    TWO_PAIR = 3
    PAIR_TENS_OR_BETTER = 2
    PAIR_BELOW_TENS = 1
    HIGH_CARD = 0

@dataclass
class HandResult:
    rank: FiveCardHandRank
    primary_cards: tuple[Rank, ...]
    kickers: tuple[Rank, ...]

def evaluate_five_card_hand(cards: Sequence[Card]) -> HandResult
```

**Estimated Scope:** ~350 lines

---

### Issue #5: Three-Card Hand Evaluation (Bonus Bet)

**Labels:** `foundation`, `priority-high`, `game-engine`

**Description:**
Implement 3-card poker hand evaluation for the Three Card Bonus side bet.

**Acceptance Criteria:**
- [ ] `ThreeCardHandRank` enum (Mini Royal through High Card)
- [ ] `evaluate_three_card_hand()` function
- [ ] Special handling for Mini Royal (AKQ suited)
- [ ] Unit tests covering all 7 hand types
- [ ] Validation against known probabilities (22,100 total combinations)

**Dependencies:** Issue #2

**Files to Create:**
- `src/let_it_ride/core/three_card_evaluator.py`
- `tests/unit/core/test_three_card_evaluator.py`

**Key Types:**
```python
class ThreeCardHandRank(Enum):
    MINI_ROYAL = 7
    STRAIGHT_FLUSH = 6
    THREE_OF_A_KIND = 5
    STRAIGHT = 4
    FLUSH = 3
    PAIR = 2
    HIGH_CARD = 1

def evaluate_three_card_hand(cards: Sequence[Card]) -> ThreeCardHandRank
```

**Estimated Scope:** ~200 lines

---

### Issue #6: Paytable Configuration System

**Labels:** `foundation`, `priority-high`, `config`

**Description:**
Implement configurable paytables for both main game and bonus bet with payout calculation.

**Acceptance Criteria:**
- [ ] `Paytable` dataclass with payout mappings
- [ ] Default paytables: standard main game, bonus paytables A/B/C
- [ ] `calculate_payout()` function given hand rank and bet amount
- [ ] Paytable validation (all ranks covered, positive payouts)
- [ ] Unit tests for payout calculations across all paytables

**Dependencies:** Issues #4, #5

**Files to Create:**
- `src/let_it_ride/config/paytables.py`
- `tests/unit/config/test_paytables.py`

**Key Types:**
```python
@dataclass
class MainGamePaytable:
    payouts: dict[FiveCardHandRank, int]  # Payout ratios
    
    def calculate_payout(self, rank: FiveCardHandRank, bet: float) -> float

@dataclass
class BonusPaytable:
    payouts: dict[ThreeCardHandRank, int]
    
    def calculate_payout(self, rank: ThreeCardHandRank, bet: float) -> float
```

**Estimated Scope:** ~200 lines

---

### Issue #7: Hand Analysis Utilities

**Labels:** `foundation`, `priority-high`, `strategy`

**Description:**
Implement hand analysis functions that identify draws, potential, and characteristics needed for strategy decisions.

**Acceptance Criteria:**
- [ ] `HandAnalysis` dataclass with all analysis fields
- [ ] `analyze_three_cards()` for Bet 1 decision support
- [ ] `analyze_four_cards()` for Bet 2 decision support
- [ ] Detection of: flush draws, straight draws (open/inside), royal draws
- [ ] High card counting, gap analysis for straight draws
- [ ] Unit tests for all draw detection scenarios

**Dependencies:** Issue #2

**Files to Create:**
- `src/let_it_ride/core/hand_analysis.py`
- `tests/unit/core/test_hand_analysis.py`

**Key Types:**
```python
@dataclass
class HandAnalysis:
    high_cards: int
    suited_cards: int
    connected_cards: int
    gaps: int
    has_paying_hand: bool
    has_pair: bool
    has_high_pair: bool
    has_trips: bool
    is_flush_draw: bool
    is_straight_draw: bool
    is_open_straight_draw: bool
    is_inside_straight_draw: bool
    is_straight_flush_draw: bool
    is_royal_draw: bool
    pair_rank: Rank | None

def analyze_three_cards(cards: Sequence[Card]) -> HandAnalysis
def analyze_four_cards(cards: Sequence[Card]) -> HandAnalysis
```

**Estimated Scope:** ~300 lines

---

### Issue #8: YAML Configuration Schema and Loader

**Labels:** `foundation`, `priority-high`, `config`

**Description:**
Implement YAML configuration loading with validation using Pydantic models.

**Acceptance Criteria:**
- [ ] Pydantic models for all configuration sections
- [ ] `load_config()` function with file path input
- [ ] Comprehensive validation with meaningful error messages
- [ ] Default values for optional fields
- [ ] Unit tests for valid and invalid configurations
- [ ] Sample configuration file

**Dependencies:** Issue #1

**Files to Create:**
- `src/let_it_ride/config/models.py`
- `src/let_it_ride/config/loader.py`
- `tests/unit/config/test_loader.py`
- `configs/sample_config.yaml`

**Key Types:**
```python
class SimulationConfig(BaseModel):
    num_sessions: int = Field(ge=1, le=100_000_000)
    hands_per_session: int = Field(ge=1, le=10_000)
    random_seed: int | None = None
    workers: int | Literal["auto"] = "auto"

class DeckConfig(BaseModel):
    shuffle_algorithm: Literal["fisher_yates", "cryptographic"] = "fisher_yates"

# ... additional config models
```

**Estimated Scope:** ~400 lines

---

## Phase 2: Game Logic (Issues 9-14)

### Issue #9: Let It Ride Hand State Machine

**Labels:** `game-logic`, `priority-critical`

**Description:**
Implement the core hand state machine that tracks a single hand through all decision points.

**Acceptance Criteria:**
- [ ] `HandState` class tracking cards, bets, decisions
- [ ] State transitions: INITIAL → BET1_DECISION → REVEAL_FIRST → BET2_DECISION → REVEAL_SECOND → RESOLVED
- [ ] Bet tracking (which bets are still in play)
- [ ] Unit tests for all state transitions

**Dependencies:** Issues #2, #4, #5

**Files to Create:**
- `src/let_it_ride/core/hand_state.py`
- `tests/unit/core/test_hand_state.py`

**Estimated Scope:** ~250 lines

---

### Issue #10: Basic Strategy Implementation

**Labels:** `game-logic`, `priority-critical`, `strategy`

**Description:**
Implement the mathematically optimal basic strategy for pull/ride decisions.

**Acceptance Criteria:**
- [ ] `BasicStrategy` class implementing strategy interface
- [ ] Bet 1 decision logic per published basic strategy charts
- [ ] Bet 2 decision logic per published basic strategy charts
- [ ] Unit tests validating against known optimal decisions
- [ ] 100% accuracy against strategy chart test cases

**Dependencies:** Issue #7

**Files to Create:**
- `src/let_it_ride/strategy/basic.py`
- `tests/unit/strategy/test_basic.py`
- `tests/fixtures/basic_strategy_cases.py`

**Key Types:**
```python
class Strategy(Protocol):
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision

class BasicStrategy(Strategy):
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
```

**Estimated Scope:** ~250 lines

---

### Issue #11: Baseline Strategies (Always Ride / Always Pull)

**Labels:** `game-logic`, `priority-high`, `strategy`

**Description:**
Implement the baseline comparison strategies for variance analysis.

**Acceptance Criteria:**
- [ ] `AlwaysRideStrategy` implementation
- [ ] `AlwaysPullStrategy` implementation
- [ ] Unit tests confirming correct behavior
- [ ] Both implement the `Strategy` protocol

**Dependencies:** Issue #10

**Files to Create:**
- `src/let_it_ride/strategy/baseline.py`
- `tests/unit/strategy/test_baseline.py`

**Estimated Scope:** ~100 lines

---

### Issue #12: Custom Strategy Configuration Parser

**Labels:** `game-logic`, `priority-medium`, `strategy`

**Description:**
Implement custom strategy rule parsing from YAML configuration.

**Acceptance Criteria:**
- [ ] Parse `bet1_rules` and `bet2_rules` from config
- [ ] Condition evaluation using HandAnalysis fields
- [ ] Rule priority (first match wins)
- [ ] Support for conservative and aggressive presets
- [ ] Unit tests for rule parsing and evaluation

**Dependencies:** Issues #7, #8

**Files to Create:**
- `src/let_it_ride/strategy/custom.py`
- `src/let_it_ride/strategy/presets.py`
- `tests/unit/strategy/test_custom.py`

**Estimated Scope:** ~300 lines

---

### Issue #13: Game Engine Orchestration

**Labels:** `game-logic`, `priority-critical`

**Description:**
Implement the main game engine that orchestrates dealing, decisions, and payout calculation.

**Acceptance Criteria:**
- [ ] `GameEngine` class coordinating all components
- [ ] `play_hand()` method returning complete hand result
- [ ] Integration of deck/shoe, strategy, paytables
- [ ] Support for both main game and bonus bet
- [ ] Integration tests for complete hand flow

**Dependencies:** Issues #2, #6, #9, #10

**Files to Create:**
- `src/let_it_ride/core/game_engine.py`
- `tests/integration/test_game_engine.py`

**Key Types:**
```python
@dataclass
class HandResult:
    hand_id: int
    player_cards: tuple[Card, ...]
    community_cards: tuple[Card, ...]
    decision_bet1: Decision
    decision_bet2: Decision
    final_hand_rank: FiveCardHandRank
    base_bet: float
    bets_at_risk: float
    main_payout: float
    bonus_bet: float
    bonus_hand_rank: ThreeCardHandRank | None
    bonus_payout: float
    net_result: float

class GameEngine:
    def __init__(self, config: GameConfig, strategy: Strategy, rng: random.Random)
    def play_hand(self, base_bet: float, bonus_bet: float = 0) -> HandResult
```

**Estimated Scope:** ~300 lines

---

### Issue #14: Bonus Betting Strategies

**Labels:** `game-logic`, `priority-high`, `strategy`

**Description:**
Implement the various bonus betting strategies (never, always, static, conditional).

**Acceptance Criteria:**
- [ ] `BonusStrategy` protocol definition
- [ ] `NeverBonusStrategy`, `AlwaysBonusStrategy`, `StaticBonusStrategy`
- [ ] `BankrollConditionalBonusStrategy` with profit thresholds
- [ ] Configuration parsing for all bonus strategy types
- [ ] Unit tests for each strategy type

**Dependencies:** Issue #8

**Files to Create:**
- `src/let_it_ride/strategy/bonus.py`
- `tests/unit/strategy/test_bonus.py`

**Key Types:**
```python
class BonusStrategy(Protocol):
    def get_bonus_bet(self, context: BonusContext) -> float

@dataclass
class BonusContext:
    bankroll: float
    starting_bankroll: float
    session_profit: float
    hands_played: int
    main_streak: int
    bonus_streak: int
    base_bet: float
```

**Estimated Scope:** ~300 lines

---

## Phase 3: Bankroll and Session Management (Issues 15-19)

### Issue #15: Bankroll Tracker

**Labels:** `bankroll`, `priority-critical`

**Description:**
Implement bankroll tracking with high water mark and drawdown calculation.

**Acceptance Criteria:**
- [ ] `BankrollTracker` class with transaction logging
- [ ] `apply_result()` method updating balance
- [ ] High water mark tracking
- [ ] Maximum drawdown calculation
- [ ] Balance history for visualization
- [ ] Unit tests for all tracking scenarios

**Dependencies:** Issue #1

**Files to Create:**
- `src/let_it_ride/bankroll/tracker.py`
- `tests/unit/bankroll/test_tracker.py`

**Key Types:**
```python
class BankrollTracker:
    def __init__(self, starting_amount: float)
    def apply_result(self, amount: float) -> None
    @property
    def balance(self) -> float
    @property
    def peak_balance(self) -> float
    @property
    def max_drawdown(self) -> float
    @property
    def history(self) -> list[float]
```

**Estimated Scope:** ~150 lines

---

### Issue #16: Flat Betting System

**Labels:** `bankroll`, `priority-critical`

**Description:**
Implement the flat (constant) betting system as the baseline.

**Acceptance Criteria:**
- [ ] `BettingSystem` protocol definition
- [ ] `FlatBetting` implementation returning constant base bet
- [ ] Validation that bet doesn't exceed bankroll
- [ ] Unit tests

**Dependencies:** Issue #15

**Files to Create:**
- `src/let_it_ride/bankroll/betting_systems.py`
- `tests/unit/bankroll/test_betting_systems.py`

**Estimated Scope:** ~100 lines

---

### Issue #17: Progressive Betting Systems

**Labels:** `bankroll`, `priority-medium`

**Description:**
Implement progressive betting systems (Martingale, Paroli, D'Alembert, Fibonacci).

**Acceptance Criteria:**
- [ ] `MartingaleBetting` with loss multiplier and max bet cap
- [ ] `ParoliBetting` with win multiplier and reset
- [ ] `DAlembertBetting` with unit adjustments
- [ ] `FibonacciBetting` with sequence progression
- [ ] All systems respect min/max bet limits
- [ ] Unit tests for each system's progression logic

**Dependencies:** Issue #16

**Files to Modify:**
- `src/let_it_ride/bankroll/betting_systems.py`
- `tests/unit/bankroll/test_betting_systems.py`

**Estimated Scope:** ~350 lines

---

### Issue #18: Session State Management

**Labels:** `session`, `priority-critical`

**Description:**
Implement session lifecycle management with stop conditions.

**Acceptance Criteria:**
- [ ] `Session` class managing session state
- [ ] Stop condition checking (win limit, loss limit, max hands, insufficient funds)
- [ ] Session statistics accumulation
- [ ] Session outcome determination (win/loss/push)
- [ ] Unit tests for all stop conditions

**Dependencies:** Issues #13, #15

**Files to Create:**
- `src/let_it_ride/simulation/session.py`
- `tests/unit/simulation/test_session.py`

**Key Types:**
```python
@dataclass
class SessionConfig:
    starting_bankroll: float
    base_bet: float
    win_limit: float | None
    loss_limit: float | None
    max_hands: int | None
    stop_on_insufficient_funds: bool = True

class Session:
    def __init__(self, config: SessionConfig, engine: GameEngine, ...)
    def play_hand(self) -> HandResult
    def should_stop(self) -> bool
    def stop_reason(self) -> StopReason
    def run_to_completion(self) -> SessionResult
```

**Estimated Scope:** ~250 lines

---

### Issue #19: Session Result Data Structures

**Labels:** `session`, `priority-high`

**Description:**
Define comprehensive data structures for session results and hand records.

**Acceptance Criteria:**
- [ ] `HandRecord` dataclass with all per-hand fields
- [ ] `SessionResult` dataclass with all summary fields
- [ ] Serialization to dict/JSON
- [ ] Hand distribution counting
- [ ] Unit tests for data structure completeness

**Dependencies:** Issue #13

**Files to Create:**
- `src/let_it_ride/simulation/results.py`
- `tests/unit/simulation/test_results.py`

**Estimated Scope:** ~200 lines

---

## Phase 4: Simulation Infrastructure (Issues 20-24)

### Issue #20: Simulation Controller (Sequential)

**Labels:** `simulation`, `priority-critical`

**Description:**
Implement the main simulation controller for running multiple sessions sequentially.

**Acceptance Criteria:**
- [ ] `SimulationController` orchestrating session execution
- [ ] Progress reporting callback
- [ ] Results aggregation
- [ ] Support for seeded RNG (reproducibility)
- [ ] Integration tests for multi-session runs

**Dependencies:** Issue #18

**Files to Create:**
- `src/let_it_ride/simulation/controller.py`
- `tests/integration/test_controller.py`

**Key Types:**
```python
class SimulationController:
    def __init__(self, config: SimulationConfig)
    def run(self, progress_callback: Callable | None = None) -> SimulationResults
```

**Estimated Scope:** ~200 lines

---

### Issue #21: Parallel Session Execution

**Labels:** `simulation`, `priority-high`

**Description:**
Add parallel execution support using multiprocessing.

**Acceptance Criteria:**
- [ ] Worker pool management with configurable worker count
- [ ] Session batching for parallel execution
- [ ] Progress aggregation across workers
- [ ] Proper RNG seeding per worker (avoid correlation)
- [ ] Integration tests for parallel correctness

**Dependencies:** Issue #20

**Files to Modify:**
- `src/let_it_ride/simulation/controller.py`

**Files to Create:**
- `src/let_it_ride/simulation/parallel.py`
- `tests/integration/test_parallel.py`

**Estimated Scope:** ~250 lines

---

### Issue #22: Simulation Results Aggregation

**Labels:** `simulation`, `priority-critical`

**Description:**
Implement aggregation of results across all sessions into summary statistics.

**Acceptance Criteria:**
- [ ] `SimulationResults` class with aggregate statistics
- [ ] Session win rate calculation
- [ ] Expected value per hand calculation
- [ ] Hand frequency distribution
- [ ] Merge results from parallel workers
- [ ] Unit tests for statistical calculations

**Dependencies:** Issue #19

**Files to Create:**
- `src/let_it_ride/simulation/aggregation.py`
- `tests/unit/simulation/test_aggregation.py`

**Estimated Scope:** ~250 lines

---

### Issue #23: Statistical Validation Module

**Labels:** `simulation`, `priority-high`, `analytics`

**Description:**
Implement validation that simulation results match theoretical probabilities.

**Acceptance Criteria:**
- [ ] Chi-square test for hand frequency distribution
- [ ] Expected value convergence testing
- [ ] Confidence interval calculation
- [ ] Validation report generation
- [ ] Unit tests with known distributions

**Dependencies:** Issue #22

**Files to Create:**
- `src/let_it_ride/analytics/validation.py`
- `tests/unit/analytics/test_validation.py`

**Estimated Scope:** ~200 lines

---

### Issue #24: RNG Quality and Seeding

**Labels:** `simulation`, `priority-medium`

**Description:**
Implement proper RNG management for reproducibility and statistical quality.

**Acceptance Criteria:**
- [ ] `RNGManager` class for seed management
- [ ] Unique seed generation for parallel workers
- [ ] RNG state serialization for checkpointing
- [ ] Basic randomness quality tests
- [ ] Unit tests for reproducibility

**Dependencies:** Issue #1

**Files to Create:**
- `src/let_it_ride/simulation/rng.py`
- `tests/unit/simulation/test_rng.py`

**Estimated Scope:** ~150 lines

---

## Phase 5: Analytics and Reporting (Issues 25-30)

### Issue #25: Core Statistics Calculator

**Labels:** `analytics`, `priority-critical`

**Description:**
Implement calculation of all primary statistics from simulation results.

**Acceptance Criteria:**
- [ ] Session win rate with confidence interval
- [ ] Expected value per hand
- [ ] Variance and standard deviation
- [ ] Skewness and kurtosis
- [ ] Percentile calculations
- [ ] Unit tests with known data sets

**Dependencies:** Issue #22

**Files to Create:**
- `src/let_it_ride/analytics/statistics.py`
- `tests/unit/analytics/test_statistics.py`

**Estimated Scope:** ~250 lines

---

### Issue #26: Strategy Comparison Analytics

**Labels:** `analytics`, `priority-high`

**Description:**
Implement statistical comparison between different strategies.

**Acceptance Criteria:**
- [ ] Side-by-side metrics comparison
- [ ] Statistical significance testing (t-test, Mann-Whitney)
- [ ] Effect size calculation
- [ ] Comparison report generation
- [ ] Unit tests for comparison logic

**Dependencies:** Issue #25

**Files to Create:**
- `src/let_it_ride/analytics/comparison.py`
- `tests/unit/analytics/test_comparison.py`

**Estimated Scope:** ~200 lines

---

### Issue #27: CSV Export

**Labels:** `reporting`, `priority-critical`

**Description:**
Implement CSV export for session summaries and aggregate statistics.

**Acceptance Criteria:**
- [ ] Session summary CSV with all fields
- [ ] Aggregate statistics CSV
- [ ] Optional per-hand detail export
- [ ] Configurable field selection
- [ ] Integration tests for file output

**Dependencies:** Issue #22

**Files to Create:**
- `src/let_it_ride/analytics/export_csv.py`
- `tests/integration/test_export_csv.py`

**Estimated Scope:** ~150 lines

---

### Issue #28: JSON Export

**Labels:** `reporting`, `priority-high`

**Description:**
Implement JSON export with full configuration preservation.

**Acceptance Criteria:**
- [ ] Complete results JSON with metadata
- [ ] Configuration included in output
- [ ] Pretty-print option
- [ ] Schema documentation
- [ ] Integration tests

**Dependencies:** Issue #22

**Files to Create:**
- `src/let_it_ride/analytics/export_json.py`
- `tests/integration/test_export_json.py`

**Estimated Scope:** ~150 lines

---

### Issue #29: Visualization - Session Outcome Histogram

**Labels:** `visualization`, `priority-medium`

**Description:**
Implement histogram visualization of session outcomes using matplotlib.

**Acceptance Criteria:**
- [ ] Session profit/loss distribution histogram
- [ ] Configurable bin count
- [ ] Mean/median markers
- [ ] Win rate annotation
- [ ] PNG and SVG export
- [ ] Integration test generating sample chart

**Dependencies:** Issue #22

**Files to Create:**
- `src/let_it_ride/analytics/visualizations/histogram.py`
- `tests/integration/test_visualizations.py`

**Estimated Scope:** ~150 lines

---

### Issue #30: Visualization - Bankroll Trajectory

**Labels:** `visualization`, `priority-medium`

**Description:**
Implement bankroll trajectory line charts for sample sessions.

**Acceptance Criteria:**
- [ ] Multi-line chart showing N sample session trajectories
- [ ] Win/loss limit reference lines
- [ ] Starting bankroll baseline
- [ ] Configurable session sampling
- [ ] PNG and SVG export

**Dependencies:** Issue #29

**Files to Create:**
- `src/let_it_ride/analytics/visualizations/trajectory.py`

**Estimated Scope:** ~150 lines

---

## Phase 6: CLI and Integration (Issues 31-35)

### Issue #31: CLI Entry Point

**Labels:** `cli`, `priority-critical`

**Description:**
Implement the main CLI using Click or Typer.

**Acceptance Criteria:**
- [ ] `let-it-ride` command with subcommands
- [ ] `run` subcommand executing simulation from config file
- [ ] `validate` subcommand checking config file
- [ ] Progress bar display
- [ ] Verbosity control
- [ ] Integration tests for CLI

**Dependencies:** Issues #8, #20

**Files to Create:**
- `src/let_it_ride/cli.py`
- `tests/integration/test_cli.py`

**Estimated Scope:** ~200 lines

---

### Issue #32: Console Output Formatting

**Labels:** `cli`, `priority-high`

**Description:**
Implement formatted console output for results summary.

**Acceptance Criteria:**
- [ ] Rich-formatted tables for statistics
- [ ] Progress bar with ETA
- [ ] Summary statistics display
- [ ] Colorized win/loss indicators
- [ ] Unit tests for formatters

**Dependencies:** Issue #31

**Files to Create:**
- `src/let_it_ride/cli/formatters.py`
- `tests/unit/cli/test_formatters.py`

**Estimated Scope:** ~150 lines

---

### Issue #33: Sample Configuration Files

**Labels:** `documentation`, `priority-high`

**Description:**
Create comprehensive sample configuration files demonstrating all features.

**Acceptance Criteria:**
- [ ] Basic strategy baseline config
- [ ] Conservative strategy config
- [ ] Aggressive strategy config
- [ ] Bonus betting comparison config
- [ ] Each config documented with comments

**Dependencies:** Issue #8

**Files to Create:**
- `configs/basic_strategy.yaml`
- `configs/conservative.yaml`
- `configs/aggressive.yaml`
- `configs/bonus_comparison.yaml`

**Estimated Scope:** ~300 lines (YAML)

---

### Issue #34: End-to-End Integration Test

**Labels:** `testing`, `priority-critical`

**Description:**
Implement comprehensive end-to-end tests validating the complete simulation pipeline.

**Acceptance Criteria:**
- [ ] Test running 1000 sessions with known seed
- [ ] Verify results match expected distributions
- [ ] Test all output formats generated correctly
- [ ] Test parallel and sequential produce same aggregate results
- [ ] Test configuration validation catches errors

**Dependencies:** All previous issues

**Files to Create:**
- `tests/e2e/test_full_simulation.py`
- `tests/e2e/test_output_formats.py`

**Estimated Scope:** ~300 lines

---

### Issue #35: Performance Optimization and Benchmarking

**Labels:** `performance`, `priority-medium`

**Description:**
Profile and optimize to meet performance targets (100k hands/second).

**Acceptance Criteria:**
- [ ] Benchmark script measuring hands/second
- [ ] Profile-guided optimization of hot paths
- [ ] Numpy optimization for hand evaluation if needed
- [ ] Memory usage validation (<4GB for 10M hands)
- [ ] Performance regression tests

**Dependencies:** Issue #34

**Files to Create:**
- `benchmarks/benchmark_throughput.py`
- `benchmarks/benchmark_memory.py`

**Estimated Scope:** ~200 lines

---

## Phase 7: Advanced Features (Issues 36-40)

### ~~Issue #36: Composition-Dependent Strategy~~ [CANCELLED]

**Status:** CANCELLED - Not applicable without multi-deck shoes.

**Original Description:**
Implement strategy that adjusts based on remaining shoe composition.

**Cancellation Reason:**
This feature was dependent on multi-deck shoe support (Issue #3). Since each hand uses a freshly shuffled single deck, composition-dependent strategies are not applicable.

---

### Issue #37: Streak-Based Bonus Strategy

**Labels:** `advanced`, `priority-low`, `strategy`

**Description:**
Implement bonus betting that adjusts based on win/loss streaks.

**Acceptance Criteria:**
- [ ] Streak tracking (main game and bonus separately)
- [ ] Configurable trigger conditions
- [ ] Multiplier and reset logic
- [ ] Unit tests for streak scenarios

**Dependencies:** Issue #14

**Files to Modify:**
- `src/let_it_ride/strategy/bonus.py`
- `tests/unit/strategy/test_bonus.py`

**Estimated Scope:** ~200 lines

---

### Issue #38: Risk of Ruin Calculator

**Labels:** `analytics`, `priority-low`

**Description:**
Implement risk of ruin calculation for various bankroll levels.

**Acceptance Criteria:**
- [ ] Analytical risk of ruin formula
- [ ] Monte Carlo risk of ruin estimation
- [ ] Risk curves for different bankroll multiples
- [ ] Visualization of risk curves

**Dependencies:** Issue #25

**Files to Create:**
- `src/let_it_ride/analytics/risk_of_ruin.py`
- `tests/unit/analytics/test_risk_of_ruin.py`

**Estimated Scope:** ~200 lines

---

### Issue #39: HTML Report Generation

**Labels:** `reporting`, `priority-low`

**Description:**
Implement HTML report generation with embedded visualizations.

**Acceptance Criteria:**
- [ ] Self-contained HTML report
- [ ] Embedded Plotly charts (interactive)
- [ ] Configuration summary section
- [ ] Statistics tables
- [ ] Template-based generation (Jinja2)

**Dependencies:** Issues #29, #30

**Files to Create:**
- `src/let_it_ride/analytics/export_html.py`
- `src/let_it_ride/analytics/templates/report.html.j2`
- `tests/integration/test_export_html.py`

**Estimated Scope:** ~300 lines

---

### Issue #40: Documentation and User Guide

**Labels:** `documentation`, `priority-medium`

**Description:**
Create comprehensive documentation for installation, usage, and strategy reference.

**Acceptance Criteria:**
- [ ] Installation guide (Poetry, pip)
- [ ] Quick start tutorial
- [ ] Configuration reference (all options documented)
- [ ] Strategy guide with basic strategy charts
- [ ] API documentation (if applicable)
- [ ] Example workflows

**Dependencies:** All previous issues

**Files to Create:**
- `docs/installation.md`
- `docs/quickstart.md`
- `docs/configuration.md`
- `docs/strategies.md`
- `docs/api.md`

**Estimated Scope:** ~500 lines (documentation)

---

## Issue Creation Strategy for GitHub

### Recommended Approach

1. **Create Issues in Phases**: Create all issues for one phase before starting development. This allows proper linking and dependency tracking.

2. **Use GitHub Projects**: Set up a GitHub Project board with columns: Backlog, Ready, In Progress, Review, Done.

3. **Batch Creation Script**: Use the GitHub CLI (`gh`) to batch-create issues:

```bash
# Example: Create Issue #1
gh issue create \
  --title "Project Scaffolding and Development Environment" \
  --body "$(cat issues/issue-01.md)" \
  --label "foundation,priority-critical,setup"
```

4. **Issue Template**: Create `.github/ISSUE_TEMPLATE/implementation_task.md`:

```markdown
---
name: Implementation Task
about: A task for Claude Code to implement
labels: implementation
---

## Description
<!-- Brief description of what needs to be implemented -->

## Acceptance Criteria
<!-- Checkboxes for all requirements -->
- [ ] Criterion 1
- [ ] Criterion 2

## Dependencies
<!-- List issue numbers that must be complete first -->
Blocked by: #X, #Y

## Files to Create/Modify
<!-- List of files this issue will touch -->

## Key Types/Interfaces
<!-- Code snippets showing expected interfaces -->

## Estimated Scope
<!-- Approximate lines of code -->
```

5. **Claude Code Workflow**:
   - Reference issue number when starting work
   - Claude Code reads issue description
   - Implements according to acceptance criteria
   - Runs tests to verify
   - Creates PR referencing issue

### Dependency Graph (Simplified)

```
Phase 1: Foundation
#1 ─┬─► #2
    ├─► #4 ─► #6
    ├─► #5 ─► #6
    ├─► #7
    └─► #8

Note: #3 (Multi-Deck Shoe) is CANCELLED

Phase 2: Game Logic
#2,#4,#5 ─► #9
#7 ─► #10 ─► #11
#7,#8 ─► #12
#2,#6,#9,#10 ─► #13
#8 ─► #14

Phase 3: Bankroll/Session
#1 ─► #15 ─► #16 ─► #17
#13,#15 ─► #18
#13 ─► #19

Phase 4: Simulation
#18 ─► #20 ─► #21
#19 ─► #22 ─► #23
#1 ─► #24

Phase 5: Analytics
#22 ─► #25 ─► #26
#22 ─► #27, #28
#22 ─► #29 ─► #30

Phase 6: CLI
#8,#20 ─► #31 ─► #32
#8 ─► #33
All ─► #34 ─► #35

Phase 7: Advanced
#36 is CANCELLED (was dependent on #3)
#14 ─► #37
#25 ─► #38
#29,#30 ─► #39
All ─► #40
```

---

## Execution Recommendations

1. **Start with Phase 1 in Order**: Issues #1-#8 establish the foundation. Complete #1 first, then #2 can begin immediately.

2. **Parallel Tracks After Foundation**: Once Phase 1 is complete, Phases 2-4 can progress in parallel on separate branches.

3. **Integration Points**: Issues #13 (Game Engine) and #20 (Simulation Controller) are critical integration points—allocate extra review time.

4. **Testing Cadence**: Run the full test suite after completing each phase before merging to main.

5. **Performance Gates**: Run benchmarks after Phase 4 completion to identify optimization needs early.

---

## Summary

| Phase | Issues | Focus | Est. Total Lines |
|-------|--------|-------|------------------|
| 1 | #1-2, #4-8 | Foundation (Note: #3 cancelled) | ~1,650 |
| 2 | #9-14 | Game Logic | ~1,500 |
| 3 | #15-19 | Bankroll/Session | ~950 |
| 4 | #20-24 | Simulation | ~1,050 |
| 5 | #25-30 | Analytics | ~1,050 |
| 6 | #31-35 | CLI/Integration | ~1,150 |
| 7 | #37-40 | Advanced (Note: #36 cancelled) | ~1,200 |
| **Total** | **38** | | **~8,550** |

This plan provides 38 well-scoped issues that Claude Code can execute against, with clear acceptance criteria and dependency tracking for efficient parallel development.

**Cancelled Issues:**
- Issue #3 (Multi-Deck Shoe Implementation) - Not needed; each hand uses freshly shuffled single deck
- Issue #36 (Composition-Dependent Strategy) - Dependent on #3, not applicable
