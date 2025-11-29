# Requirements Document: Let It Ride Strategy Simulator
## Version 1.1

---

## 1. Introduction

### 1.1 Purpose
This document defines the requirements for a Python application designed to simulate the casino card game "Let It Ride" and analyze various play and betting strategies to identify approaches that maximize the probability of profitable sessions.

### 1.2 Scope
The application will simulate millions of hands under various strategic conditions, track session outcomes, and provide statistical analysis to identify optimal play decisions and bankroll management approaches.

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Session** | A defined period of play with a starting bankroll and ending condition |
| **Base Bet** | The equal amount wagered on each of the three betting circles |
| **Let It Ride** | Decision to leave a bet in play |
| **Pull** | Decision to withdraw a bet |
| **Qualifying Hand** | A hand that pays (typically pair of 10s or better) |
| **Shoe** | One or more decks shuffled together for dealing |
| **Penetration** | Percentage of shoe dealt before reshuffling |

---

## 2. Game Rules Reference

### 2.1 Core Game Mechanics
The application must accurately implement standard Let It Ride rules:

1. Player places three equal bets (positions 1, 2, and 3)
2. Player receives 3 cards face down
3. Two community cards are dealt face down
4. **Decision Point 1**: After viewing 3-card hand, player may pull Bet 1 or let it ride
5. **First Community Card** is revealed (4 cards now visible)
6. **Decision Point 2**: Player may pull Bet 2 or let it ride
7. **Second Community Card** is revealed (final 5-card hand)
8. Bet 3 always remains in play
9. All remaining bets pay according to the paytable

### 2.2 Standard Paytable
The application must support configurable paytables. Default paytable:

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
| Pair of 10s or Better | 1:1 |
| All Other | Loss |

### 2.3 Deck Configuration

#### 2.3.1 Single Deck Mode
- Standard 52-card deck
- Reshuffled after each hand
- Baseline for comparison

#### 2.3.2 Multi-Deck Shoe Mode
- Support for 2, 4, 6, or 8 deck shoes
- Configurable penetration (typically 50-75%)
- Reshuffle when cut card reached
- Track dealt cards for composition analysis

### 2.4 Three Card Bonus Rules

#### 2.4.1 Core Mechanics
The Three Card Bonus is an optional side bet placed before cards are dealt:

1. Player places optional bonus bet (typically $1-$5, may have table maximum)
2. Bonus bet is evaluated based **only** on the player's initial 3 cards
3. Payout is independent of main game outcome and pull/ride decisions
4. Bonus bet resolves immediately after player views initial 3 cards

#### 2.4.2 Three Card Bonus Paytable (Default: Paytable B)

| Hand | Payout |
|------|--------|
| Mini Royal (AKQ suited) | 100:1 |
| Straight Flush | 40:1 |
| Three of a Kind | 30:1 |
| Straight | 5:1 |
| Flush | 4:1 |
| Pair | 1:1 |
| All Other | Loss |

**House Edge: ~3.5%**

#### 2.4.3 Alternative Bonus Paytables (Configurable)

**Paytable A (Lower Volatility):**

| Hand | Payout |
|------|--------|
| Mini Royal (AKQ suited) | 50:1 |
| Straight Flush | 40:1 |
| Three of a Kind | 30:1 |
| Straight | 6:1 |
| Flush | 3:1 |
| Pair | 1:1 |

**House Edge: ~2.4%**

**Paytable C (Progressive):**

| Hand | Payout |
|------|--------|
| Mini Royal (AKQ suited) | Progressive Jackpot |
| Straight Flush | 200:1 |
| Three of a Kind | 30:1 |
| Straight | 6:1 |
| Flush | 4:1 |
| Pair | 1:1 |

**House Edge: Variable based on jackpot**

#### 2.4.4 Three Card Hand Rankings

| Rank | Hand | Combinations | Probability |
|------|------|--------------|-------------|
| 1 | Mini Royal (AKQ suited) | 4 | 0.0181% |
| 2 | Straight Flush | 44 | 0.199% |
| 3 | Three of a Kind | 52 | 0.235% |
| 4 | Straight | 720 | 3.26% |
| 5 | Flush | 1,096 | 4.96% |
| 6 | Pair | 3,744 | 16.94% |
| 7 | High Card | 16,440 | 74.39% |
| **Total** | | **22,100** | **100%** |

---

## 3. Functional Requirements

### 3.1 Game Engine (FR-100)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-101 | Implement standard 52-card deck with proper shuffling (Fisher-Yates or cryptographic RNG) | Must |
| FR-102 | Deal cards according to Let It Ride rules | Must |
| FR-103 | Accurately evaluate 5-card poker hands | Must |
| FR-104 | Calculate payouts based on configurable paytable | Must |
| FR-105 | Support configurable house rules/variations | Should |
| FR-106 | Track all dealt cards for statistical validation | Must |
| FR-107 | Implement multi-deck shoe (2, 4, 6, 8 decks) | Must |
| FR-108 | Support configurable shoe penetration | Must |
| FR-109 | Track shoe composition for analysis | Must |
| FR-110 | Implement cut card mechanics for reshuffle trigger | Must |

