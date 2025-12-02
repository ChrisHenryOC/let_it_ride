# Scratchpad: Issue #16 - Game Engine Orchestration

**GitHub Issue:** [#16](https://github.com/ChrisHenryOC/let_it_ride/issues/16)
**Implementation Plan Issue:** LIR-13
**Created:** 2025-12-02

## Problem Statement

Implement the main game engine that orchestrates dealing, decisions, and payout calculation for a single hand.

## Dependencies (All Complete)

- `core/deck.py` - Card dealing and shuffling
- `strategy/base.py` - Strategy protocol and Decision enum
- `config/paytables.py` - Payout calculations
- `core/hand_evaluator.py` - Five-card hand ranking
- `core/three_card_evaluator.py` - Three-card bonus ranking
- `core/hand_analysis.py` - Strategy input

## Key Types

### GameHandResult

Named `GameHandResult` to avoid collision with existing `HandResult` in `hand_evaluator.py`.

```python
@dataclass(frozen=True)
class GameHandResult:
    hand_id: int
    player_cards: tuple[Card, Card, Card]
    community_cards: tuple[Card, Card]
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
```

## Payout Logic

- `calculate_payout()` returns pure profit (bet * ratio)
- Winning hand: net = payout (profit)
- Losing hand (ratio 0): net = -stake

```python
main_net = main_payout if main_payout > 0 else -bets_at_risk
bonus_net = bonus_payout if bonus_payout > 0 else -bonus_bet
net_result = main_net + bonus_net
```

## Hand Flow

1. Reset and shuffle deck
2. Deal 3 player cards + 2 community cards
3. Analyze 3-card hand, invoke strategy for bet 1
4. Reveal first community card
5. Analyze 4-card hand, invoke strategy for bet 2
6. Reveal second community card
7. Evaluate final 5-card hand
8. Calculate main payout based on active bets
9. If bonus bet > 0, evaluate 3-card hand and calculate bonus payout
10. Return GameHandResult

## Files to Create

- `src/let_it_ride/core/game_engine.py`
- `tests/integration/test_game_engine.py`

## Test Cases

- Complete hand with paying hand
- Complete hand with losing hand
- PULL on bet 1, bet 2, or both
- Bonus bet winning/losing
- No bonus bet
- Verify deck reset each hand
- Verify correct payout calculations
