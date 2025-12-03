# LIR-19: Session Result Data Structures

**GitHub Issue**: #22
**Branch**: `feature/lir-19-session-result-data-structures`

## Summary

Implement comprehensive data structures for session results and hand records with serialization support.

## Key Decisions

1. **HandRecord vs GameHandResult**: `GameHandResult` is for in-memory game engine results with Card objects. `HandRecord` is for serialization/storage with string representations.

2. **String representations**: Cards stored as space-separated strings (e.g., "Ah Kd Qs") using Card.__str__() method.

3. **SessionResult enhancement**: The existing `SessionResult` in session.py is used internally. We add serialization methods directly to it via mixin or separate functions.

4. **Dataclass pattern**: Use `@dataclass(frozen=True, slots=True)` for immutable value objects.

## Tasks

1. [x] Review existing SessionResult and GameHandResult
2. [ ] Implement HandRecord dataclass with all per-hand fields
3. [ ] Add to_dict() and from_dict() methods to HandRecord
4. [ ] Implement count_hand_distribution helper
5. [ ] Add serialization functions for SessionResult
6. [ ] Update simulation __init__.py exports
7. [ ] Write comprehensive tests

## Implementation Plan

### HandRecord Fields (from requirements spec)
- hand_id: int
- session_id: int
- shoe_id: int | None
- cards_player: str (e.g., "Ah Kd Qs")
- cards_community: str
- decision_bet1: str ("ride" or "pull")
- decision_bet2: str
- final_hand_rank: str
- base_bet: float
- bets_at_risk: float
- main_payout: float
- bonus_bet: float
- bonus_hand_rank: str | None
- bonus_payout: float
- bankroll_after: float

### Conversion functions
- `hand_record_from_game_result()`: Convert GameHandResult to HandRecord
- `count_hand_distribution()`: Count hand types from list of HandRecords or GameHandResults

### Files to Create/Modify
- `src/let_it_ride/simulation/results.py` (NEW)
- `tests/unit/simulation/test_results.py` (NEW)
- `src/let_it_ride/simulation/__init__.py` (UPDATE)