### 3.2 Strategy Engine (FR-200)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-201 | Implement "basic strategy" (mathematically optimal pull/ride decisions) | Must |
| FR-202 | Support custom strategy definitions via configuration | Must |
| FR-203 | Allow strategy comparison (A/B testing multiple strategies) | Must |
| FR-204 | Implement "always let it ride" baseline strategy | Must |
| FR-205 | Implement "always pull" baseline strategy | Must |
| FR-206 | Support conditional strategies based on hand potential | Should |
| FR-207 | Support composition-dependent strategy (multi-deck) | Should |
| FR-208 | Support machine learning/genetic algorithm strategy discovery | Could |

### 3.3 Betting/Bankroll Management (FR-300)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-301 | Track player bankroll across hands and sessions | Must |
| FR-302 | Support flat betting (constant base bet) | Must |
| FR-303 | Support proportional betting (bet % of bankroll) | Should |
| FR-304 | Support progressive betting systems (Martingale, Paroli, etc.) | Should |
| FR-305 | Define session win/loss limits | Must |
| FR-306 | Define session time/hand limits | Must |
| FR-307 | Track "high water mark" and drawdown | Should |

### 3.4 Session Management (FR-400)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-401 | Define session parameters (starting bankroll, bet size, stop conditions) | Must |
| FR-402 | Run multiple independent sessions for statistical validity | Must |
| FR-403 | Support parallel session execution | Should |
| FR-404 | Define win/loss session outcomes | Must |
| FR-405 | Track session duration (hands played) | Must |

### 3.5 Simulation Engine (FR-500)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-501 | Execute configurable number of simulations (target: 10M+ hands) | Must |
| FR-502 | Support batch execution with progress reporting | Must |
| FR-503 | Checkpoint/resume long-running simulations | Could |
| FR-504 | Validate simulation accuracy against known probabilities | Must |
| FR-505 | Support seeded RNG for reproducibility | Must |
| FR-506 | Support single-deck and multi-deck simulation modes | Must |

### 3.6 Analytics & Reporting (FR-600)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-601 | Calculate win/loss session ratios | Must |
| FR-602 | Calculate expected value per hand | Must |
| FR-603 | Calculate variance and standard deviation | Must |
| FR-604 | Generate probability distributions (session outcomes) | Must |
| FR-605 | Compare strategies with statistical significance testing | Should |
| FR-606 | Calculate risk of ruin for various bankroll levels | Should |
| FR-607 | Export results to CSV/JSON | Must |
| FR-608 | Generate visualization charts (matplotlib/plotly) | Should |
| FR-609 | Calculate hand frequency distribution vs. theoretical | Must |
| FR-610 | Compare single-deck vs. multi-deck outcomes | Must |

### 3.7 Three Card Bonus Engine (FR-700)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-701 | Accurately evaluate 3-card poker hands | Must |
| FR-702 | Support multiple bonus paytables (configurable) | Must |
| FR-703 | Calculate bonus bet payouts independently of main game | Must |
| FR-704 | Track bonus bet results separately from main game results | Must |
| FR-705 | Support progressive jackpot tracking (simulated) | Could |
| FR-706 | Calculate theoretical house edge for each paytable | Must |
| FR-710 | Implement "always bet bonus" baseline strategy | Must |
| FR-711 | Implement "never bet bonus" baseline strategy | Must |
| FR-712 | Implement proportional bonus betting (% of base bet) | Must |
| FR-713 | Implement bankroll-conditional bonus betting | Should |
| FR-714 | Implement session-outcome-conditional bonus betting | Should |
| FR-715 | Implement streak-based bonus betting | Should |
| FR-716 | Support custom bonus betting rules via configuration | Must |

---

## 4. Non-Functional Requirements

### 4.1 Performance (NFR-100)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-101 | Simulation throughput | ≥100,000 hands/second |
| NFR-102 | Memory efficiency | <4GB RAM for 10M hand simulation |
| NFR-103 | Support multi-core parallelization | Scale to available CPU cores |

### 4.2 Reliability (NFR-200)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-201 | Hand evaluation accuracy | 100% (validated against test suite) |
| NFR-202 | RNG quality | Pass statistical randomness tests |
| NFR-203 | Payout calculation accuracy | 100% |

### 4.3 Maintainability (NFR-300)

| ID | Requirement |
|----|-------------|
| NFR-301 | Modular architecture (separate game, strategy, simulation, analytics) |
| NFR-302 | Comprehensive unit test coverage (≥90%) |
| NFR-303 | Type hints throughout codebase |
| NFR-304 | Documented API and configuration options |

---

## 5. Strategy Configuration Reference

This section provides complete documentation for all strategy configuration options. Strategies are defined in YAML configuration files and control all aspects of gameplay decisions.

### 5.1 Configuration File Structure

