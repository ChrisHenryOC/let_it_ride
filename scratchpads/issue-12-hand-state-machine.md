# Scratchpad: Issue #12 - Let It Ride Hand State Machine

**GitHub Issue:** [#12](https://github.com/ChrisHenryOC/let_it_ride/issues/12)
**Implementation Plan Issue:** LIR-9
**Created:** 2025-12-01

## Problem Statement

Implement the core hand state machine that tracks a single hand through all decision points in Let It Ride. This is a critical component that enforces the proper game flow and tracks bet/card state.

## Dependencies

- **Card** from `core/card.py` (GitHub #5) - DONE
- **Deck** from `core/deck.py` (GitHub #5) - DONE
- **evaluate_five_card_hand** from `core/hand_evaluator.py` (GitHub #7) - DONE

## Game Flow Reference

1. Player places 3 equal bets, receives 3 cards → DEAL phase
2. Player decides on Bet 1 (pull/ride) → BET1_DECISION phase
3. First community card revealed → FIRST_REVEAL phase
4. Player decides on Bet 2 (pull/ride) → BET2_DECISION phase
5. Second community card revealed → SECOND_REVEAL phase
6. Hand is resolved (evaluated and paid) → RESOLVED phase

## Key Requirements

### 1. HandPhase Enum
```python
class HandPhase(Enum):
    DEAL = "deal"
    BET1_DECISION = "bet1_decision"
    FIRST_REVEAL = "first_reveal"
    BET2_DECISION = "bet2_decision"
    SECOND_REVEAL = "second_reveal"
    RESOLVED = "resolved"
```

### 2. Decision Enum
```python
class Decision(Enum):
    RIDE = "ride"
    PULL = "pull"
```

### 3. HandState Class
Key fields:
- `phase`: Current HandPhase
- `player_cards`: tuple of 3 Cards
- `community_cards`: list of 0, 1, or 2 Cards
- `base_bet`: float (bet amount per circle)
- `bet1_decision`: Decision or None
- `bet2_decision`: Decision or None
- `bet1_active`: bool (still in play?)
- `bet2_active`: bool (still in play?)
- `bet3_active`: bool (always True)

Key methods:
- `apply_bet1_decision(decision: Decision) -> None`
- `reveal_first_community(card: Card) -> None`
- `apply_bet2_decision(decision: Decision) -> None`
- `reveal_second_community(card: Card) -> None`
- `get_visible_cards() -> list[Card]`
- `get_final_hand() -> tuple[Card, ...]`
- `bets_at_risk() -> float`

### 4. State Transition Rules

Valid transitions:
- DEAL → BET1_DECISION (via apply_bet1_decision)
- BET1_DECISION → FIRST_REVEAL (via reveal_first_community)
- FIRST_REVEAL → BET2_DECISION (via apply_bet2_decision)
- BET2_DECISION → SECOND_REVEAL (via reveal_second_community)
- SECOND_REVEAL → RESOLVED (via resolve)

Invalid transitions should raise InvalidPhaseError.

## Implementation Approach

### Files to Create
- `src/let_it_ride/core/hand_state.py` - Main implementation
- `tests/unit/core/test_hand_state.py` - Unit tests

### Design Decisions

1. **Mutable state**: Unlike Card (frozen), HandState must be mutable since we track phase transitions
2. **Explicit phase checks**: Each method validates the current phase before executing
3. **Bet tracking**: bet1_active/bet2_active are updated when decisions are made (PULL = False)
4. **Player cards as tuple**: Immutable after creation
5. **Community cards as list**: Grows from 0 to 2 during play

### Error Handling

Create a custom exception:
```python
class InvalidPhaseError(Exception):
    """Raised when an operation is attempted in an invalid phase."""
    pass
```

## Test Cases

### Valid Transitions
1. Create hand, apply bet1 decision → phase becomes BET1_DECISION
2. After bet1, reveal first community → phase becomes FIRST_REVEAL
3. After first reveal, apply bet2 decision → phase becomes BET2_DECISION
4. After bet2, reveal second community → phase becomes SECOND_REVEAL
5. After second reveal, resolve → phase becomes RESOLVED

### Invalid Transitions (should raise)
1. Apply bet1 when not in DEAL phase
2. Reveal first community when not in BET1_DECISION phase
3. Apply bet2 when not in FIRST_REVEAL phase
4. Reveal second community when not in BET2_DECISION phase
5. Resolve when not in SECOND_REVEAL phase
6. Any operation after RESOLVED phase

### Bet Tracking Tests
1. PULL decision sets bet_active to False
2. RIDE decision keeps bet_active as True
3. bet3_active is always True
4. bets_at_risk() returns correct amount

### Utility Method Tests
1. get_visible_cards() returns correct cards at each phase
2. get_final_hand() only works in SECOND_REVEAL or RESOLVED phase
3. get_final_hand() returns all 5 cards

## Estimated Scope
~250 lines implementation + ~300 lines tests
