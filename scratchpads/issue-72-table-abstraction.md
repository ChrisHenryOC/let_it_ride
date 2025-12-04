# LIR-42: Table Abstraction - Implementation Plan

**GitHub Issue:** #72
**Date:** 2025-12-04

## Summary

Implement the `Table` class that orchestrates multiple player positions at a single table, dealing from a shared deck with shared community cards.

## Dependencies

- LIR-13 (Game Engine Orchestration) - Complete
- LIR-41 (Dealer Discard Mechanics) - Complete

## Implementation Plan

### 1. Add TableConfig to config/models.py

```python
class TableConfig(BaseModel):
    """Configuration for table settings."""
    num_seats: Annotated[int, Field(ge=1, le=6)] = 1
    track_seat_positions: bool = True
```

### 2. Create core/table.py with:

**PlayerSeat dataclass:**
- seat_number: int (1-6)
- player_cards: tuple[Card, Card, Card]
- decision_bet1: Decision
- decision_bet2: Decision
- final_hand_rank: FiveCardHandRank
- base_bet: float
- bets_at_risk: float
- main_payout: float
- bonus_bet: float
- bonus_hand_rank: ThreeCardHandRank | None
- bonus_payout: float
- net_result: float

**TableRoundResult dataclass:**
- round_id: int
- community_cards: tuple[Card, Card]
- dealer_discards: tuple[Card, ...] | None
- seat_results: list[PlayerSeat]

**Table class:**
- Constructor accepts: TableConfig, Deck, Strategy, MainGamePaytable, BonusPaytable|None, DealerConfig, rng
- play_round(round_id, base_bet, bonus_bet, context) -> TableRoundResult
- Internal logic:
  1. Reset and shuffle deck
  2. Dealer discard (if enabled)
  3. Deal 3 cards to each seat
  4. Deal 2 community cards
  5. For each seat: analyze, make decisions, evaluate, calculate payouts
  6. Return TableRoundResult

### 3. Key Design Decisions

1. **Shared resources per round:**
   - Same deck shuffle for all seats
   - Same community cards for all seats
   - Same strategy instance for all seats

2. **Per-seat isolation:**
   - Each seat gets its own 3 cards
   - Decisions are made per seat (same strategy, but based on different cards)
   - Each seat tracks its own results

3. **Backwards compatibility:**
   - Single seat (num_seats=1) should produce equivalent results to GameEngine
   - All fields in PlayerSeat align with GameHandResult

### 4. Files to Create/Modify

**Create:**
- `src/let_it_ride/core/table.py`
- `tests/unit/core/test_table.py`

**Modify:**
- `src/let_it_ride/config/models.py` - Add TableConfig
- `src/let_it_ride/core/__init__.py` - Export new types (if safe from circular imports)

## Test Plan

1. TableConfig validation tests
2. Single-seat behavior matches GameEngine
3. Multi-seat dealing uses shared community cards
4. Multi-seat dealing uses unique player cards per seat
5. All cards in a round are unique
6. Dealer discard integration
7. Reproducibility with same RNG seed
8. Boundary tests (1 seat, 6 seats)
