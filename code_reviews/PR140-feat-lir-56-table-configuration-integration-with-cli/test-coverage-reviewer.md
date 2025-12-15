# Test Coverage Review: PR #140 - LIR-56 Table Configuration Integration with CLI

## Summary

This PR adds multi-seat table configuration to `FullConfig` and integrates `TableSession` with the CLI and simulation controller. The test coverage is good for the core functionality, with integration tests covering multi-seat simulations and unit tests for the new config model fields. However, there are gaps in testing for the new `create_table_session_config()` utility function, parallel execution with multi-seat tables, and formatter display of table settings.

## Findings

### High Severity

#### H1: No Unit Tests for `create_table_session_config()` Function
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/utils.py:123-147`

The new `create_table_session_config()` function lacks dedicated unit tests. While it is exercised indirectly through integration tests, the function has specific logic for mapping `FullConfig` fields to `TableSessionConfig` that should be tested in isolation:

```python
def create_table_session_config(
    config: FullConfig, bonus_bet: float
) -> TableSessionConfig:
    """Create a TableSessionConfig from FullConfig."""
    bankroll_config = config.bankroll
    stop_conditions = bankroll_config.stop_conditions

    return TableSessionConfig(
        table_config=config.table,
        starting_bankroll=bankroll_config.starting_amount,
        base_bet=bankroll_config.base_bet,
        win_limit=stop_conditions.win_limit,
        loss_limit=stop_conditions.loss_limit,
        max_hands=config.simulation.hands_per_session,
        stop_on_insufficient_funds=stop_conditions.stop_on_insufficient_funds,
        bonus_bet=bonus_bet,
    )
```

Missing test scenarios:
- Verify all fields are correctly mapped from `FullConfig` to `TableSessionConfig`
- Test with various `bonus_bet` values (0.0, positive values)
- Test with different `num_seats` values in `table_config`
- Test with `None` values for `win_limit`/`loss_limit`

---

#### H2: No Tests for Parallel Multi-Seat Execution Path
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:134-178`

The `_run_single_table_session()` function and the parallel multi-seat branch in `run_worker_sessions()` are not covered by tests. The existing `test_parallel.py` tests do not include multi-seat configurations:

```python
def _run_single_table_session(
    seed: int,
    config: FullConfig,
    strategy: Strategy,
    main_paytable: MainGamePaytable,
    bonus_paytable: BonusPaytable | None,
    betting_system_factory: Callable[[], BettingSystem],
) -> list[SessionResult]:
```

Missing test scenarios:
- Parallel execution with `num_seats > 1`
- Verify parallel multi-seat results match sequential multi-seat results (reproducibility)
- Test composite ID calculation: `session_id * num_seats + seat_idx`
- Test `_merge_results()` with `num_seats > 1` parameter

---

### Medium Severity

#### M1: No Tests for Formatter Multi-Seat Display Logic
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/cli/formatters.py:162-166`

The conditional display of table seats in `print_config_summary()` is not tested. The existing formatter tests set `num_seats=1` but do not verify the multi-seat display branch:

```python
# Table settings (only show if multi-seat)
if config.table.num_seats > 1:
    table.add_row("", "")  # Separator
    table.add_row("Table Seats", str(config.table.num_seats))
```

Missing test scenarios:
- Verify "Table Seats" row appears when `num_seats > 1`
- Verify "Table Seats" row is absent when `num_seats == 1`
- Test display formatting with various seat counts (2, 6)

---

#### M2: Missing Edge Case Tests for Multi-Seat Integration
**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_multi_seat.py:1-171`

The integration tests cover the happy path but miss several edge cases:

Missing test scenarios:
- Multi-seat with stop conditions (win/loss limits) - existing tests use `None` for both
- Multi-seat with `workers > 1` (parallel mode) - all tests use `workers=1`
- Multi-seat with dealer discard configuration enabled
- Multi-seat with bonus betting enabled
- Test behavior when one seat busts early while others continue (stop condition interactions)

---

#### M3: No Tests for `_create_table_session()` Method in Controller
**File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:527-570`

The `_create_table_session()` method in `SimulationController` lacks unit test coverage. While integration tests exercise this path, there are no isolated unit tests to verify:

```python
def _create_table_session(
    self,
    rng: random.Random,
    strategy: Strategy,
    main_paytable: MainGamePaytable,
    bonus_paytable: BonusPaytable | None,
    betting_system_factory: Callable[[], BettingSystem],
) -> TableSession:
```

Missing test scenarios:
- Verify `Deck` is created fresh per call
- Verify `Table` is created with correct config parameters
- Verify `TableSessionConfig` is created with correct bonus_bet
- Verify `betting_system_factory()` is called (not reused)

---

### Low Severity

#### L1: Integration Test Does Not Verify Result Structure for Multi-Seat
**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_multi_seat.py:52-80`

The `test_multi_seat_simulation_produces_per_seat_results()` test only checks the count of results but not their structure or ordering:

```python
def test_multi_seat_simulation_produces_per_seat_results(self) -> None:
    # ...
    # Multi-seat: num_results == num_sessions * num_seats
    assert len(results.session_results) == num_sessions * num_seats
```

Consider adding assertions for:
- Results are properly ordered by table, then by seat
- Each result has expected attributes populated
- Consistency of results within a table (all played same number of hands as verified in `test_multi_seat_seats_share_community_cards`)

---

#### L2: Missing Deterministic Seed Test for Parallel Multi-Seat
**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_multi_seat.py:114-149`

The `test_multi_seat_reproducible_with_seed()` test only uses `workers=1` (sequential). There should be a corresponding test for parallel execution reproducibility with multi-seat tables.

---

### Info

#### I1: Test Config Helper Functions Could Be Refactored to Support Multi-Seat
**File:** `/Users/chrishenry/source/let_it_ride/tests/integration/test_controller.py:56-98`

The `create_test_config()` helper in `test_controller.py` does not accept a `num_seats` parameter, requiring each multi-seat test to manually construct `FullConfig`. Consider extending this helper or creating a shared test utility.

---

#### I2: Sample Config File Added But Not Exercised by Tests
**File:** `/Users/chrishenry/source/let_it_ride/configs/multi_seat_example.yaml`

A new example configuration file was added but there is no test verifying it can be loaded and validated. Consider adding it to `test_sample_configs.py` to ensure the example stays valid.

---

## Test Quality Assessment

### Positive Aspects
1. **Good use of parametrized tests**: `test_all_seat_counts()` tests all valid seat counts (2-6)
2. **Reproducibility testing**: Tests verify deterministic behavior with fixed seeds
3. **Clear test organization**: Tests are grouped into logical classes
4. **Good coverage of TableConfig validation**: Unit tests cover valid/invalid seat counts

### Areas for Improvement
1. **Parallel execution path**: No tests for multi-seat with `workers > 1`
2. **Utility function coverage**: `create_table_session_config()` needs dedicated unit tests
3. **Formatter display logic**: Multi-seat display branch untested
4. **Edge case coverage**: Stop conditions with multi-seat not tested

---

## Recommendations

1. **Add unit tests for `create_table_session_config()`** in a new test file or `test_factories.py`
2. **Add parallel multi-seat tests** to `test_parallel.py` mirroring the sequential tests in `test_multi_seat.py`
3. **Extend formatter tests** to verify multi-seat display behavior
4. **Add `multi_seat_example.yaml`** to the sample config validation tests
5. **Consider property-based testing** using Hypothesis for verifying result count formula: `num_sessions * num_seats`
