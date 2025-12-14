# Issue #89: LIR-47 Session API Consistency and DRY Refactoring

GitHub Issue: https://github.com/chrishenry/let_it_ride/issues/89

## Tasks

1. **API Consistency**: Make `stop_reason` a property (consistent with `is_complete`)
   - Files: `session.py`, `table_session.py`
   - Both currently have `stop_reason()` as method but `is_complete` as property

2. **DRY Validation**: Extract shared validation to helper function
   - `SessionConfig.__post_init__` and `TableSessionConfig.__post_init__` are nearly identical
   - Create shared `validate_session_config()` function

3. **Test Setup Helper**: Create factory function for integration tests
   - `tests/integration/test_table.py` has ~20+ repeated setup patterns
   - Create `create_table_session()` helper with sensible defaults

## Implementation Notes

### Task 1: stop_reason Property
- Change `def stop_reason(self) -> StopReason | None:` to `@property`
- Update any callers from `session.stop_reason()` to `session.stop_reason`

### Task 2: Shared Validation
Both configs validate:
- starting_bankroll > 0
- base_bet > 0
- win_limit > 0 if set
- loss_limit > 0 if set
- max_hands > 0 if set
- bonus_bet >= 0
- at least one stop condition
- starting_bankroll >= min_bet_required

### Task 3: Test Helper
Helper should accept:
- main_paytable (required)
- rng (required)
- num_seats, starting_bankroll, base_bet (with defaults)
- Optional: max_hands, win_limit, loss_limit, strategy, bonus_paytable, bonus_bet, dealer_config
