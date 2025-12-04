# Test Coverage Review: PR #80 - LIR-42 Add Table Abstraction for Multi-Player Support

## Summary

The PR introduces a well-tested `Table` class for multi-player Let It Ride with comprehensive unit tests covering most scenarios. However, there are notable gaps in integration testing, edge case coverage for multi-deck scenarios, and missing tests for the `track_seat_positions` config flag which is defined but never used. The dealing sequence change in `GameEngine` (player cards now dealt before dealer discard) lacks explicit verification tests.

---

## Findings by Severity

### High Severity

#### H1: Missing Tests for `track_seat_positions` Config Flag
**Location:** `src/let_it_ride/config/models.py:216`, `tests/unit/core/test_table.py`

The `TableConfig.track_seat_positions` attribute is defined with a default value of `True`, but:
1. No test verifies what behavior changes when `track_seat_positions=False`
2. The `Table` class does not appear to use this flag at all in the implementation
3. This is either dead code or missing functionality

**Impact:** Configuration option has no effect; potential future bug if flag is expected to work.

**Recommendation:** Either remove the unused `track_seat_positions` field or implement and test the intended behavior (e.g., aggregating seat results vs. tracking individually).

---

#### H2: No Integration Tests for Table Class
**Location:** `tests/integration/` (missing)

The `Table` class has extensive unit tests but lacks integration tests verifying:
1. Table integration with Session management
2. Multi-round table gameplay with bankroll tracking
3. Table with different strategy types (BasicStrategy, CustomStrategy, etc.)

**Impact:** Integration issues between Table and other system components may go undetected.

**Recommendation:** Add integration tests in `tests/integration/test_table.py` that verify Table works correctly with Session, bankroll tracking, and various strategies.

---

#### H3: GameEngine Dealing Sequence Change Not Explicitly Tested
**Location:** `src/let_it_ride/core/game_engine.py:136-156`

The PR changes the dealing order from "discard then deal" to "deal player cards, then discard, then community cards". While existing tests pass, there is no explicit test verifying this new sequence order.

**Impact:** Future refactoring could accidentally revert this change without detection.

**Recommendation:** Add a test that explicitly verifies the dealing sequence:
```python
def test_dealing_sequence_player_before_discard():
    """Verify player cards are dealt before dealer discard."""
    # Use a mock or tracking mechanism to verify deal order
```

---

### Medium Severity

#### M1: No Tests for Multi-Deck Scenarios with Table
**Location:** `tests/unit/core/test_table.py`

All Table tests use a single-deck configuration. No tests verify:
1. Table works correctly with 2, 4, 6, or 8 deck shoes
2. Deck penetration settings with multi-player tables
3. Card uniqueness across multiple rounds without reshuffle

**Impact:** Multi-deck configurations may have subtle bugs that go undetected.

**Recommendation:** Add parameterized tests for multi-deck scenarios:
```python
@pytest.mark.parametrize("num_decks", [2, 4, 6, 8])
def test_table_multi_deck_scenarios(num_decks):
    deck = Deck(num_decks=num_decks)
    # Verify correct behavior
```

---

#### M2: Missing Edge Case: Maximum Discard with Maximum Seats
**Location:** `tests/unit/core/test_table.py`

No test verifies behavior when `discard_cards=10` (maximum) combined with `num_seats=6` (maximum). This uses 18 + 10 + 2 = 30 cards, leaving only 22 cards in a single deck.

**Impact:** Edge case may fail or produce unexpected behavior.

**Recommendation:** Add explicit boundary test:
```python
def test_max_discard_with_max_seats():
    """Verify table handles max discard (10) with max seats (6)."""
    table_config = TableConfig(num_seats=6)
    dealer_config = DealerConfig(discard_enabled=True, discard_cards=10)
    # 18 player + 10 discard + 2 community = 30 cards
    # Should work with single deck (52 cards)
```

---

#### M3: No Tests for Different Strategy Types with Table
**Location:** `tests/unit/core/test_table.py`

All Table tests use `BasicStrategy`. Missing tests for:
1. `AlwaysRideStrategy` / `AlwaysPullStrategy` behavior consistency across seats
2. `CustomStrategy` with seat-specific conditions
3. Strategies that depend heavily on StrategyContext

**Impact:** Strategy interaction edge cases may go undetected.

**Recommendation:** Add tests with various strategy implementations to verify consistent behavior.

---

#### M4: Missing Test for Bonus Bet with Multi-Seat Table
**Location:** `tests/unit/core/test_table.py`

While `test_single_seat_matches_game_engine_with_bonus` exists, there is no test verifying:
1. Bonus bets work correctly across all 6 seats
2. Each seat receives correct bonus evaluation based on its own 3 cards
3. Total bonus payouts are calculated correctly

**Impact:** Bonus bet handling in multi-seat scenarios may have bugs.

**Recommendation:** Add:
```python
def test_multi_seat_bonus_bet():
    """Verify bonus bets are evaluated independently per seat."""
    table_config = TableConfig(num_seats=6)
    # Play round with bonus_bet=1.0
    # Verify each seat has independent bonus_hand_rank
```

---

### Low Severity

#### L1: No Negative Round ID Test
**Location:** `tests/unit/core/test_table.py`

No test verifies behavior with negative or zero `round_id` values. While likely acceptable (just an identifier), consistency should be verified.

---

#### L2: TestTableConfigModel Uses ValidationError But May Not Be Specific
**Location:** `tests/unit/core/test_table.py:55-63`

Tests check for `ValueError` but Pydantic raises `ValidationError`. The tests work because pytest catches the ValidationError subclass, but assertions could be more specific.

---

#### L3: No Floating-Point Edge Case Tests
**Location:** `tests/unit/core/test_table.py`

No tests verify behavior with very small (`0.01`) or very large (`1000000.0`) bet amounts, or floating-point precision edge cases.

---

## Specific Recommendations

### File: `tests/unit/core/test_table.py`

| Line | Recommendation |
|------|----------------|
| After line 541 | Add `TestTableWithMultiDeck` class for multi-deck scenarios |
| After line 541 | Add `TestTableBonusMultiSeat` class for multi-seat bonus betting |
| After line 541 | Add `TestTableEdgeCases` class for boundary conditions |

### File: `tests/integration/test_table.py` (new file)

Create integration tests covering:
1. Table + Session integration
2. Table with various strategy implementations
3. Multi-round gameplay with consistent state

### File: `src/let_it_ride/core/table.py`

| Line | Recommendation |
|------|----------------|
| 78-82 | Either use `track_seat_positions` or remove from config |

---

## Test Coverage Metrics (Estimated)

| Component | Unit Test Coverage | Integration Coverage | Notes |
|-----------|-------------------|---------------------|-------|
| TableConfig | 95% | 0% | Missing track_seat_positions usage test |
| PlayerSeat | 80% | 0% | Immutability tested, fields verified indirectly |
| TableRoundResult | 80% | 0% | Immutability tested |
| Table.play_round | 90% | 0% | Good coverage, missing multi-deck |
| Table._process_seat | 85% | 0% | Covered via play_round tests |
| Table.last_discarded_cards | 95% | 0% | Well tested |
| GameEngine dealing sequence | 70% | 90% | Sequence change not explicitly tested |

---

## Summary of Required Actions

1. **Critical:** Determine if `track_seat_positions` should be implemented or removed
2. **High:** Add integration tests for Table class
3. **High:** Add explicit test for new dealing sequence (player before discard)
4. **Medium:** Add multi-deck scenario tests
5. **Medium:** Add max discard + max seats boundary test
6. **Medium:** Add multi-seat bonus betting tests