```yaml
# let_it_ride_config.yaml
# Complete strategy configuration file

metadata:
  name: "Strategy Configuration Name"
  description: "Description of this configuration"
  version: "1.0"
  author: "Author Name"
  created: "2025-01-15"

simulation:
  # ... simulation parameters

deck:
  # ... deck configuration

bankroll:
  # ... bankroll management

strategy:
  # ... main game strategy

bonus_strategy:
  # ... three card bonus strategy

paytables:
  # ... payout configurations

output:
  # ... reporting options
```

### 5.2 Simulation Configuration

```yaml
simulation:
  # Number of complete sessions to simulate
  # Type: integer, Required: yes
  # Range: 1 - 100,000,000
  num_sessions: 100000
  
  # Maximum hands per session (before other stop conditions)
  # Type: integer, Required: yes
  # Range: 1 - 10,000
  hands_per_session: 200
  
  # Random seed for reproducibility
  # Type: integer or null, Required: no
  # Use null for true randomness, integer for reproducible results
  random_seed: 42
  
  # Number of parallel workers for simulation
  # Type: integer or "auto", Required: no
  # "auto" uses all available CPU cores
  # Default: "auto"
  workers: "auto"
  
  # Progress reporting interval (sessions)
  # Type: integer, Required: no
  # Default: 10000
  progress_interval: 10000
  
  # Enable detailed hand logging (warning: large output)
  # Type: boolean, Required: no
  # Default: false
  detailed_logging: false
```

### 5.3 Deck Configuration

```yaml
deck:
  # Number of decks in shoe
  # Type: integer, Required: yes
  # Values: 1, 2, 4, 6, 8
  num_decks: 1
  
  # Shoe penetration before reshuffle (multi-deck only)
  # Type: float, Required: if num_decks > 1
  # Range: 0.25 - 0.90
  # Represents percentage of shoe dealt before cut card
  penetration: 0.75
  
  # Shuffle algorithm
  # Type: string, Required: no
  # Values: "fisher_yates", "cryptographic"
  # Default: "fisher_yates"
  shuffle_algorithm: "fisher_yates"
  
  # Track composition for analysis
  # Type: boolean, Required: no
  # Default: true for multi-deck, false for single
  track_composition: true
```

### 5.4 Bankroll Configuration

```yaml
bankroll:
  # Starting bankroll in dollars
  # Type: float, Required: yes
  # Range: > 0
  starting_amount: 500.00
  
  # Base bet amount (each of 3 betting circles)
  # Type: float, Required: yes
  # Range: > 0
  # Note: Total initial wager = base_bet * 3
  base_bet: 5.00
  
  # Session stop conditions (all optional, first triggered ends session)
  stop_conditions:
    # Stop when profit reaches this amount
    # Type: float or null
    win_limit: 250.00
    
    # Stop when loss reaches this amount
    # Type: float or null
    loss_limit: 200.00
    
    # Stop after this many hands regardless of outcome
    # Type: integer or null
    max_hands: 200
    
    # Stop after this duration (minutes, for realistic session modeling)
    # Type: integer or null
    max_duration_minutes: null
    
    # Stop if bankroll drops below minimum bet requirement
    # Type: boolean
    # Default: true
    stop_on_insufficient_funds: true
  
  # Betting progression system
  betting_system:
    # Type of betting progression
    # Type: string, Required: yes
    # Values: "flat", "proportional", "martingale", "reverse_martingale", 
    #         "paroli", "dalembert", "fibonacci", "custom"
    type: "flat"
    
    # Configuration for each betting system type:
    
    # --- flat ---
    # No additional configuration needed; uses base_bet always
    
    # --- proportional ---
    proportional:
      # Bet this percentage of current bankroll
      # Type: float, Range: 0.001 - 0.50
      bankroll_percentage: 0.03
      
      # Minimum bet floor
      # Type: float
      min_bet: 5.00
      
      # Maximum bet ceiling
      # Type: float
      max_bet: 100.00
      
      # Round bets to nearest increment
      # Type: float
      round_to: 1.00
    
    # --- martingale ---
    martingale:
      # Multiplier after loss
      # Type: float, typical: 2.0
      loss_multiplier: 2.0
      
      # Reset to base bet after win
      # Type: boolean
      reset_on_win: true
      
      # Maximum bet cap (table limit simulation)
      # Type: float
      max_bet: 500.00
      
      # Maximum consecutive progressions
      # Type: integer
      max_progressions: 6
    
    # --- reverse_martingale ---
    reverse_martingale:
      # Multiplier after win
      # Type: float
      win_multiplier: 2.0
      
      # Reset to base bet after loss
      # Type: boolean
      reset_on_loss: true
      
      # Take profit after N consecutive wins
      # Type: integer
      profit_target_streak: 3
      
      # Maximum bet cap
      # Type: float
      max_bet: 500.00
    
    # --- paroli ---
    paroli:
      # Multiplier after win
      # Type: float
      win_multiplier: 2.0
      
      # Number of wins before reset
      # Type: integer
      wins_before_reset: 3
      
      # Maximum bet cap
      # Type: float
      max_bet: 500.00
    
    # --- dalembert ---
    dalembert:
      # Unit to add after loss
      # Type: float
      unit: 5.00
      
      # Unit to subtract after win
      # Type: float
      decrease_unit: 5.00
      
      # Minimum bet floor
      # Type: float
      min_bet: 5.00
      
      # Maximum bet cap
      # Type: float
      max_bet: 500.00
    
    # --- fibonacci ---
    fibonacci:
      # Base unit for sequence
      # Type: float
      unit: 5.00
      
      # Move back N positions after win
      # Type: integer
      win_regression: 2
      
      # Maximum bet cap
      # Type: float
      max_bet: 500.00
      
      # Maximum sequence position
      # Type: integer
      max_position: 10
    
    # --- custom ---
    custom:
      # Python expression evaluated for bet sizing
      # Available variables: bankroll, base_bet, last_result, 
      #                      streak, session_profit, hands_played
      # Type: string (Python expression)
      expression: "base_bet * (1.5 if streak > 2 and last_result == 'win' else 1.0)"
      
      # Minimum bet floor
      # Type: float
      min_bet: 5.00
      
      # Maximum bet cap
      # Type: float
      max_bet: 500.00
```

