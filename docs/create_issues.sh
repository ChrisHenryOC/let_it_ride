#!/bin/bash
# GitHub Issue Creation Script for Let It Ride Strategy Simulator
# Repository: ChrisHenryOC/let_it_ride
#
# Prerequisites:
#   1. GitHub CLI installed: https://cli.github.com/
#   2. Authenticated: gh auth login
#   3. Run from any directory
#
# Usage:
#   chmod +x create_issues.sh
#   ./create_issues.sh           # Create all issues
#   ./create_issues.sh 1 8       # Create issues 1-8 only (Phase 1)
#   ./create_issues.sh 9 14      # Create issues 9-14 only (Phase 2)

set -e

REPO="ChrisHenryOC/let_it_ride"
START_ISSUE=${1:-1}
END_ISSUE=${2:-40}

echo "Creating issues $START_ISSUE to $END_ISSUE in $REPO"
echo "=================================================="

create_issue() {
    local title="$1"
    local labels="$2"
    local body="$3"
    
    echo "Creating: $title"
    gh issue create \
        --repo "$REPO" \
        --title "$title" \
        --label "$labels" \
        --body "$body"
    echo "✓ Created"
    echo ""
    sleep 1  # Rate limiting courtesy
}

# ==============================================================================
# PHASE 1: FOUNDATION (Issues 1-8)
# ==============================================================================

if [[ $START_ISSUE -le 1 && $END_ISSUE -ge 1 ]]; then
create_issue \
"#1: Project Scaffolding and Development Environment" \
"foundation,priority-critical,setup" \
'## Description
Set up the Python project structure with Poetry, configure development tooling (pytest, mypy, ruff), and establish the package structure.

## Acceptance Criteria
- [ ] Poetry project initialized with Python 3.10+ requirement
- [ ] Package structure created (`src/let_it_ride/` with subpackages)
- [ ] pytest configured with coverage reporting
- [ ] mypy configured with strict type checking
- [ ] ruff configured for linting
- [ ] Basic `__init__.py` files with version info
- [ ] README.md with project description
- [ ] `make` or `just` commands for common tasks (test, lint, format)

## Dependencies
None - this is the first issue.

## Files to Create
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

## Estimated Scope
~150 lines'
fi

if [[ $START_ISSUE -le 2 && $END_ISSUE -ge 2 ]]; then
create_issue \
"#2: Card and Deck Implementation" \
"foundation,priority-critical,game-engine" \
'## Description
Implement the fundamental card representation and single-deck management with Fisher-Yates shuffling.

## Acceptance Criteria
- [ ] `Card` dataclass with rank, suit, and comparison methods
- [ ] `Rank` enum (TWO through ACE) with proper ordering
- [ ] `Suit` enum (CLUBS, DIAMONDS, HEARTS, SPADES)
- [ ] `Deck` class with shuffle (Fisher-Yates), deal, reset methods
- [ ] Deck tracks dealt cards for statistical validation
- [ ] Comprehensive unit tests for card creation and deck operations
- [ ] Shuffling produces statistically uniform distribution (test with chi-square)

## Dependencies
Blocked by: #1

## Files to Create
- `src/let_it_ride/core/card.py`
- `src/let_it_ride/core/deck.py`
- `tests/unit/core/test_card.py`
- `tests/unit/core/test_deck.py`

## Key Types
```python
class Rank(Enum):
    TWO = 2
    THREE = 3
    # ... through ACE = 14

class Suit(Enum):
    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"

@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

class Deck:
    def shuffle(self, rng: random.Random) -> None
    def deal(self, count: int = 1) -> list[Card]
    def cards_remaining(self) -> int
    def dealt_cards(self) -> list[Card]
    def reset(self) -> None
```

## Estimated Scope
~250 lines'
fi

if [[ $START_ISSUE -le 3 && $END_ISSUE -ge 3 ]]; then
create_issue \
"#3: Multi-Deck Shoe Implementation" \
"foundation,priority-high,game-engine" \
'## Description
Extend deck handling to support multi-deck shoes (2, 4, 6, 8 decks) with penetration-based reshuffle triggers.

## Acceptance Criteria
- [ ] `Shoe` class supporting configurable deck count (2, 4, 6, 8)
- [ ] Cut card placement based on penetration percentage (0.25-0.90)
- [ ] Automatic reshuffle detection when cut card reached
- [ ] Shoe composition tracking (cards remaining by rank/suit)
- [ ] `high_card_ratio()` method for strategy support
- [ ] Unit tests for shoe mechanics and composition tracking

## Dependencies
Blocked by: #2

## Files to Create
- `src/let_it_ride/core/shoe.py`
- `tests/unit/core/test_shoe.py`

## Key Types
```python
class Shoe:
    def __init__(self, num_decks: int, penetration: float, rng: random.Random)
    def deal(self, count: int = 1) -> list[Card]
    def needs_reshuffle(self) -> bool
    def reshuffle(self) -> None
    def composition(self) -> dict[Rank, int]
    def high_card_ratio(self) -> float
    def cards_remaining(self) -> int
```

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 4 && $END_ISSUE -ge 4 ]]; then
create_issue \
"#4: Five-Card Hand Evaluation" \
"foundation,priority-critical,game-engine" \
'## Description
Implement accurate 5-card poker hand evaluation for the main game payouts.

## Acceptance Criteria
- [ ] `FiveCardHandRank` enum with all poker hands (Royal Flush through High Card)
- [ ] `HandResult` dataclass with rank, primary cards, and kickers
- [ ] `evaluate_five_card_hand()` function returning HandResult
- [ ] Correctly identifies all hand types including edge cases (wheel straight, steel wheel)
- [ ] Distinguishes between `PAIR_TENS_OR_BETTER` and `PAIR_BELOW_TENS` (only 10+ pays)
- [ ] Unit tests covering all 10 hand ranks with multiple examples each
- [ ] Performance: evaluate 100,000 hands in under 1 second

## Dependencies
Blocked by: #2

## Files to Create
- `src/let_it_ride/core/hand_evaluator.py`
- `tests/unit/core/test_hand_evaluator.py`
- `tests/fixtures/hand_samples.py`

## Key Types
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

## Estimated Scope
~350 lines'
fi

if [[ $START_ISSUE -le 5 && $END_ISSUE -ge 5 ]]; then
create_issue \
"#5: Three-Card Hand Evaluation (Bonus Bet)" \
"foundation,priority-high,game-engine" \
'## Description
Implement 3-card poker hand evaluation for the Three Card Bonus side bet.

## Acceptance Criteria
- [ ] `ThreeCardHandRank` enum (Mini Royal, Straight Flush, Three of a Kind, Straight, Flush, Pair, High Card)
- [ ] `evaluate_three_card_hand()` function returning rank
- [ ] Special handling for Mini Royal (AKQ suited) - distinct from other straight flushes
- [ ] Correct straight detection (A-2-3 is valid, A-K-Q is valid, K-A-2 is not)
- [ ] Unit tests covering all 7 hand types
- [ ] Validation against known probabilities (22,100 total combinations)

## Dependencies
Blocked by: #2

## Files to Create
- `src/let_it_ride/core/three_card_evaluator.py`
- `tests/unit/core/test_three_card_evaluator.py`

## Key Types
```python
class ThreeCardHandRank(Enum):
    MINI_ROYAL = 7      # AKQ suited only
    STRAIGHT_FLUSH = 6  # Other straight flushes
    THREE_OF_A_KIND = 5
    STRAIGHT = 4
    FLUSH = 3
    PAIR = 2
    HIGH_CARD = 1

def evaluate_three_card_hand(cards: Sequence[Card]) -> ThreeCardHandRank
```

## Reference Probabilities
| Hand | Combinations | Probability |
|------|--------------|-------------|
| Mini Royal | 4 | 0.0181% |
| Straight Flush | 44 | 0.199% |
| Three of a Kind | 52 | 0.235% |
| Straight | 720 | 3.26% |
| Flush | 1,096 | 4.96% |
| Pair | 3,744 | 16.94% |
| High Card | 16,440 | 74.39% |

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 6 && $END_ISSUE -ge 6 ]]; then
create_issue \
"#6: Paytable Configuration System" \
"foundation,priority-high,config" \
'## Description
Implement configurable paytables for both main game and bonus bet with payout calculation.

## Acceptance Criteria
- [ ] `MainGamePaytable` dataclass with payout mappings for 5-card hands
- [ ] `BonusPaytable` dataclass with payout mappings for 3-card hands
- [ ] Default paytables: standard main game, bonus paytables A/B/C per requirements
- [ ] `calculate_payout()` methods given hand rank and bet amount
- [ ] Paytable validation (all ranks covered, non-negative payouts)
- [ ] Support for custom paytable definition
- [ ] Unit tests for payout calculations across all paytables

## Dependencies
Blocked by: #4, #5

## Files to Create
- `src/let_it_ride/config/paytables.py`
- `tests/unit/config/test_paytables.py`

