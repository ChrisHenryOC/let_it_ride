# Code Quality Review for PR #140

## Summary

This PR integrates the `TableConfig` into `FullConfig` and updates the `SimulationController` and `ParallelExecutor` to support multi-seat table simulations via CLI configuration. The implementation follows existing patterns well with good separation of concerns, but introduces some code duplication between sequential and parallel execution paths, and lacks bonus strategy support in multi-seat mode which could lead to unexpected behavior.

## Findings

### Critical

None identified.

### High

**Missing bonus strategy in multi-seat table sessions** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:527-570` and `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:134-178`

The `_create_table_session` method and `_run_single_table_session` function do not accept or use a `bonus_strategy_factory`. While the `bonus_bet` amount is passed to the `TableSessionConfig`, the `BonusStrategy` protocol determines whether to place bonus bets dynamically based on context. Single-seat sessions properly use `bonus_strategy_factory()` to create fresh strategies per session, but multi-seat sessions ignore this entirely. This could lead to incorrect bonus bet behavior when users configure `bankroll_conditional` or other dynamic bonus strategies.

Recommendation: Add `bonus_strategy_factory` parameter to `_create_table_session` and `_run_single_table_session`, or document this as a known limitation and add validation that rejects incompatible bonus strategy configurations when `num_seats > 1`.

### Medium

**Code duplication between sequential and parallel multi-seat handling** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:416-441` and `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:216-243`

The logic for deciding between `TableSession` and `Session`, running them, and extracting results is nearly identical in both `_run_sequential` and `run_worker_sessions`. This duplicates the branching logic and result extraction pattern:

```python
if use_table_session:
    # Multi-seat: use TableSession
    table_session = self._create_table_session(...)
    table_result = table_session.run_to_completion()
    for seat_result in table_result.seat_results:
        session_results.append(seat_result.session_result)
else:
    # Single-seat: use Session for efficiency
    session = self._create_session(...)
    result = self._run_session(session)
    session_results.append(result)
```

Recommendation: Consider extracting a shared factory function or helper that encapsulates the session-type decision and result extraction, reducing the risk of the two paths diverging in future changes.

---

**Composite ID calculation lacks documentation** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/parallel.py:228-229`

The composite ID formula `session_id * num_seats + seat_idx` is used to flatten multi-seat results into a single ordered list. While mathematically correct, this encoding scheme is not documented and could be confusing for maintainers. The same formula must be used consistently in `_merge_results` for ordering.

```python
# Use composite ID: session_id * num_seats + seat_idx
composite_id = session_id * num_seats + seat_idx
```

Recommendation: Add a module-level docstring or constant explaining the composite ID scheme, or extract it into a small helper function like `calculate_result_id(session_id, seat_idx, num_seats)` that documents its purpose.

---

**Inconsistent use of assertion vs exception for invariants** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:391`, `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py:415`

The existing `table_session.py` uses `assert` statements to verify that `stop_reason` is set before building results:

```python
# Seat stop reason is guaranteed to be set
assert seat_state.stop_reason is not None
```

While this is in existing code (not new to this PR), the new integration relies on these assertions. Assertions can be stripped in optimized Python runs (`-O` flag), which could lead to confusing `None` values in production. This is noted as a pre-existing pattern that the PR inherits.

Recommendation: For future consideration, replace assertions with explicit `RuntimeError` raises for invariant violations that should never occur.

---

**Magic number for seat validation range** - `/Users/chrishenry/source/let_it_ride/tests/unit/config/test_models.py:885-886`

The test validates seats `1-6` but uses magic numbers in assertions:

```python
def test_num_seats_below_min(self) -> None:
    with pytest.raises(ValidationError) as exc_info:
        TableConfig(num_seats=0)
    assert "greater than or equal to 1" in str(exc_info.value)

def test_num_seats_above_max(self) -> None:
    with pytest.raises(ValidationError) as exc_info:
        TableConfig(num_seats=7)
    assert "less than or equal to 6" in str(exc_info.value)
```

Recommendation: Consider defining constants `MIN_SEATS = 1` and `MAX_SEATS = 6` in the config models module and referencing them in tests for better maintainability.

### Low

**Inconsistent parameter ordering** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py:527-535`

The `_create_table_session` method signature differs from `_create_session` in parameter ordering. `_create_session` takes `session_id` as the first parameter while `_create_table_session` does not take a session ID at all (which is reasonable since TableSession manages multiple results). However, the remaining parameters are in a different order.

`_create_session`:
```python
def _create_session(self, session_id, rng, strategy, main_paytable, bonus_paytable, betting_system_factory, bonus_strategy_factory)
```

`_create_table_session`:
```python
def _create_table_session(self, rng, strategy, main_paytable, bonus_paytable, betting_system_factory)
```

This is minor but could cause confusion. No action required but noted for awareness.

---

**Test file location** - `/Users/chrishenry/source/let_it_ride/tests/integration/test_multi_seat.py`

The new integration tests are appropriately placed in `tests/integration/` which is correct for end-to-end simulation tests. Good practice.

### Info

**Well-structured configuration example** - `/Users/chrishenry/source/let_it_ride/configs/multi_seat_example.yaml`

The new configuration example is well-documented with clear section comments explaining the purpose of multi-seat simulation and its use cases. This serves as good documentation for users.

**Backwards compatibility maintained** - `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py:1228`

The `table` field defaults to `TableConfig()` which has `num_seats=1`, preserving backwards compatibility with existing configurations that do not specify a table section.

**Good use of existing patterns** - The implementation correctly follows the established pattern of using factory functions for stateful components (`betting_system_factory`) and reusing immutable components (`strategy`, `paytables`) across sessions.