### 5.5 Main Game Strategy Configuration

```yaml
strategy:
  # Strategy type selection
  # Type: string, Required: yes
  # Values: "basic", "always_ride", "always_pull", "conservative", 
  #         "aggressive", "composition_dependent", "custom"
  type: "basic"
  
  # Configuration for each strategy type:
  
  # --- basic ---
  # Mathematically optimal strategy (no additional configuration)
  # Implements standard basic strategy charts (see Section 5.5.1)
  
  # --- always_ride ---
  # Never pull bets (maximum variance baseline)
  # No additional configuration
  
  # --- always_pull ---
  # Always pull bets 1 and 2 (minimum variance baseline)
  # No additional configuration
  
  # --- conservative ---
  conservative:
    # Only let it ride with made paying hands
    # Type: boolean
    made_hands_only: true
    
    # Minimum hand strength to ride (1-10 scale)
    # 1 = any pair, 10 = royal flush only
    # Type: integer
    min_strength_bet1: 7  # three of a kind or better
    min_strength_bet2: 5  # two pair or better
  
  # --- aggressive ---
  aggressive:
    # Let it ride with any draw
    # Type: boolean
    ride_on_draws: true
    
    # Include inside straights
    # Type: boolean
    include_gutshots: true
    
    # Include backdoor flush draws
    # Type: boolean
    include_backdoor_flush: true
  
  # --- composition_dependent ---
  # Adjusts strategy based on remaining deck composition (multi-deck)
  composition_dependent:
    # Enable for multi-deck shoes only
    # Type: boolean
    enabled: true
    
    # Adjustment factors for rich/poor deck
    # Increase ride frequency when deck is rich in high cards
    high_card_threshold: 0.52  # ride more when >52% high cards remain
    low_card_threshold: 0.48   # pull more when <48% high cards remain
    
    # Specific card tracking
    track_cards:
      - "T"  # Tens
      - "J"  # Jacks
      - "Q"  # Queens
      - "K"  # Kings
      - "A"  # Aces
  
  # --- custom ---
  custom:
    # Define custom rules for each decision point
    # Rules are evaluated in order; first match determines action
    
    bet1_rules:
      # Rule format: condition -> action
      # Conditions use hand analysis variables (see Section 5.5.2)
      
      - condition: "has_paying_hand"
        action: "ride"
        
      - condition: "is_royal_draw and suited_high_cards >= 3"
        action: "ride"
        
      - condition: "is_straight_flush_draw and gaps <= 1"
        action: "ride"
        
      - condition: "is_flush_draw and high_cards >= 2"
        action: "ride"
        
      - condition: "is_open_straight_draw and high_cards >= 1"
        action: "ride"
        
      # Default action if no rules match
      - condition: "default"
        action: "pull"
    
    bet2_rules:
      - condition: "has_paying_hand"
        action: "ride"
        
      - condition: "is_flush_draw"
        action: "ride"
        
      - condition: "is_open_straight_draw and high_cards >= 1"
        action: "ride"
        
      - condition: "is_inside_straight_draw and high_cards >= 4"
        action: "ride"
        
      - condition: "default"
        action: "pull"
```

#### 5.5.1 Basic Strategy Reference

**Bet 1 Decision (3 cards visible):**

LET IT RIDE when holding:

- Any paying hand (pair of 10s or better, three of a kind)
- Three to a Royal Flush (10-J-Q, 10-J-K, 10-Q-K, J-Q-K, J-Q-A, J-K-A, Q-K-A suited)
- Three suited cards in sequence (except A-2-3, 2-3-4)
- Three to a straight flush, spread 4 (5-7-8 suited), with at least one high card (10+)
- Three to a straight flush, spread 5 (5-7-9 suited), with at least two high cards

PULL on all other hands.

**Bet 2 Decision (4 cards visible):**

LET IT RIDE when holding:

- Any paying hand (pair of 10s or better, two pair, three of a kind, etc.)
- Four to a flush
- Four to an outside straight with at least one high card (10+)
- Four to an inside straight with four high cards (10-J-Q-K)