## Key Types
```python
@dataclass
class MainGamePaytable:
    name: str
    payouts: dict[FiveCardHandRank, int]  # Payout ratios (e.g., 1000 for Royal)
    
    def calculate_payout(self, rank: FiveCardHandRank, bet: float) -> float
    def validate(self) -> None

@dataclass  
class BonusPaytable:
    name: str
    payouts: dict[ThreeCardHandRank, int]
    
    def calculate_payout(self, rank: ThreeCardHandRank, bet: float) -> float
    def validate(self) -> None

# Factory functions for standard paytables
def standard_main_paytable() -> MainGamePaytable
def bonus_paytable_a() -> BonusPaytable
def bonus_paytable_b() -> BonusPaytable
def bonus_paytable_c() -> BonusPaytable
```

## Standard Main Game Paytable
| Hand | Payout |
|------|--------|
| Royal Flush | 1000:1 |
| Straight Flush | 200:1 |
| Four of a Kind | 50:1 |
| Full House | 11:1 |
| Flush | 8:1 |
| Straight | 5:1 |
| Three of a Kind | 3:1 |
| Two Pair | 2:1 |
| Pair of 10s+ | 1:1 |

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 7 && $END_ISSUE -ge 7 ]]; then
create_issue \
"#7: Hand Analysis Utilities" \
"foundation,priority-high,strategy" \
'## Description
Implement hand analysis functions that identify draws, potential, and characteristics needed for strategy decisions.

## Acceptance Criteria
- [ ] `HandAnalysis` dataclass with all analysis fields
- [ ] `analyze_three_cards()` for Bet 1 decision support
- [ ] `analyze_four_cards()` for Bet 2 decision support
- [ ] Detection of flush draws (3 or 4 suited cards)
- [ ] Detection of straight draws (open-ended vs inside/gutshot)
- [ ] Detection of royal flush draws and straight flush draws
- [ ] High card counting (10, J, Q, K, A)
- [ ] Gap analysis for straight draw quality
- [ ] Unit tests for all draw detection scenarios

## Dependencies
Blocked by: #2

## Files to Create
- `src/let_it_ride/core/hand_analysis.py`
- `tests/unit/core/test_hand_analysis.py`

## Key Types
```python
@dataclass
class HandAnalysis:
    # Card counts
    high_cards: int           # Count of 10, J, Q, K, A
    suited_cards: int         # Maximum cards of same suit
    connected_cards: int      # Maximum sequential cards
    gaps: int                 # Gaps in potential straight
    
    # Made hand flags
    has_paying_hand: bool     # Already qualifies for payout
    has_pair: bool
    has_high_pair: bool       # Pair of 10s or better
    has_trips: bool
    pair_rank: Rank | None
    
    # Draw flags  
    is_flush_draw: bool
    is_straight_draw: bool
    is_open_straight_draw: bool
    is_inside_straight_draw: bool
    is_straight_flush_draw: bool
    is_royal_draw: bool
    
    # For 3-card analysis: cards needed info
    suited_high_cards: int    # High cards that are suited together

def analyze_three_cards(cards: Sequence[Card]) -> HandAnalysis
def analyze_four_cards(cards: Sequence[Card]) -> HandAnalysis
```

## Estimated Scope
~300 lines'
fi

if [[ $START_ISSUE -le 8 && $END_ISSUE -ge 8 ]]; then
create_issue \
"#8: YAML Configuration Schema and Loader" \
"foundation,priority-high,config" \
'## Description
Implement YAML configuration loading with validation using Pydantic models.

## Acceptance Criteria
- [ ] Pydantic models for all configuration sections (simulation, deck, bankroll, strategy, bonus_strategy, paytables, output)
- [ ] `load_config()` function accepting file path
- [ ] Comprehensive validation with meaningful error messages
- [ ] Default values for all optional fields
- [ ] Type coercion where appropriate (e.g., "auto" for workers)
- [ ] Unit tests for valid configurations
- [ ] Unit tests for invalid configurations (proper error messages)
- [ ] Sample configuration file demonstrating all options

## Dependencies
Blocked by: #1

## Files to Create
- `src/let_it_ride/config/models.py`
- `src/let_it_ride/config/loader.py`
- `tests/unit/config/test_loader.py`
- `tests/unit/config/test_models.py`
- `configs/sample_config.yaml`

## Key Types
```python
class SimulationConfig(BaseModel):
    num_sessions: int = Field(ge=1, le=100_000_000)
    hands_per_session: int = Field(ge=1, le=10_000)
    random_seed: int | None = None
    workers: int | Literal["auto"] = "auto"
    progress_interval: int = 10000
    detailed_logging: bool = False

class DeckConfig(BaseModel):
    num_decks: Literal[1, 2, 4, 6, 8] = 1
    penetration: float = Field(ge=0.25, le=0.90, default=0.75)
    shuffle_algorithm: Literal["fisher_yates", "cryptographic"] = "fisher_yates"
    track_composition: bool = True

class BankrollConfig(BaseModel):
    starting_amount: float = Field(gt=0)
    base_bet: float = Field(gt=0)
    stop_conditions: StopConditionsConfig
    betting_system: BettingSystemConfig

class StrategyConfig(BaseModel):
    type: Literal["basic", "always_ride", "always_pull", "conservative", "aggressive", "composition_dependent", "custom"]
    # ... strategy-specific configs

class FullConfig(BaseModel):
    metadata: MetadataConfig
    simulation: SimulationConfig
    deck: DeckConfig
    bankroll: BankrollConfig
    strategy: StrategyConfig
    bonus_strategy: BonusStrategyConfig
    paytables: PaytablesConfig
    output: OutputConfig

def load_config(path: Path) -> FullConfig
```

## Estimated Scope
~400 lines'
fi

# ==============================================================================
# PHASE 2: GAME LOGIC (Issues 9-14)
# ==============================================================================

if [[ $START_ISSUE -le 9 && $END_ISSUE -ge 9 ]]; then
create_issue \
"#9: Let It Ride Hand State Machine" \
"game-logic,priority-critical" \
'## Description
Implement the core hand state machine that tracks a single hand through all decision points.

## Acceptance Criteria
- [ ] `HandPhase` enum: DEAL, BET1_DECISION, FIRST_REVEAL, BET2_DECISION, SECOND_REVEAL, RESOLVED
- [ ] `HandState` class tracking current phase, cards, bets, decisions
- [ ] State transitions enforced (cannot skip phases)
- [ ] Bet tracking: which of the 3 bets are still in play
- [ ] `apply_decision()` method for recording ride/pull choices
- [ ] `reveal_community_card()` method for phase advancement
- [ ] `resolve()` method for final evaluation
- [ ] Unit tests for all state transitions
- [ ] Unit tests for invalid transitions (should raise)

## Dependencies
Blocked by: #2, #4, #5

## Files to Create
- `src/let_it_ride/core/hand_state.py`
- `tests/unit/core/test_hand_state.py`

## Key Types
```python
class HandPhase(Enum):
    DEAL = "deal"
    BET1_DECISION = "bet1_decision"
    FIRST_REVEAL = "first_reveal"
    BET2_DECISION = "bet2_decision"
    SECOND_REVEAL = "second_reveal"
    RESOLVED = "resolved"

class Decision(Enum):
    RIDE = "ride"
    PULL = "pull"

@dataclass
class HandState:
    phase: HandPhase
    player_cards: tuple[Card, Card, Card]
    community_cards: list[Card]  # 0, 1, or 2 cards
    base_bet: float
    bet1_decision: Decision | None
    bet2_decision: Decision | None
    bet1_active: bool  # Still in play?
    bet2_active: bool
    bet3_active: bool  # Always True
    
    def apply_bet1_decision(self, decision: Decision) -> None
    def reveal_first_community(self, card: Card) -> None
    def apply_bet2_decision(self, decision: Decision) -> None
    def reveal_second_community(self, card: Card) -> None
    def get_visible_cards(self) -> list[Card]
    def get_final_hand(self) -> tuple[Card, ...]
    def bets_at_risk(self) -> float
```

## Estimated Scope
~250 lines'
fi

if [[ $START_ISSUE -le 10 && $END_ISSUE -ge 10 ]]; then
create_issue \
"#10: Basic Strategy Implementation" \
"game-logic,priority-critical,strategy" \
'## Description
Implement the mathematically optimal basic strategy for pull/ride decisions.

## Acceptance Criteria
- [ ] `Strategy` protocol defining the interface
- [ ] `BasicStrategy` class implementing the protocol
- [ ] Bet 1 decision logic per published basic strategy charts (see below)
- [ ] Bet 2 decision logic per published basic strategy charts
- [ ] Unit tests validating against known optimal decisions
- [ ] Test coverage for edge cases (borderline hands)
- [ ] 100% accuracy against comprehensive strategy chart test cases

## Dependencies
Blocked by: #7

## Files to Create
- `src/let_it_ride/strategy/base.py` (Protocol definition)
- `src/let_it_ride/strategy/basic.py`
- `tests/unit/strategy/test_basic.py`
- `tests/fixtures/basic_strategy_cases.py`

## Key Types
```python
@dataclass
class StrategyContext:
    """Context available to strategy for decisions"""
    session_profit: float
    hands_played: int
    streak: int  # Positive = wins, negative = losses
    bankroll: float
    deck_composition: dict[Rank, int] | None  # For composition-dependent

class Strategy(Protocol):
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision

class BasicStrategy:
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
```

## Basic Strategy Reference

**Bet 1 (3 cards) - LET IT RIDE when holding:**
- Any paying hand (pair of 10s+, three of a kind)
- Three to a Royal Flush
- Three suited in sequence (except A-2-3, 2-3-4)
- Three to straight flush, spread 4, with 1+ high card
- Three to straight flush, spread 5, with 2+ high cards

**Bet 2 (4 cards) - LET IT RIDE when holding:**
- Any paying hand
- Four to a flush
- Four to outside straight with 1+ high card
- Four to inside straight with 4 high cards (10-J-Q-K)

## Estimated Scope
~250 lines'
fi

if [[ $START_ISSUE -le 11 && $END_ISSUE -ge 11 ]]; then
create_issue \
"#11: Baseline Strategies (Always Ride / Always Pull)" \
"game-logic,priority-high,strategy" \
'## Description
Implement the baseline comparison strategies for variance analysis.

## Acceptance Criteria
- [ ] `AlwaysRideStrategy` - always returns RIDE for both decisions
- [ ] `AlwaysPullStrategy` - always returns PULL for both decisions  
- [ ] Both implement the `Strategy` protocol from #10
- [ ] Unit tests confirming correct behavior
- [ ] These serve as variance bounds for strategy comparison

## Dependencies
Blocked by: #10

## Files to Create
- `src/let_it_ride/strategy/baseline.py`
- `tests/unit/strategy/test_baseline.py`

## Key Types
```python
class AlwaysRideStrategy:
    """Maximum variance baseline - never pulls"""
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        return Decision.RIDE
    
    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        return Decision.RIDE

class AlwaysPullStrategy:
    """Minimum variance baseline - always pulls (only bet 3 remains)"""
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        return Decision.PULL
    
    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        return Decision.PULL
```

## Estimated Scope
~100 lines'
fi

if [[ $START_ISSUE -le 12 && $END_ISSUE -ge 12 ]]; then
create_issue \
"#12: Custom Strategy Configuration Parser" \
"game-logic,priority-medium,strategy" \
'## Description
Implement custom strategy rule parsing from YAML configuration, plus conservative/aggressive presets.

## Acceptance Criteria
- [ ] `CustomStrategy` class that evaluates rules from config
- [ ] Parse `bet1_rules` and `bet2_rules` lists from YAML
- [ ] Condition evaluation using HandAnalysis fields
- [ ] Rule priority: first matching rule wins
- [ ] Default rule support (fallback action)
- [ ] `ConservativeStrategy` preset (ride only on made hands)
- [ ] `AggressiveStrategy` preset (ride on any draw)
- [ ] Unit tests for rule parsing
- [ ] Unit tests for condition evaluation

## Dependencies
Blocked by: #7, #8

## Files to Create
- `src/let_it_ride/strategy/custom.py`
- `src/let_it_ride/strategy/presets.py`
- `tests/unit/strategy/test_custom.py`
- `tests/unit/strategy/test_presets.py`

## Key Types
```python
@dataclass
class StrategyRule:
    condition: str  # e.g., "has_paying_hand", "is_flush_draw and high_cards >= 2"
    action: Decision

class CustomStrategy:
    def __init__(self, bet1_rules: list[StrategyRule], bet2_rules: list[StrategyRule])
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision
    def _evaluate_condition(self, condition: str, analysis: HandAnalysis) -> bool

def conservative_strategy() -> CustomStrategy
def aggressive_strategy() -> CustomStrategy
```

## Example Config Rules
```yaml
bet1_rules:
  - condition: "has_paying_hand"
    action: "ride"
  - condition: "is_royal_draw and suited_high_cards >= 3"
    action: "ride"
  - condition: "default"
    action: "pull"
```

## Estimated Scope
~300 lines'
fi

if [[ $START_ISSUE -le 13 && $END_ISSUE -ge 13 ]]; then
create_issue \
"#13: Game Engine Orchestration" \
"game-logic,priority-critical" \
'## Description
Implement the main game engine that orchestrates dealing, decisions, and payout calculation for a single hand.

## Acceptance Criteria
- [ ] `GameEngine` class coordinating deck/shoe, strategy, paytables
- [ ] `play_hand()` method executing complete hand flow
- [ ] Proper card dealing sequence (3 player, 2 community)
- [ ] Strategy invocation at correct decision points
- [ ] Main game payout calculation
- [ ] Bonus bet evaluation and payout (if bonus bet > 0)
- [ ] `HandResult` dataclass returned with all hand details
- [ ] Support for both single deck and shoe
- [ ] Integration tests for complete hand flow
- [ ] Tests verifying payout accuracy

## Dependencies
Blocked by: #3, #6, #9, #10

## Files to Create
- `src/let_it_ride/core/game_engine.py`
- `tests/integration/test_game_engine.py`

## Key Types
```python
@dataclass
class HandResult:
    hand_id: int
    player_cards: tuple[Card, Card, Card]
    community_cards: tuple[Card, Card]
    decision_bet1: Decision
    decision_bet2: Decision
    final_hand_rank: FiveCardHandRank
    base_bet: float
    bets_at_risk: float  # Total wagered after decisions
    main_payout: float
    bonus_bet: float
    bonus_hand_rank: ThreeCardHandRank | None
    bonus_payout: float
    net_result: float  # Total profit/loss for hand

class GameEngine:
    def __init__(
        self,
        deck_or_shoe: Deck | Shoe,
        strategy: Strategy,
        main_paytable: MainGamePaytable,
        bonus_paytable: BonusPaytable | None,
        rng: random.Random,
    )
    
    def play_hand(
        self,
        hand_id: int,
        base_bet: float,
        bonus_bet: float = 0.0,
        context: StrategyContext | None = None,
    ) -> HandResult
    
    def needs_reshuffle(self) -> bool  # For shoe mode
```

## Hand Flow
1. Deal 3 cards to player, 2 face-down community
2. Analyze 3-card hand, invoke strategy for bet 1
3. Reveal first community card
4. Analyze 4-card hand, invoke strategy for bet 2
5. Reveal second community card
6. Evaluate final 5-card hand
7. Calculate main game payout based on active bets
8. If bonus bet, evaluate 3-card hand and calculate bonus payout
9. Return complete HandResult

## Estimated Scope
~300 lines'
fi

if [[ $START_ISSUE -le 14 && $END_ISSUE -ge 14 ]]; then
create_issue \
"#14: Bonus Betting Strategies" \
"game-logic,priority-high,strategy" \
'## Description
Implement the various bonus betting strategies (never, always, static, bankroll-conditional).

## Acceptance Criteria
- [ ] `BonusStrategy` protocol definition
- [ ] `NeverBonusStrategy` - always returns 0
- [ ] `AlwaysBonusStrategy` - returns fixed amount
- [ ] `StaticBonusStrategy` - fixed amount or ratio of base bet
- [ ] `BankrollConditionalBonusStrategy` with profit thresholds and scaling tiers
- [ ] Configuration parsing for all bonus strategy types
- [ ] All strategies respect min/max bonus bet limits
- [ ] Unit tests for each strategy type
- [ ] Unit tests for edge cases (bankroll below threshold, etc.)

## Dependencies
Blocked by: #8

## Files to Create
- `src/let_it_ride/strategy/bonus.py`
- `tests/unit/strategy/test_bonus.py`

## Key Types
```python
@dataclass
class BonusContext:
    bankroll: float
    starting_bankroll: float
    session_profit: float
    hands_played: int
    main_streak: int
    bonus_streak: int
    base_bet: float
    min_bonus_bet: float
    max_bonus_bet: float

class BonusStrategy(Protocol):
    def get_bonus_bet(self, context: BonusContext) -> float

class NeverBonusStrategy:
    def get_bonus_bet(self, context: BonusContext) -> float:
        return 0.0

class AlwaysBonusStrategy:
    def __init__(self, amount: float)
    def get_bonus_bet(self, context: BonusContext) -> float

class StaticBonusStrategy:
    def __init__(self, amount: float | None = None, ratio: float | None = None)
    def get_bonus_bet(self, context: BonusContext) -> float

class BankrollConditionalBonusStrategy:
    def __init__(
        self,
        base_amount: float,
        min_session_profit: float | None,
        min_bankroll_ratio: float | None,
        max_drawdown: float | None,
        scaling_tiers: list[ScalingTier] | None,
    )
    def get_bonus_bet(self, context: BonusContext) -> float
```

## Estimated Scope
~300 lines'
fi

# ==============================================================================
# PHASE 3: BANKROLL AND SESSION MANAGEMENT (Issues 15-19)
# ==============================================================================

if [[ $START_ISSUE -le 15 && $END_ISSUE -ge 15 ]]; then
create_issue \
"#15: Bankroll Tracker" \
"bankroll,priority-critical" \
'## Description
Implement bankroll tracking with high water mark and drawdown calculation.

## Acceptance Criteria
- [ ] `BankrollTracker` class initialized with starting amount
- [ ] `apply_result()` method updating balance
- [ ] `balance` property for current bankroll
- [ ] `peak_balance` (high water mark) tracking
- [ ] `max_drawdown` calculation (largest decline from peak)
- [ ] `current_drawdown` (current decline from peak)
- [ ] `history` property returning balance after each hand
- [ ] `session_profit` property (current - starting)
- [ ] Unit tests for all tracking scenarios
- [ ] Tests for drawdown calculation accuracy