PULL on all other hands.

#### 5.5.2 Hand Analysis Variables

The following variables are available for custom strategy conditions:

```yaml
# Hand composition variables
high_cards: integer        # Count of 10, J, Q, K, A in hand
suited_cards: integer      # Maximum cards of same suit
connected_cards: integer   # Maximum sequential cards
gaps: integer             # Gaps in straight draws
pair_rank: string         # Rank of pair if present (null if none)

# Boolean hand state flags
has_paying_hand: boolean   # True if hand already qualifies for payout
has_pair: boolean         # True if any pair
has_high_pair: boolean    # True if pair of 10s or better
has_trips: boolean        # True if three of a kind

# Draw detection flags
is_flush_draw: boolean    # True if 4 to flush (bet 2) or 3 suited (bet 1)
is_straight_draw: boolean # True if 4 to straight (any type)
is_open_straight_draw: boolean    # True if open-ended straight draw
is_inside_straight_draw: boolean  # True if gutshot straight draw
is_straight_flush_draw: boolean   # True if drawing to straight flush
is_royal_draw: boolean    # True if drawing to royal flush

# Deck composition (multi-deck only)
deck_high_card_ratio: float  # Ratio of high cards remaining
deck_suit_ratio: dict        # Remaining cards by suit
cards_remaining: integer     # Cards left in shoe

# Session context
session_profit: float     # Current session profit/loss
hands_played: integer     # Hands played this session
streak: integer          # Current win/loss streak (positive = wins)
```

### 5.6 Three Card Bonus Strategy Configuration

```yaml
bonus_strategy:
  # Enable/disable bonus betting
  # Type: boolean, Required: yes
  enabled: true
  
  # Paytable selection
  # Type: string, Required: yes
  # Values: "paytable_a", "paytable_b", "paytable_c", "custom"
  # Default: "paytable_b"
  paytable: "paytable_b"
  
  # Bonus bet limits
  limits:
    # Minimum bonus bet
    # Type: float
    min_bet: 1.00
    
    # Maximum bonus bet (table limit)
    # Type: float
    max_bet: 25.00
    
    # Increment for bet sizing
    # Type: float
    increment: 1.00
  
  # Strategy type selection
  # Type: string, Required: yes
  # Values: "never", "always", "static", "bankroll_conditional", 
  #         "streak_based", "session_conditional", "combined", "custom"
  type: "static"
  
  # Configuration for each strategy type:
  
  # --- never ---
  # Never place bonus bet (baseline for comparison)
  # No additional configuration
  
  # --- always ---
  # Always place bonus bet at specified amount
  always:
    # Fixed bet amount
    # Type: float
    amount: 1.00
  
  # --- static ---
  # Constant bonus betting approach
  static:
    # Fixed amount (mutually exclusive with ratio)
    # Type: float or null
    amount: 1.00
    
    # Ratio of base bet (mutually exclusive with amount)
    # Type: float or null
    # Example: 0.2 means bonus = 20% of base bet
    ratio: null
  
  # --- bankroll_conditional ---
  # Adjust bonus betting based on current bankroll state
  bankroll_conditional:
    # Base bonus bet amount when conditions met
    # Type: float
    base_amount: 1.00
    
    # Only bet bonus when session profit exceeds this
    # Type: float or null (null = no restriction)
    min_session_profit: 0.00
    
    # Only bet bonus when bankroll ratio exceeds this
    # Type: float or null
    # Example: 0.8 = only bet when bankroll >= 80% of starting
    min_bankroll_ratio: null
    
    # Bet percentage of profits instead of fixed amount
    # Type: float or null (null = use base_amount)
    # Example: 0.10 = bet 10% of session profits
    profit_percentage: null
    
    # Stop bonus betting after drawdown exceeds this percentage
    # Type: float or null
    max_drawdown: 0.25
    
    # Scale bet with profit level
    scaling:
      # Enable profit-based scaling
      # Type: boolean
      enabled: false
      
      # Profit tiers and corresponding bet amounts
      tiers:
        - min_profit: 0
          max_profit: 50
          bet_amount: 1.00
        - min_profit: 50
          max_profit: 100
          bet_amount: 2.00
        - min_profit: 100
          max_profit: null  # null = no upper limit
          bet_amount: 5.00
  
  # --- streak_based ---
  # Adjust bonus betting based on recent hand outcomes
  streak_based:
    # Base bonus bet amount
    # Type: float
    base_amount: 1.00
    
    # Trigger type for adjustment
    # Type: string
    # Values: "main_loss", "main_win", "bonus_loss", "bonus_win", 
    #         "any_loss", "any_win"
    trigger: "bonus_loss"
    
    # Number of consecutive events to trigger adjustment
    # Type: integer
    streak_length: 5
    
    # Action when streak triggers
    action:
      # Type of adjustment
      # Type: string
      # Values: "increase", "decrease", "stop", "start", "multiply"
      type: "multiply"
      
      # Value for adjustment
      # Type: float
      # For "multiply": multiplier applied to base_amount
      # For "increase"/"decrease": amount added/subtracted
      value: 2.0
    
    # When to reset streak counter
    # Type: string
    # Values: "bonus_win", "bonus_loss", "main_win", "main_loss", 
    #         "any_win", "any_loss", "never"
    reset_on: "bonus_win"
    
    # Cap on streak multiplier
    # Type: float or null
    max_multiplier: 5.0
  
  # --- session_conditional ---
  # Adjust based on session progress and state
  session_conditional:
    # Base bonus bet amount
    # Type: float
    base_amount: 1.00
    
    # Conditions and corresponding bet adjustments
    conditions:
      # Early session (first N hands)
      early_session:
        # Number of hands considered "early"
        hands: 20
        # Bet amount during early session
        amount: 1.00
      
      # Approaching win limit
      near_win_limit:
        # Within this amount of win limit
        threshold: 50.00
        # Bet amount (often increase for "last chance" at big bonus)
        amount: 5.00
      
      # Approaching loss limit
      near_loss_limit:
        # Within this amount of loss limit
        threshold: 50.00
        # Bet amount (often decrease to preserve bankroll)
        amount: 0.00  # 0 = no bonus bet
      
      # Default when no conditions match
      default:
        amount: 1.00
  
  # --- combined ---
  # Coordinate bonus betting with main game decisions
  combined:
    # Base bonus bet amount
    # Type: float
    base_amount: 1.00
    
    # Adjust based on main game ride/pull decisions
    ride_correlation:
      # Enable correlation with ride decisions
      enabled: true
      
      # Bonus multiplier when letting both bets ride
      both_ride_multiplier: 2.0
      
      # Bonus multiplier when letting one bet ride
      one_ride_multiplier: 1.5
      
      # Bonus multiplier when pulling both bets
      both_pull_multiplier: 0.5
    
    # Adjust based on 3-card hand quality
    hand_quality_adjustment:
      enabled: true
      
      # Bonus adjustment when 3-card hand is strong
      # (has high cards or straight/flush potential)
      strong_hand_multiplier: 1.5
      
      # Bonus adjustment when 3-card hand is weak
      weak_hand_multiplier: 0.5
  
  # --- custom ---
  # Fully custom bonus betting logic
  custom:
    # Python expression evaluated to determine bonus bet
    # Must return a float (bet amount) or 0 for no bet
    # Available variables: bankroll, starting_bankroll, session_profit,
    #                      hands_played, main_streak, bonus_streak,
    #                      last_main_result, last_bonus_result,
    #                      three_card_hand, base_bet, min_bet, max_bet
    expression: |
      if session_profit > 100:
          min(5.0, session_profit * 0.05)
      elif session_profit > 0:
          1.0
      else:
          0.0
    
    # Minimum bet floor (expression result clamped to this)
    # Type: float
    min_bet: 0.00
    
    # Maximum bet ceiling (expression result clamped to this)
    # Type: float
    max_bet: 25.00
```