## Dependencies
Blocked by: #1

## Files to Create
- `src/let_it_ride/bankroll/tracker.py`
- `tests/unit/bankroll/test_tracker.py`

## Key Types
```python
class BankrollTracker:
    def __init__(self, starting_amount: float)
    
    def apply_result(self, amount: float) -> None
        """Apply hand result (positive = win, negative = loss)"""
    
    @property
    def balance(self) -> float
    
    @property
    def starting_balance(self) -> float
    
    @property
    def session_profit(self) -> float
    
    @property
    def peak_balance(self) -> float
    
    @property
    def max_drawdown(self) -> float
        """Largest peak-to-trough decline as absolute value"""
    
    @property
    def max_drawdown_pct(self) -> float
        """Largest peak-to-trough decline as percentage of peak"""
    
    @property
    def current_drawdown(self) -> float
    
    @property
    def history(self) -> list[float]
        """Balance after each transaction"""
```

## Estimated Scope
~150 lines'
fi

if [[ $START_ISSUE -le 16 && $END_ISSUE -ge 16 ]]; then
create_issue \
"#16: Flat Betting System" \
"bankroll,priority-critical" \
'## Description
Implement the flat (constant) betting system as the baseline, plus the betting system protocol.

## Acceptance Criteria
- [ ] `BettingSystem` protocol definition
- [ ] `BettingContext` dataclass with bankroll state info
- [ ] `FlatBetting` implementation returning constant base bet
- [ ] Validation that bet does not exceed available bankroll
- [ ] Returns reduced bet if bankroll insufficient for full bet
- [ ] Unit tests for normal operation
- [ ] Unit tests for insufficient bankroll scenarios

## Dependencies
Blocked by: #15

## Files to Create
- `src/let_it_ride/bankroll/betting_systems.py`
- `tests/unit/bankroll/test_betting_systems.py`

## Key Types
```python
@dataclass
class BettingContext:
    bankroll: float
    starting_bankroll: float
    session_profit: float
    last_result: float | None  # Last hand result
    streak: int  # Positive = wins, negative = losses
    hands_played: int

class BettingSystem(Protocol):
    def get_bet(self, context: BettingContext) -> float
    def record_result(self, result: float) -> None
    def reset(self) -> None

class FlatBetting:
    def __init__(self, base_bet: float)
    def get_bet(self, context: BettingContext) -> float
    def record_result(self, result: float) -> None
    def reset(self) -> None
```

## Estimated Scope
~100 lines'
fi

if [[ $START_ISSUE -le 17 && $END_ISSUE -ge 17 ]]; then
create_issue \
"#17: Progressive Betting Systems" \
"bankroll,priority-medium" \
'## Description
Implement progressive betting systems (Martingale, Paroli, D'\''Alembert, Fibonacci).

## Acceptance Criteria
- [ ] `MartingaleBetting` - double after loss, reset after win
  - Configurable loss multiplier (default 2.0)
  - Max bet cap (table limit)
  - Max progressions limit
- [ ] `ReverseMartingaleBetting` - double after win, reset after loss
  - Profit target streak for reset
- [ ] `ParoliBetting` - increase after win, reset after N wins
  - Configurable wins before reset
- [ ] `DAlembertBetting` - add unit after loss, subtract after win
  - Configurable unit size
  - Min bet floor
- [ ] `FibonacciBetting` - follow Fibonacci sequence on losses
  - Configurable base unit
  - Win regression (move back N positions)
  - Max sequence position
- [ ] All systems respect min/max bet limits
- [ ] All systems implement BettingSystem protocol
- [ ] Unit tests for each system'\''s progression logic
- [ ] Tests for bet cap enforcement

## Dependencies
Blocked by: #16

## Files to Modify
- `src/let_it_ride/bankroll/betting_systems.py`
- `tests/unit/bankroll/test_betting_systems.py`

## Key Types
```python
class MartingaleBetting:
    def __init__(
        self,
        base_bet: float,
        loss_multiplier: float = 2.0,
        max_bet: float = 500.0,
        max_progressions: int = 6,
    )

class ParoliBetting:
    def __init__(
        self,
        base_bet: float,
        win_multiplier: float = 2.0,
        wins_before_reset: int = 3,
        max_bet: float = 500.0,
    )

class DAlembertBetting:
    def __init__(
        self,
        base_bet: float,
        unit: float = 5.0,
        min_bet: float = 5.0,
        max_bet: float = 500.0,
    )

class FibonacciBetting:
    def __init__(
        self,
        base_unit: float = 5.0,
        win_regression: int = 2,
        max_bet: float = 500.0,
        max_position: int = 10,
    )
```

## Estimated Scope
~350 lines'
fi

if [[ $START_ISSUE -le 18 && $END_ISSUE -ge 18 ]]; then
create_issue \
"#18: Session State Management" \
"session,priority-critical" \
'## Description
Implement session lifecycle management with stop conditions.

## Acceptance Criteria
- [ ] `SessionConfig` dataclass with all session parameters
- [ ] `StopReason` enum (WIN_LIMIT, LOSS_LIMIT, MAX_HANDS, INSUFFICIENT_FUNDS, COMPLETED)
- [ ] `Session` class managing complete session state
- [ ] `should_stop()` method checking all stop conditions
- [ ] `play_hand()` method executing single hand via GameEngine
- [ ] `run_to_completion()` method running until stop condition
- [ ] Statistics accumulation (hands played, total wagered, etc.)
- [ ] Session outcome determination (WIN, LOSS, PUSH based on profit)
- [ ] Unit tests for all stop conditions
- [ ] Tests for session statistics accuracy

## Dependencies
Blocked by: #13, #15

## Files to Create
- `src/let_it_ride/simulation/session.py`
- `tests/unit/simulation/test_session.py`

## Key Types
```python
@dataclass
class SessionConfig:
    starting_bankroll: float
    base_bet: float
    win_limit: float | None
    loss_limit: float | None
    max_hands: int | None
    stop_on_insufficient_funds: bool = True

class StopReason(Enum):
    WIN_LIMIT = "win_limit"
    LOSS_LIMIT = "loss_limit"
    MAX_HANDS = "max_hands"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    SHOE_RESHUFFLE = "shoe_reshuffle"  # Optional: stop on reshuffle

class SessionOutcome(Enum):
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"

class Session:
    def __init__(
        self,
        config: SessionConfig,
        engine: GameEngine,
        betting_system: BettingSystem,
        bonus_strategy: BonusStrategy,
        bankroll: BankrollTracker,
    )
    
    def play_hand(self) -> HandResult
    def should_stop(self) -> bool
    def stop_reason(self) -> StopReason | None
    def run_to_completion(self) -> SessionResult
    
    @property
    def hands_played(self) -> int
    @property
    def is_complete(self) -> bool
```

## Estimated Scope
~250 lines'
fi

if [[ $START_ISSUE -le 19 && $END_ISSUE -ge 19 ]]; then
create_issue \
"#19: Session Result Data Structures" \
"session,priority-high" \
'## Description
Define comprehensive data structures for session results and hand records.

## Acceptance Criteria
- [ ] `HandRecord` dataclass with all per-hand fields matching requirements spec
- [ ] `SessionResult` dataclass with all summary fields matching requirements spec
- [ ] `to_dict()` methods for serialization
- [ ] `from_dict()` class methods for deserialization
- [ ] Hand distribution counting helper
- [ ] Proper typing for all fields
- [ ] Unit tests for serialization round-trip
- [ ] Tests for hand distribution counting

## Dependencies
Blocked by: #13

## Files to Create
- `src/let_it_ride/simulation/results.py`
- `tests/unit/simulation/test_results.py`

## Key Types
```python
@dataclass
class HandRecord:
    hand_id: int
    session_id: int
    shoe_id: int | None
    cards_player: str  # e.g., "Ah Kd Qs"
    cards_community: str
    decision_bet1: str
    decision_bet2: str
    final_hand_rank: str
    base_bet: float
    bets_at_risk: float
    main_payout: float
    bonus_bet: float
    bonus_hand_rank: str | None
    bonus_payout: float
    bankroll_after: float
    
    def to_dict(self) -> dict[str, Any]
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HandRecord"

@dataclass
class SessionResult:
    session_id: int
    starting_bankroll: float
    ending_bankroll: float
    net_result: float
    hands_played: int
    stop_reason: str
    peak_bankroll: float
    max_drawdown: float
    main_game_wagered: float
    main_game_won: float
    bonus_wagered: float
    bonus_won: float
    hand_distribution: dict[str, int]  # Hand type -> count
    outcome: str  # "win", "loss", "push"
    
    def to_dict(self) -> dict[str, Any]
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionResult"

def count_hand_distribution(results: list[HandResult]) -> dict[str, int]
```

## Estimated Scope
~200 lines'
fi

# ==============================================================================
# PHASE 4: SIMULATION INFRASTRUCTURE (Issues 20-24)
# ==============================================================================

if [[ $START_ISSUE -le 20 && $END_ISSUE -ge 20 ]]; then
create_issue \
"#20: Simulation Controller (Sequential)" \
"simulation,priority-critical" \
'## Description
Implement the main simulation controller for running multiple sessions sequentially.

## Acceptance Criteria
- [ ] `SimulationController` class orchestrating session execution
- [ ] `run()` method executing configured number of sessions
- [ ] Progress reporting via callback function
- [ ] Results aggregation into `SimulationResults`
- [ ] Support for seeded RNG ensuring reproducibility
- [ ] Session isolation (each session gets fresh state)
- [ ] Integration tests for multi-session runs
- [ ] Test that same seed produces identical results

## Dependencies
Blocked by: #18

## Files to Create
- `src/let_it_ride/simulation/controller.py`
- `tests/integration/test_controller.py`

## Key Types
```python
ProgressCallback = Callable[[int, int], None]  # (completed, total)

class SimulationController:
    def __init__(
        self,
        config: FullConfig,
        progress_callback: ProgressCallback | None = None,
    )
    
    def run(self) -> SimulationResults
    
    def _create_session(self, session_id: int, rng: random.Random) -> Session
    def _run_session(self, session: Session) -> SessionResult

@dataclass
class SimulationResults:
    config: FullConfig
    session_results: list[SessionResult]
    start_time: datetime
    end_time: datetime
    total_hands: int
```

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 21 && $END_ISSUE -ge 21 ]]; then
create_issue \
"#21: Parallel Session Execution" \
"simulation,priority-high" \
'## Description
Add parallel execution support using multiprocessing for improved throughput.

## Acceptance Criteria
- [ ] Worker pool management with configurable worker count
- [ ] "auto" option uses `os.cpu_count()`
- [ ] Session batching for parallel execution
- [ ] Progress aggregation across workers
- [ ] Proper RNG seeding per worker (avoid correlation between workers)
- [ ] Results merging from all workers
- [ ] Graceful handling of worker failures
- [ ] Integration tests verifying parallel correctness
- [ ] Test that parallel and sequential produce statistically equivalent results

## Dependencies
Blocked by: #20

## Files to Modify
- `src/let_it_ride/simulation/controller.py`

## Files to Create
- `src/let_it_ride/simulation/parallel.py`
- `tests/integration/test_parallel.py`

## Key Types
```python
class ParallelExecutor:
    def __init__(self, num_workers: int | Literal["auto"])
    
    def run_sessions(
        self,
        session_configs: list[tuple[int, SessionConfig]],  # (session_id, config)
        base_seed: int | None,
        progress_callback: ProgressCallback | None,
    ) -> list[SessionResult]

def worker_process(
    session_ids: list[int],
    config: FullConfig,
    worker_seed: int,
) -> list[SessionResult]
```

## RNG Seeding Strategy
```python
# Each worker gets a unique seed derived from base seed
worker_seed = base_seed + worker_id * 1_000_000 if base_seed else None
```

## Estimated Scope
~250 lines'
fi

if [[ $START_ISSUE -le 22 && $END_ISSUE -ge 22 ]]; then
create_issue \
"#22: Simulation Results Aggregation" \
"simulation,priority-critical" \
'## Description
Implement aggregation of results across all sessions into summary statistics.

## Acceptance Criteria
- [ ] `AggregateStatistics` dataclass with all summary metrics
- [ ] Session win rate calculation (profitable sessions / total)
- [ ] Expected value per hand ((total won - total wagered) / total hands)
- [ ] Main game and bonus game separate statistics
- [ ] Hand frequency distribution across all sessions
- [ ] `aggregate_results()` function processing list of SessionResults
- [ ] Support for incremental aggregation (for parallel merge)
- [ ] Unit tests for statistical calculations
- [ ] Tests with known data sets verifying accuracy

## Dependencies
Blocked by: #19

## Files to Create
- `src/let_it_ride/simulation/aggregation.py`
- `tests/unit/simulation/test_aggregation.py`

## Key Types
```python
@dataclass
class AggregateStatistics:
    # Session metrics
    total_sessions: int
    winning_sessions: int
    losing_sessions: int
    push_sessions: int
    session_win_rate: float
    
    # Hand metrics
    total_hands: int
    
    # Financial metrics
    total_wagered: float
    total_won: float
    net_result: float
    expected_value_per_hand: float
    
    # Main game breakdown
    main_wagered: float
    main_won: float
    main_ev_per_hand: float
    
    # Bonus breakdown
    bonus_wagered: float
    bonus_won: float
    bonus_ev_per_hand: float
    
    # Hand distribution
    hand_frequencies: dict[str, int]
    hand_frequency_pct: dict[str, float]
    
    # Session outcome distribution
    session_profit_mean: float
    session_profit_std: float
    session_profit_median: float
    session_profit_min: float
    session_profit_max: float

def aggregate_results(results: list[SessionResult]) -> AggregateStatistics

def merge_aggregates(agg1: AggregateStatistics, agg2: AggregateStatistics) -> AggregateStatistics
```

## Estimated Scope
~250 lines'
fi

if [[ $START_ISSUE -le 23 && $END_ISSUE -ge 23 ]]; then
create_issue \
"#23: Statistical Validation Module" \
"simulation,priority-high,analytics" \
'## Description
Implement validation that simulation results match theoretical probabilities.

## Acceptance Criteria
- [ ] Chi-square test for hand frequency distribution vs theoretical
- [ ] Theoretical probability constants for all hand types
- [ ] P-value calculation and significance reporting
- [ ] Expected value convergence testing (actual EV vs theoretical house edge)
- [ ] Confidence interval calculation for session win rate
- [ ] `ValidationReport` dataclass with all test results
- [ ] `validate_simulation()` function generating report
- [ ] Unit tests with known distributions
- [ ] Warning thresholds for suspicious deviations

## Dependencies
Blocked by: #22

## Files to Create
- `src/let_it_ride/analytics/validation.py`
- `tests/unit/analytics/test_validation.py`

## Key Types
```python
# Theoretical 5-card hand probabilities (from combinatorics)
THEORETICAL_HAND_PROBS: dict[str, float] = {
    "royal_flush": 0.00000154,
    "straight_flush": 0.0000139,
    "four_of_a_kind": 0.000240,
    "full_house": 0.00144,
    "flush": 0.00197,
    "straight": 0.00392,
    "three_of_a_kind": 0.0211,
    "two_pair": 0.0475,
    "pair": 0.423,  # All pairs
    "high_card": 0.501,
}

@dataclass
class ChiSquareResult:
    statistic: float
    p_value: float
    degrees_of_freedom: int
    is_valid: bool  # p_value > 0.05

@dataclass
class ValidationReport:
    chi_square_result: ChiSquareResult
    observed_frequencies: dict[str, float]
    expected_frequencies: dict[str, float]
    ev_actual: float
    ev_theoretical: float
    ev_deviation_pct: float
    session_win_rate: float
    session_win_rate_ci: tuple[float, float]  # 95% CI
    warnings: list[str]
    is_valid: bool

def validate_simulation(
    stats: AggregateStatistics,
    significance_level: float = 0.05,
) -> ValidationReport
```

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 24 && $END_ISSUE -ge 24 ]]; then
create_issue \
"#24: RNG Quality and Seeding" \
"simulation,priority-medium" \
'## Description
Implement proper RNG management for reproducibility and statistical quality.

## Acceptance Criteria
- [ ] `RNGManager` class for centralized seed management
- [ ] Unique seed derivation for parallel workers
- [ ] `create_rng()` factory method
- [ ] RNG state serialization for potential checkpointing
- [ ] Basic randomness quality validation (simple statistical tests)
- [ ] Support for cryptographic RNG option
- [ ] Unit tests for reproducibility (same seed = same results)
- [ ] Tests for worker seed independence

## Dependencies
Blocked by: #1

## Files to Create
- `src/let_it_ride/simulation/rng.py`
- `tests/unit/simulation/test_rng.py`

## Key Types
```python
class RNGManager:
    def __init__(self, base_seed: int | None = None)
    
    def create_rng(self) -> random.Random
        """Create a new RNG with derived seed"""
    
    def create_worker_rng(self, worker_id: int) -> random.Random
        """Create RNG for specific worker with guaranteed unique seed"""
    
    def get_state(self) -> dict[str, Any]
        """Serialize RNG state for checkpointing"""
    
    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "RNGManager"
        """Restore from serialized state"""
    
    @property
    def base_seed(self) -> int | None

def validate_rng_quality(rng: random.Random, sample_size: int = 10000) -> bool
    """Basic statistical tests for RNG quality"""
```

## Estimated Scope
~150 lines'
fi

# ==============================================================================
# PHASE 5: ANALYTICS AND REPORTING (Issues 25-30)
# ==============================================================================

if [[ $START_ISSUE -le 25 && $END_ISSUE -ge 25 ]]; then
create_issue \
"#25: Core Statistics Calculator" \
"analytics,priority-critical" \
'## Description
Implement calculation of all primary statistics from simulation results.

## Acceptance Criteria
- [ ] Session win rate with confidence interval (Wilson score or normal approx)
- [ ] Expected value per hand with confidence interval
- [ ] Variance and standard deviation of session outcomes
- [ ] Skewness and kurtosis of session profit distribution
- [ ] Percentile calculations (5th, 25th, 50th, 75th, 95th)
- [ ] Interquartile range
- [ ] Risk metrics (probability of specific loss levels)
- [ ] All calculations as pure functions
- [ ] Unit tests with known data sets
- [ ] Tests verifying numerical stability

## Dependencies
Blocked by: #22