### 5.7 Paytable Configuration

```yaml
paytables:
  # Main game paytable
  main_game:
    # Paytable identifier
    # Type: string
    # Values: "standard", "liberal", "tight", "custom"
    type: "standard"
    
    # Custom paytable definition (if type = "custom")
    custom:
      royal_flush: 1000
      straight_flush: 200
      four_of_a_kind: 50
      full_house: 11
      flush: 8
      straight: 5
      three_of_a_kind: 3
      two_pair: 2
      pair_tens_or_better: 1
      # All other hands pay 0 (loss)
  
  # Three card bonus paytable
  bonus:
    # Paytable identifier
    # Type: string
    # Values: "paytable_a", "paytable_b", "paytable_c", "custom"
    # Default: "paytable_b"
    type: "paytable_b"
    
    # Custom paytable definition (if type = "custom")
    custom:
      mini_royal: 100
      straight_flush: 40
      three_of_a_kind: 30
      straight: 5
      flush: 4
      pair: 1
    
    # Progressive jackpot configuration (if type = "paytable_c")
    progressive:
      # Starting jackpot amount
      starting_jackpot: 10000.00
      
      # Contribution per bonus bet to jackpot
      contribution_rate: 0.15
      
      # Jackpot trigger hand
      trigger: "mini_royal"
      
      # Reset amount after jackpot hit
      reset_amount: 10000.00
```

### 5.8 Output Configuration