## Files to Create
- `src/let_it_ride/analytics/statistics.py`
- `tests/unit/analytics/test_statistics.py`

## Key Types
```python
@dataclass
class ConfidenceInterval:
    lower: float
    upper: float
    level: float  # e.g., 0.95

@dataclass
class DistributionStats:
    mean: float
    std: float
    variance: float
    skewness: float
    kurtosis: float
    min: float
    max: float
    percentiles: dict[int, float]  # {5: value, 25: value, ...}
    iqr: float

@dataclass
class DetailedStatistics:
    session_win_rate: float
    session_win_rate_ci: ConfidenceInterval
    ev_per_hand: float
    ev_per_hand_ci: ConfidenceInterval
    session_profit_distribution: DistributionStats
    main_game_ev: float
    bonus_ev: float
    
def calculate_statistics(
    results: list[SessionResult],
    confidence_level: float = 0.95,
) -> DetailedStatistics

def wilson_score_interval(
    successes: int,
    trials: int,
    confidence: float = 0.95,
) -> ConfidenceInterval
```

## Estimated Scope
~250 lines'
fi

if [[ $START_ISSUE -le 26 && $END_ISSUE -ge 26 ]]; then
create_issue \
"#26: Strategy Comparison Analytics" \
"analytics,priority-high" \
'## Description
Implement statistical comparison between different strategies.

## Acceptance Criteria
- [ ] Side-by-side metrics comparison dataclass
- [ ] Statistical significance testing (two-sample t-test for session profits)
- [ ] Mann-Whitney U test for non-normal distributions
- [ ] Effect size calculation (Cohen'\''s d)
- [ ] Relative performance metrics (% improvement)
- [ ] Comparison report generation
- [ ] Support comparing 2+ strategies
- [ ] Unit tests for comparison logic
- [ ] Tests with known effect sizes

## Dependencies
Blocked by: #25

## Files to Create
- `src/let_it_ride/analytics/comparison.py`
- `tests/unit/analytics/test_comparison.py`

## Key Types
```python
@dataclass
class SignificanceTest:
    test_name: str  # "t-test", "mann-whitney"
    statistic: float
    p_value: float
    is_significant: bool

@dataclass
class EffectSize:
    cohens_d: float
    interpretation: str  # "small", "medium", "large"

@dataclass
class StrategyComparison:
    strategy_a_name: str
    strategy_b_name: str
    
    # Key metrics comparison
    win_rate_a: float
    win_rate_b: float
    win_rate_diff: float
    
    ev_a: float
    ev_b: float
    ev_diff: float
    
    # Statistical tests
    significance: SignificanceTest
    effect_size: EffectSize
    
    # Recommendation
    better_strategy: str | None  # None if not statistically significant
    confidence: str  # "high", "medium", "low"

def compare_strategies(
    results_a: list[SessionResult],
    results_b: list[SessionResult],
    name_a: str,
    name_b: str,
    significance_level: float = 0.05,
) -> StrategyComparison

def compare_multiple_strategies(
    results_dict: dict[str, list[SessionResult]],
) -> list[StrategyComparison]
```

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 27 && $END_ISSUE -ge 27 ]]; then
create_issue \
"#27: CSV Export" \
"reporting,priority-critical" \
'## Description
Implement CSV export for session summaries and aggregate statistics.

## Acceptance Criteria
- [ ] `export_sessions_csv()` - session summaries to CSV
- [ ] `export_aggregate_csv()` - aggregate statistics to CSV
- [ ] `export_hands_csv()` - optional per-hand detail export (large files)
- [ ] Configurable field selection
- [ ] Proper CSV escaping and quoting
- [ ] UTF-8 encoding with BOM option for Excel compatibility
- [ ] Integration tests verifying file output
- [ ] Tests for large file handling

## Dependencies
Blocked by: #22

## Files to Create
- `src/let_it_ride/analytics/export_csv.py`
- `tests/integration/test_export_csv.py`

## Key Types
```python
def export_sessions_csv(
    results: list[SessionResult],
    path: Path,
    fields: list[str] | None = None,  # None = all fields
) -> None

def export_aggregate_csv(
    stats: AggregateStatistics,
    path: Path,
) -> None

def export_hands_csv(
    hands: list[HandRecord],
    path: Path,
    fields: list[str] | None = None,
) -> None

class CSVExporter:
    def __init__(
        self,
        output_dir: Path,
        prefix: str = "simulation",
        include_bom: bool = True,
    )
    
    def export_all(
        self,
        results: SimulationResults,
        include_hands: bool = False,
    ) -> list[Path]
```

## Estimated Scope
~150 lines'
fi

if [[ $START_ISSUE -le 28 && $END_ISSUE -ge 28 ]]; then
create_issue \
"#28: JSON Export" \
"reporting,priority-high" \
'## Description
Implement JSON export with full configuration preservation.

## Acceptance Criteria
- [ ] Complete results JSON including all data
- [ ] Configuration embedded in output for reproducibility
- [ ] Pretty-print option for human readability
- [ ] Compact option for smaller file size
- [ ] Metadata section (timestamps, version, etc.)
- [ ] JSON schema documentation
- [ ] Custom encoder for dataclasses and enums
- [ ] Integration tests for file output
- [ ] Tests for round-trip (export then import)

## Dependencies
Blocked by: #22

## Files to Create
- `src/let_it_ride/analytics/export_json.py`
- `tests/integration/test_export_json.py`
- `docs/json_schema.md`

## Key Types
```python
def export_json(
    results: SimulationResults,
    path: Path,
    pretty: bool = True,
    include_config: bool = True,
    include_hands: bool = False,
) -> None

def load_results_json(path: Path) -> SimulationResults

class ResultsEncoder(json.JSONEncoder):
    """Custom encoder for simulation data types"""
    def default(self, obj: Any) -> Any
```

## JSON Structure
```json
{
  "metadata": {
    "version": "1.0",
    "generated_at": "2025-01-15T10:30:00Z",
    "simulator_version": "0.1.0"
  },
  "config": { ... },
  "aggregate_statistics": { ... },
  "session_results": [ ... ],
  "hands": [ ... ]  // optional
}
```

## Estimated Scope
~150 lines'
fi

if [[ $START_ISSUE -le 29 && $END_ISSUE -ge 29 ]]; then
create_issue \
"#29: Visualization - Session Outcome Histogram" \
"visualization,priority-medium" \
'## Description
Implement histogram visualization of session outcomes using matplotlib.

## Acceptance Criteria
- [ ] Session profit/loss distribution histogram
- [ ] Configurable bin count (auto or specified)
- [ ] Mean and median vertical markers
- [ ] Win rate annotation on chart
- [ ] Zero line (break-even) marker
- [ ] Title and axis labels
- [ ] Color coding (green for profit bins, red for loss bins)
- [ ] PNG and SVG export options
- [ ] Configurable figure size and DPI
- [ ] Integration test generating sample chart

## Dependencies
Blocked by: #22

## Files to Create
- `src/let_it_ride/analytics/visualizations/__init__.py`
- `src/let_it_ride/analytics/visualizations/histogram.py`
- `tests/integration/test_visualizations.py`

## Key Types
```python
@dataclass
class HistogramConfig:
    bins: int | str = "auto"
    figsize: tuple[float, float] = (10, 6)
    dpi: int = 150
    show_mean: bool = True
    show_median: bool = True
    show_zero_line: bool = True
    title: str = "Session Outcome Distribution"

def plot_session_histogram(
    results: list[SessionResult],
    config: HistogramConfig = HistogramConfig(),
) -> matplotlib.figure.Figure

def save_histogram(
    results: list[SessionResult],
    path: Path,
    format: Literal["png", "svg"] = "png",
    config: HistogramConfig = HistogramConfig(),
) -> None
```

## Estimated Scope
~150 lines'
fi

if [[ $START_ISSUE -le 30 && $END_ISSUE -ge 30 ]]; then
create_issue \
"#30: Visualization - Bankroll Trajectory" \
"visualization,priority-medium" \
'## Description
Implement bankroll trajectory line charts for sample sessions.

## Acceptance Criteria
- [ ] Multi-line chart showing N sample session trajectories
- [ ] Configurable number of sample sessions to display
- [ ] Random or deterministic session selection
- [ ] Win limit and loss limit horizontal reference lines
- [ ] Starting bankroll baseline
- [ ] Color gradient based on session outcome (green=win, red=loss)
- [ ] X-axis: hands played, Y-axis: bankroll
- [ ] Legend with session outcomes
- [ ] PNG and SVG export
- [ ] Integration test generating sample chart

## Dependencies
Blocked by: #29

## Files to Create
- `src/let_it_ride/analytics/visualizations/trajectory.py`

## Key Types
```python
@dataclass
class TrajectoryConfig:
    sample_sessions: int = 20
    figsize: tuple[float, float] = (12, 6)
    dpi: int = 150
    show_limits: bool = True
    alpha: float = 0.6  # Line transparency
    title: str = "Bankroll Trajectories"
    random_seed: int | None = None  # For reproducible sampling

def plot_bankroll_trajectories(
    results: list[SessionResult],
    bankroll_histories: list[list[float]],  # From BankrollTracker
    config: TrajectoryConfig = TrajectoryConfig(),
    win_limit: float | None = None,
    loss_limit: float | None = None,
) -> matplotlib.figure.Figure

def save_trajectory_chart(
    results: list[SessionResult],
    bankroll_histories: list[list[float]],
    path: Path,
    format: Literal["png", "svg"] = "png",
    config: TrajectoryConfig = TrajectoryConfig(),
) -> None
```