```yaml
output:
  # Output directory for results
  # Type: string
  directory: "./results"
  
  # Output filename prefix
  # Type: string
  prefix: "simulation"
  
  # Timestamp format in filename
  # Type: string (Python strftime format)
  timestamp_format: "%Y%m%d_%H%M%S"
  
  # Output formats to generate
  formats:
    # CSV export
    csv:
      enabled: true
      # Include per-hand details (large files)
      include_hands: false
      # Include per-session summaries
      include_sessions: true
      # Include aggregate statistics
      include_aggregate: true
    
    # JSON export
    json:
      enabled: true
      # Pretty print JSON
      pretty: true
      # Include full configuration in output
      include_config: true
    
    # HTML report
    html:
      enabled: false
      # Include visualizations
      include_charts: true
      # Chart library
      chart_library: "plotly"
  
  # Visualization options
  visualizations:
    enabled: true
    
    # Charts to generate
    charts:
      - type: "session_outcomes_histogram"
        title: "Distribution of Session Outcomes"
        
      - type: "bankroll_trajectory"
        title: "Sample Bankroll Trajectories"
        sample_sessions: 100
        
      - type: "hand_frequency"
        title: "Hand Frequency vs. Theoretical"
        
      - type: "strategy_comparison"
        title: "Strategy Performance Comparison"
        
      - type: "bonus_impact"
        title: "Bonus Bet Impact Analysis"
    
    # Chart format
    format: "png"  # png, svg, html
    
    # Chart resolution
    dpi: 150
  
  # Console output options
  console:
    # Show progress bar
    progress_bar: true
    
    # Verbosity level (0-3)
    verbosity: 1
    
    # Summary statistics to display
    show_summary: true
```

### 5.9 Complete Configuration Example

```yaml
# let_it_ride_complete_example.yaml
# Full configuration example with all options

metadata:
  name: "Bankroll Conditional Bonus Study"
  description: "Testing bonus betting only when ahead"
  version: "1.0"
  author: "Strategy Researcher"
  created: "2025-01-15"

simulation:
  num_sessions: 100000
  hands_per_session: 200
  random_seed: 42
  workers: "auto"
  progress_interval: 10000
  detailed_logging: false

deck:
  num_decks: 6
  penetration: 0.75
  shuffle_algorithm: "fisher_yates"
  track_composition: true

bankroll:
  starting_amount: 500.00
  base_bet: 5.00
  stop_conditions:
    win_limit: 250.00
    loss_limit: 200.00
    max_hands: 200
    max_duration_minutes: null
    stop_on_insufficient_funds: true
  betting_system:
    type: "flat"

strategy:
  type: "basic"

bonus_strategy:
  enabled: true
  paytable: "paytable_b"
  limits:
    min_bet: 1.00
    max_bet: 25.00
    increment: 1.00
  type: "bankroll_conditional"
  bankroll_conditional:
    base_amount: 1.00
    min_session_profit: 25.00
    min_bankroll_ratio: null
    profit_percentage: null
    max_drawdown: 0.25
    scaling:
      enabled: true
      tiers:
        - min_profit: 25
          max_profit: 75
          bet_amount: 1.00
        - min_profit: 75
          max_profit: 150
          bet_amount: 2.00
        - min_profit: 150
          max_profit: null
          bet_amount: 5.00

paytables:
  main_game:
    type: "standard"
  bonus:
    type: "paytable_b"

output:
  directory: "./results/bonus_study"
  prefix: "bankroll_conditional"
  timestamp_format: "%Y%m%d_%H%M%S"
  formats:
    csv:
      enabled: true
      include_hands: false
      include_sessions: true
      include_aggregate: true
    json:
      enabled: true
      pretty: true
      include_config: true
    html:
      enabled: false
  visualizations:
    enabled: true
    charts:
      - type: "session_outcomes_histogram"
        title: "Session Outcomes with Conditional Bonus"
      - type: "bonus_impact"
        title: "Bonus Contribution Analysis"
    format: "png"
    dpi: 150
  console:
    progress_bar: true
    verbosity: 1
    show_summary: true
```

---

## 6. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    CLI / Config Loader                   │
│              (YAML parsing, validation)                  │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                  Simulation Controller                   │
│         (orchestrates sessions, parallelization)         │
└───────┬─────────────────┬─────────────────┬─────────────┘
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│  Game Engine  │ │Strategy Engine│ │Bankroll Manager│
│  - Deck/Shoe  │ │ - Basic       │ │ - Tracking     │
│  - Dealing    │ │ - Custom      │ │ - Limits       │
│  - Evaluation │ │ - Comp-Dep    │ │ - Progression  │
└───────┬───────┘ └───────┬───────┘ └───────┬────────┘
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼────────┐
│  Hand Eval    │ │ Bonus Strategy│ │ Betting System │
│  - 5-card     │ │ - Static      │ │ - Flat         │
│  - 3-card     │ │ - Conditional │ │ - Progressive  │
└───────────────┘ │ - Streak      │ │ - Custom       │
                  │ - Custom      │ └────────────────┘
                  └───────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                  Analytics & Reporting                   │
│     - Statistics calculation                             │
│     - Strategy comparison                                │
│     - Visualization                                      │
│     - Export (CSV, JSON, HTML)                           │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Key Metrics to Analyze

### 7.1 Primary Research Questions

1. **Session Win Rate**: What combination of strategy and session parameters maximizes the percentage of winning sessions?

2. **Optimal Session Length**: Is there a "sweet spot" for session duration that improves win rate?

3. **Bankroll Sizing**: What starting bankroll (in base bet units) provides the best balance of session win rate vs. capital at risk?

4. **Stop Conditions**: How do win/loss limits affect session outcomes?