## Estimated Scope
~150 lines'
fi

# ==============================================================================
# PHASE 6: CLI AND INTEGRATION (Issues 31-35)
# ==============================================================================

if [[ $START_ISSUE -le 31 && $END_ISSUE -ge 31 ]]; then
create_issue \
"#31: CLI Entry Point" \
"cli,priority-critical" \
'## Description
Implement the main CLI using Click or Typer.

## Acceptance Criteria
- [ ] `let-it-ride` command registered as entry point
- [ ] `run` subcommand executing simulation from config file
- [ ] `validate` subcommand checking config file syntax and values
- [ ] `--config` / `-c` option for config file path
- [ ] `--output` / `-o` option for output directory override
- [ ] `--seed` option for random seed override
- [ ] `--sessions` option for session count override
- [ ] `--quiet` / `-q` flag for minimal output
- [ ] `--verbose` / `-v` flag for detailed output
- [ ] Progress bar display (disable with --quiet)
- [ ] Proper exit codes (0 = success, 1 = error)
- [ ] Integration tests for CLI invocation

## Dependencies
Blocked by: #8, #20

## Files to Create
- `src/let_it_ride/cli/__init__.py`
- `src/let_it_ride/cli/main.py`
- `tests/integration/test_cli.py`

## Key Types
```python
# Using Typer example
import typer

app = typer.Typer(
    name="let-it-ride",
    help="Let It Ride Strategy Simulator",
)

@app.command()
def run(
    config: Path = typer.Option(..., "--config", "-c", help="Configuration file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output directory"),
    seed: int = typer.Option(None, "--seed", help="Random seed override"),
    sessions: int = typer.Option(None, "--sessions", help="Session count override"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Run a simulation with the given configuration."""

@app.command()
def validate(
    config: Path = typer.Option(..., "--config", "-c", help="Configuration file"),
) -> None:
    """Validate a configuration file."""
```

## pyproject.toml Entry Point
```toml
[tool.poetry.scripts]
let-it-ride = "let_it_ride.cli.main:app"
```

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 32 && $END_ISSUE -ge 32 ]]; then
create_issue \
"#32: Console Output Formatting" \
"cli,priority-high" \
'## Description
Implement formatted console output for results summary using Rich.

## Acceptance Criteria
- [ ] Progress bar with ETA during simulation
- [ ] Summary statistics table after completion
- [ ] Colorized win/loss indicators (green/red)
- [ ] Hand frequency table
- [ ] Configuration summary at start
- [ ] Elapsed time and throughput display
- [ ] Verbosity levels (0=minimal, 1=normal, 2=detailed)
- [ ] Plain text fallback when Rich unavailable
- [ ] Unit tests for formatters

## Dependencies
Blocked by: #31

## Files to Create
- `src/let_it_ride/cli/formatters.py`
- `src/let_it_ride/cli/progress.py`
- `tests/unit/cli/test_formatters.py`

## Key Types
```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

class OutputFormatter:
    def __init__(self, verbosity: int = 1, use_color: bool = True)
    
    def print_config_summary(self, config: FullConfig) -> None
    def print_progress(self, completed: int, total: int) -> None
    def print_statistics(self, stats: DetailedStatistics) -> None
    def print_hand_frequencies(self, frequencies: dict[str, int]) -> None
    def print_completion(self, elapsed: float, total_hands: int) -> None

class ProgressTracker:
    def __init__(self, total: int, description: str = "Simulating")
    def update(self, completed: int) -> None
    def finish(self) -> None
```

## Estimated Scope
~150 lines'
fi

if [[ $START_ISSUE -le 33 && $END_ISSUE -ge 33 ]]; then
create_issue \
"#33: Sample Configuration Files" \
"documentation,priority-high" \
'## Description
Create comprehensive sample configuration files demonstrating all features.

## Acceptance Criteria
- [ ] `basic_strategy.yaml` - Basic strategy with flat betting baseline
- [ ] `conservative.yaml` - Conservative strategy, low risk
- [ ] `aggressive.yaml` - Aggressive strategy, high variance
- [ ] `multi_deck.yaml` - 6-deck shoe with penetration settings
- [ ] `bonus_comparison.yaml` - Comparing bonus betting strategies
- [ ] `progressive_betting.yaml` - Martingale and Paroli examples
- [ ] Each config fully documented with comments explaining every option
- [ ] All configs validated by test suite
- [ ] README in configs/ directory explaining each file

## Dependencies
Blocked by: #8

## Files to Create
- `configs/README.md`
- `configs/basic_strategy.yaml`
- `configs/conservative.yaml`
- `configs/aggressive.yaml`
- `configs/multi_deck.yaml`
- `configs/bonus_comparison.yaml`
- `configs/progressive_betting.yaml`

## Example: basic_strategy.yaml
```yaml
# Basic Strategy Baseline Configuration
# Uses mathematically optimal decisions with flat betting
# Good starting point for comparison studies

metadata:
  name: "Basic Strategy Baseline"
  description: "Optimal play with flat betting - baseline for comparisons"
  version: "1.0"

simulation:
  num_sessions: 100000
  hands_per_session: 200
  random_seed: 42  # For reproducibility
  workers: "auto"

deck:
  num_decks: 1

bankroll:
  starting_amount: 500.00
  base_bet: 5.00
  stop_conditions:
    win_limit: 250.00
    loss_limit: 200.00
    max_hands: 200
  betting_system:
    type: "flat"

strategy:
  type: "basic"

bonus_strategy:
  enabled: false

output:
  directory: "./results/basic_strategy"
  formats:
    csv:
      enabled: true
    json:
      enabled: true
```

## Estimated Scope
~300 lines (YAML)'
fi

if [[ $START_ISSUE -le 34 && $END_ISSUE -ge 34 ]]; then
create_issue \
"#34: End-to-End Integration Test" \
"testing,priority-critical" \
'## Description
Implement comprehensive end-to-end tests validating the complete simulation pipeline.

## Acceptance Criteria
- [ ] Test running 10,000 sessions with known seed
- [ ] Verify session win rate within expected range
- [ ] Verify hand frequency distribution passes chi-square test
- [ ] Test all output formats generated correctly (CSV, JSON)
- [ ] Test parallel and sequential produce statistically equivalent results
- [ ] Test configuration validation catches all documented error types
- [ ] Test CLI invocation end-to-end
- [ ] Test with each sample configuration file
- [ ] Performance assertion (minimum hands/second)
- [ ] Memory usage validation

## Dependencies
Blocked by: All previous issues (this is final integration)

## Files to Create
- `tests/e2e/__init__.py`
- `tests/e2e/test_full_simulation.py`
- `tests/e2e/test_output_formats.py`
- `tests/e2e/test_cli_e2e.py`
- `tests/e2e/test_sample_configs.py`

## Key Tests
```python
def test_basic_strategy_simulation():
    """Run full simulation and verify results are statistically valid."""
    
def test_reproducibility():
    """Same seed produces identical results."""
    
def test_parallel_equivalence():
    """Parallel and sequential produce equivalent distributions."""
    
def test_all_sample_configs():
    """Each sample config runs without error."""
    
def test_output_file_generation():
    """All configured output files are created and valid."""
    
def test_statistical_validity():
    """Hand frequencies match theoretical within tolerance."""
    
def test_performance_threshold():
    """Simulation meets minimum throughput requirement."""
```

## Estimated Scope
~300 lines'
fi

if [[ $START_ISSUE -le 35 && $END_ISSUE -ge 35 ]]; then
create_issue \
"#35: Performance Optimization and Benchmarking" \
"performance,priority-medium" \
'## Description
Profile and optimize to meet performance targets (100k hands/second).

## Acceptance Criteria
- [ ] Benchmark script measuring hands/second
- [ ] Memory profiling for large simulations
- [ ] Profile-guided identification of hot paths
- [ ] Optimization of hand evaluation (consider lookup tables or numpy)
- [ ] Optimization of deck shuffling
- [ ] Memory usage validation (<4GB for 10M hands)
- [ ] Performance regression test (fail if below threshold)
- [ ] Benchmark results documented

## Dependencies
Blocked by: #34

## Files to Create
- `benchmarks/__init__.py`
- `benchmarks/benchmark_throughput.py`
- `benchmarks/benchmark_memory.py`
- `benchmarks/profile_hotspots.py`
- `docs/performance.md`

## Key Benchmarks
```python
def benchmark_hand_evaluation():
    """Measure hand evaluation throughput."""
    
def benchmark_deck_operations():
    """Measure shuffle and deal throughput."""
    
def benchmark_full_simulation():
    """Measure end-to-end simulation throughput."""
    
def profile_simulation():
    """Generate cProfile output for analysis."""
    
def measure_memory_usage():
    """Track memory during large simulation."""
```

## Performance Targets
- Hand evaluation: >500,000 hands/second
- Full simulation: >100,000 hands/second  
- Memory: <4GB for 10M hand simulation
- Startup time: <2 seconds

## Optimization Strategies to Consider
1. Hand evaluation lookup tables
2. Numpy for batch operations
3. `__slots__` on hot dataclasses
4. Cython for critical paths (if needed)
5. Memory-efficient result storage

## Estimated Scope
~200 lines'
fi

# ==============================================================================
# PHASE 7: ADVANCED FEATURES (Issues 36-40)
# ==============================================================================

if [[ $START_ISSUE -le 36 && $END_ISSUE -ge 36 ]]; then
create_issue \
"#36: Composition-Dependent Strategy" \
"advanced,priority-low,strategy" \
'## Description
Implement strategy that adjusts decisions based on remaining shoe composition.

## Acceptance Criteria
- [ ] Track high card ratio in shoe (10, J, Q, K, A)
- [ ] `CompositionDependentStrategy` extending basic strategy
- [ ] Configurable thresholds for adjustment
- [ ] More aggressive (ride more) when shoe is rich in high cards
- [ ] More conservative (pull more) when shoe is poor in high cards
- [ ] Only active for multi-deck shoes
- [ ] Falls back to basic strategy for single deck
- [ ] Unit tests for adjustment logic
- [ ] Integration tests with shoe simulation

## Dependencies
Blocked by: #3, #10

## Files to Create
- `src/let_it_ride/strategy/composition_dependent.py`
- `tests/unit/strategy/test_composition_dependent.py`

## Key Types
```python
@dataclass
class CompositionThresholds:
    high_card_rich: float = 0.52  # Ride more above this
    high_card_poor: float = 0.48  # Pull more below this
    track_cards: list[str] = field(default_factory=lambda: ["T", "J", "Q", "K", "A"])

class CompositionDependentStrategy:
    def __init__(
        self,
        base_strategy: Strategy,
        thresholds: CompositionThresholds,
    )
    
    def decide_bet1(
        self,
        analysis: HandAnalysis,
        context: StrategyContext,
    ) -> Decision
    
    def decide_bet2(
        self,
        analysis: HandAnalysis,
        context: StrategyContext,
    ) -> Decision
    
    def _should_adjust_aggressive(self, context: StrategyContext) -> bool
    def _should_adjust_conservative(self, context: StrategyContext) -> bool
```

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 37 && $END_ISSUE -ge 37 ]]; then
create_issue \
"#37: Streak-Based Bonus Strategy" \
"advanced,priority-low,strategy" \
'## Description
Implement bonus betting that adjusts based on win/loss streaks.

## Acceptance Criteria
- [ ] Track main game and bonus streaks separately
- [ ] `StreakBasedBonusStrategy` with configurable triggers
- [ ] Trigger types: main_loss, main_win, bonus_loss, bonus_win, any_loss, any_win
- [ ] Actions: increase, decrease, multiply, stop, start
- [ ] Configurable streak length to trigger
- [ ] Reset conditions
- [ ] Max multiplier cap
- [ ] Unit tests for all streak scenarios
- [ ] Tests for reset behavior

## Dependencies
Blocked by: #14

## Files to Modify
- `src/let_it_ride/strategy/bonus.py`
- `tests/unit/strategy/test_bonus.py`

## Key Types
```python
@dataclass
class StreakConfig:
    trigger: Literal["main_loss", "main_win", "bonus_loss", "bonus_win", "any_loss", "any_win"]
    streak_length: int
    action: Literal["increase", "decrease", "multiply", "stop", "start"]
    action_value: float
    reset_on: str
    max_multiplier: float = 5.0

class StreakBasedBonusStrategy:
    def __init__(
        self,
        base_amount: float,
        config: StreakConfig,
    )
    
    def get_bonus_bet(self, context: BonusContext) -> float
    def record_result(self, main_won: bool, bonus_won: bool | None) -> None
    def reset(self) -> None
    
    @property
    def current_streak(self) -> int
    @property
    def current_multiplier(self) -> float
```

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 38 && $END_ISSUE -ge 38 ]]; then
create_issue \
"#38: Risk of Ruin Calculator" \
"analytics,priority-low" \
'## Description
Implement risk of ruin calculation for various bankroll levels.

## Acceptance Criteria
- [ ] Analytical risk of ruin formula (if applicable)
- [ ] Monte Carlo risk of ruin estimation
- [ ] Calculate probability of losing X% of bankroll
- [ ] Risk curves for different bankroll multiples of base bet
- [ ] `RiskOfRuinReport` with detailed breakdown
- [ ] Visualization of risk curves
- [ ] Unit tests with known risk scenarios
- [ ] Tests for convergence of Monte Carlo estimates

## Dependencies
Blocked by: #25

## Files to Create
- `src/let_it_ride/analytics/risk_of_ruin.py`
- `src/let_it_ride/analytics/visualizations/risk_curves.py`
- `tests/unit/analytics/test_risk_of_ruin.py`

## Key Types
```python
@dataclass
class RiskOfRuinResult:
    bankroll_units: int  # Bankroll as multiple of base bet
    ruin_probability: float  # Probability of losing entire bankroll
    confidence_interval: ConfidenceInterval
    half_bankroll_risk: float  # Probability of losing 50%
    sessions_simulated: int

@dataclass  
class RiskOfRuinReport:
    base_bet: float
    results: list[RiskOfRuinResult]  # For each bankroll level

def calculate_risk_of_ruin(
    session_results: list[SessionResult],
    bankroll_units: list[int],  # e.g., [20, 40, 60, 80, 100]
    simulations_per_level: int = 10000,
) -> RiskOfRuinReport

def plot_risk_curves(
    report: RiskOfRuinReport,
    path: Path,
) -> None
```

## Estimated Scope
~200 lines'
fi

if [[ $START_ISSUE -le 39 && $END_ISSUE -ge 39 ]]; then
create_issue \
"#39: HTML Report Generation" \
"reporting,priority-low" \
'## Description
Implement HTML report generation with embedded visualizations.

## Acceptance Criteria
- [ ] Self-contained HTML report (no external dependencies)
- [ ] Embedded Plotly charts for interactivity
- [ ] Configuration summary section
- [ ] Statistics tables with formatting
- [ ] Hand frequency comparison (actual vs theoretical)
- [ ] Session outcome histogram
- [ ] Bankroll trajectory samples
- [ ] Template-based generation using Jinja2
- [ ] Responsive design (mobile-friendly)
- [ ] Integration tests for report generation

## Dependencies
Blocked by: #29, #30

## Files to Create
- `src/let_it_ride/analytics/export_html.py`
- `src/let_it_ride/analytics/templates/report.html.j2`
- `src/let_it_ride/analytics/templates/styles.css`
- `tests/integration/test_export_html.py`

## Key Types
```python
@dataclass
class HTMLReportConfig:
    title: str = "Let It Ride Simulation Report"
    include_charts: bool = True
    chart_library: Literal["plotly", "chartjs"] = "plotly"
    include_config: bool = True
    include_raw_data: bool = False

def generate_html_report(
    results: SimulationResults,
    stats: DetailedStatistics,
    output_path: Path,
    config: HTMLReportConfig = HTMLReportConfig(),
) -> None

class HTMLReportGenerator:
    def __init__(self, template_dir: Path | None = None)
    def render(
        self,
        results: SimulationResults,
        stats: DetailedStatistics,
        config: HTMLReportConfig,
    ) -> str
```

## Estimated Scope
~300 lines'
fi

if [[ $START_ISSUE -le 40 && $END_ISSUE -ge 40 ]]; then
create_issue \
"#40: Documentation and User Guide" \
"documentation,priority-medium" \
'## Description
Create comprehensive documentation for installation, usage, and strategy reference.

## Acceptance Criteria
- [ ] Installation guide (Poetry, pip, from source)
- [ ] Quick start tutorial (run first simulation in 5 minutes)
- [ ] Configuration reference (all options documented with examples)
- [ ] Strategy guide with basic strategy charts
- [ ] Bonus betting strategy guide
- [ ] Output format documentation
- [ ] API documentation for library usage
- [ ] Example workflows (common use cases)
- [ ] Troubleshooting section
- [ ] Contributing guide

## Dependencies
Blocked by: All previous issues

## Files to Create
- `docs/index.md`
- `docs/installation.md`
- `docs/quickstart.md`
- `docs/configuration.md`
- `docs/strategies.md`
- `docs/bonus_strategies.md`
- `docs/output_formats.md`
- `docs/api.md`
- `docs/examples.md`
- `docs/troubleshooting.md`
- `CONTRIBUTING.md`

## Documentation Outline

### installation.md
- System requirements
- Poetry installation
- pip installation
- Development setup
- Verifying installation

### quickstart.md
- Your first simulation
- Understanding the output
- Modifying parameters
- Next steps

### configuration.md
- File structure
- Simulation settings
- Deck configuration
- Bankroll settings
- Strategy configuration
- Bonus strategy configuration
- Output settings
- Complete example

### strategies.md
- Basic strategy explanation
- Basic strategy charts (Bet 1 and Bet 2)
- Conservative strategy
- Aggressive strategy
- Custom strategies
- Composition-dependent strategy

## Estimated Scope
~500 lines (documentation)'
fi

echo "=================================================="
echo "Issue creation complete!"
echo "Created issues $START_ISSUE through $END_ISSUE"