5. **Variance Reduction**: Can betting adjustments reduce variance without significantly impacting expected value?

6. **Multi-Deck Effects**: Does shoe penetration create exploitable situations?

### 7.2 Bonus Betting Research Questions

1. **Standalone Viability**: What is the true cost per hand of bonus betting under each paytable?

2. **Session Win Rate Impact**: Can strategic bonus betting improve session win rates despite negative EV?

3. **Optimal Bet Sizing**: If betting bonus, what sizing relative to base bet optimizes session outcomes?

4. **Conditional Value**: Under what bankroll/session conditions does bonus betting become more/less costly?

5. **Variance Manipulation**: Can bonus betting be used to deliberately increase variance when seeking to reach a win target?

### 7.3 Strategy Comparisons

| Strategy | Description | Hypothesis |
|----------|-------------|------------|
| Basic Strategy | Mathematically optimal decisions | Baseline (lowest house edge) |
| Conservative | Pull except with made hands | Lower variance, lower EV |
| Aggressive | Let it ride more often | Higher variance |
| Composition-Dependent | Adjust for multi-deck shoe state | May find small edges |

---

## 8. Data Requirements

### 8.1 Per-Hand Record

| Field | Type | Description |
|-------|------|-------------|
| hand_id | integer | Unique hand identifier |
| session_id | integer | Parent session identifier |
| shoe_id | integer | Shoe identifier (multi-deck) |
| cards_player | string | Player's 3 cards |
| cards_community | string | 2 community cards |
| decision_bet1 | string | "ride" or "pull" |
| decision_bet2 | string | "ride" or "pull" |
| final_hand_rank | string | Evaluated hand (e.g., "flush") |
| base_bet | float | Bet amount per circle |
| bets_at_risk | float | Total wagered after decisions |
| main_payout | float | Main game payout |
| bonus_bet | float | Bonus bet amount (0 if none) |
| bonus_hand_rank | string | 3-card hand rank |
| bonus_payout | float | Bonus payout |
| bankroll_after | float | Bankroll after hand |

### 8.2 Per-Session Summary

| Field | Type | Description |
|-------|------|-------------|
| session_id | integer | Unique session identifier |
| starting_bankroll | float | Initial bankroll |
| ending_bankroll | float | Final bankroll |
| net_result | float | Profit/loss |
| hands_played | integer | Total hands |
| stop_reason | string | Why session ended |
| peak_bankroll | float | Highest bankroll reached |
| max_drawdown | float | Largest decline from peak |
| main_game_wagered | float | Total main bets |
| main_game_won | float | Total main payouts |
| bonus_wagered | float | Total bonus bets |
| bonus_won | float | Total bonus payouts |
| hand_distribution | object | Count by hand type |
| outcome | string | "win", "loss", "push" |

### 8.3 Aggregate Statistics

| Metric | Description |
|--------|-------------|
| session_win_rate | Percentage of profitable sessions |
| expected_value_per_hand | Average profit/loss per hand |
| variance | Variance of session outcomes |
| standard_deviation | Std dev of session outcomes |
| skewness | Distribution asymmetry |
| confidence_intervals | 95% CI for key metrics |
| hand_frequencies | Actual vs. theoretical by hand |
| risk_of_ruin | Probability of losing X% of bankroll |

---

## 9. Testing Requirements

### 9.1 Unit Tests

- Deck shuffling produces uniform distribution
- All 2,598,960 possible 5-card hands evaluate correctly
- All 22,100 possible 3-card hands evaluate correctly
- Payout calculations match paytables
- Basic strategy decisions match published charts
- Multi-deck shoe deals correct number of cards before reshuffle
- All betting progression systems calculate correctly

### 9.2 Integration Tests

- Full session simulation with known seed produces reproducible results
- Bankroll tracking remains accurate over long sessions
- Configuration loading handles all documented options
- Strategy conditions evaluate correctly

### 9.3 Statistical Validation

- Simulated hand frequencies match theoretical probabilities (chi-square test)
- Expected value converges to theoretical house edge over large samples
- Multi-deck composition tracking is accurate

---

## 10. Deliverables

1. **Python Package**: Installable, documented simulator
2. **CLI Tool**: Run simulations from command line with config files
3. **Sample Configurations**: Pre-built strategy and session configurations
4. **Analysis Report**: Findings from baseline simulations
5. **Visualization Dashboard**: Interactive results explorer

---

## 11. Assumptions & Constraints

### 11.1 Assumptions

- Standard casino rules apply
- No additional side bets beyond three card bonus
- Players cannot see other hands (single player simulation)

### 11.2 Constraints

- Python 3.10+ required
- Initial release targets CLI usage
- No real-money integration

---

## 12. Future Considerations

- Additional side bet analysis (other bonus bets)
- Card counting viability analysis for multi-deck
- Web-based interface for interactive exploration
- Machine learning strategy optimization
- Multi-player table simulation

---

## Approval

| Role | Name | Date |
|------|------|------|
| Business Analyst | | |
| Technical Lead | | |
| Stakeholder | | |
