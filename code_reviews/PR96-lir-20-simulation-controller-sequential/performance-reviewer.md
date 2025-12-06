# Performance Review: PR #96 - LIR-20 Simulation Controller (Sequential)

**Reviewer:** Performance Specialist
**Date:** 2025-12-06
**Files Reviewed:** 4 files, +919 lines

## Summary

The SimulationController implementation is well-structured with good use of `__slots__` for memory efficiency. The code follows project conventions and should meet the 100,000 hands/second throughput target for sequential execution. However, there are opportunities to reduce per-session object creation overhead and improve memory efficiency for large simulations. No critical performance issues were identified.

---

## Findings by Severity

### Medium Priority

#### 1. Repeated Strategy/Paytable Creation Per Session

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 369-382 (`_create_session` method)

**Issue:** The controller creates new `Strategy`, `MainGamePaytable`, and `BonusPaytable` instances for each session, even though these are immutable and identical across all sessions in a simulation run.

**Code:**
```python
def _create_session(self, _session_id: int, rng: random.Random) -> Session:
    # ...
    # These are created fresh for EACH session:
    deck = Deck()
    strategy = create_strategy(self._config.strategy)  # New strategy each time
    main_paytable = _get_main_paytable(self._config)   # New paytable each time
    bonus_paytable = _get_bonus_paytable(self._config) # New paytable each time
```

**Impact:** For 10,000 sessions, this creates 10,000 unnecessary strategy objects. While Python's GC handles cleanup, this adds allocation overhead in the hot path.

**Recommendation:** Move strategy and paytable creation to the controller's `__init__` or `run()` method and reuse across sessions:

```python
def run(self) -> SimulationResults:
    # Create once at start of simulation
    strategy = create_strategy(self._config.strategy)
    main_paytable = _get_main_paytable(self._config)
    bonus_paytable = _get_bonus_paytable(self._config)

    for session_id in range(num_sessions):
        session = self._create_session(
            session_id, session_rng, strategy, main_paytable, bonus_paytable
        )
        # ...
```

**Effort:** Low
**Impact:** Medium (reduces GC pressure for large simulation runs)

---

#### 2. List Comprehension for Custom Strategy Rules

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 116-128

**Issue:** When creating a custom strategy, the code iterates through rules twice (once for bet1, once for bet2) and creates new `StrategyRule` objects. This happens per-session due to Issue #1.

**Code:**
```python
bet1_rules = [
    StrategyRule(
        condition=rule.condition, action=_action_to_decision(rule.action)
    )
    for rule in config.custom.bet1_rules
]
bet2_rules = [
    StrategyRule(
        condition=rule.condition, action=_action_to_decision(rule.action)
    )
    for rule in config.custom.bet2_rules
]
```

**Impact:** Custom strategies with many rules will see more allocation overhead. Combined with Issue #1, this compounds for large simulations.

**Recommendation:** This is addressed by fixing Issue #1 (strategy created once and reused).

**Effort:** N/A (addressed by Issue #1)

---

### Low Priority

#### 3. Inner Function Definition in Hot Path

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 113-115

**Issue:** The helper function `_action_to_decision` is defined inside `create_strategy()`, meaning it's recreated on every call.

**Code:**
```python
def _action_to_decision(action: str) -> Decision:
    return Decision.RIDE if action == "ride" else Decision.PULL
```

**Impact:** Minimal, as function creation is lightweight, but it's a micro-optimization opportunity.

**Recommendation:** Move to module level or use a dict lookup:

```python
_ACTION_TO_DECISION = {"ride": Decision.RIDE, "pull": Decision.PULL}
# Then use: _ACTION_TO_DECISION[rule.action]
```

**Effort:** Very Low
**Impact:** Very Low

---

#### 4. Datetime Creation Per Simulation

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 293, 315

**Issue:** `datetime.now()` is called twice per simulation run. This is fine but worth noting that for very high-frequency simulation runs, this could be optimized.

**Code:**
```python
start_time = datetime.now()
# ... simulation ...
end_time = datetime.now()
```

**Impact:** Negligible for typical usage.

**Recommendation:** No change needed. This is the correct approach for timing simulations.

---

### Best Practices (Positive Observations)

#### 1. Proper Use of `__slots__`

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, line 265

The `SimulationController` correctly uses `__slots__` to reduce memory overhead:

```python
__slots__ = ("_config", "_progress_callback", "_base_seed")
```

This follows the project convention and is appropriate for a class that may be instantiated frequently.

---

#### 2. Efficient RNG Seeding Strategy

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 297-306

The approach of deriving session seeds from a master RNG is efficient and ensures reproducibility:

```python
if self._base_seed is not None:
    master_rng = random.Random(self._base_seed)
else:
    master_rng = random.Random()

for session_id in range(num_sessions):
    session_seed = master_rng.randint(0, 2**31 - 1)
    session_rng = random.Random(session_seed)
```

This is correct and efficient for reproducible simulations.

---

#### 3. SessionConfig Uses `frozen=True, slots=True`

The existing `SessionConfig` dataclass (not in this PR but used) correctly uses both `frozen=True` and `slots=True` for optimal memory usage:

```python
@dataclass(frozen=True, slots=True)
class SessionConfig:
```

---

#### 4. SimulationResults Uses `frozen=True`

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 57-74

```python
@dataclass(frozen=True)
class SimulationResults:
```

**Observation:** Consider adding `slots=True` for memory efficiency, especially since `session_results` can be a very large list for big simulations. However, the frozen dataclass prevents mutation which is correct.

**Minor Recommendation:** Add `slots=True`:
```python
@dataclass(frozen=True, slots=True)
class SimulationResults:
```

---

## Performance Against Targets

### Throughput (Target: >= 100,000 hands/second)

**Assessment:** The sequential controller should meet this target. The main work happens in `Session.run_to_completion()` which calls `Session.play_hand()` in a tight loop. The controller adds minimal overhead:

- One-time setup per session (creates Session, Engine, etc.)
- Progress callback per session (optional, O(1))
- Result aggregation: O(n) for n sessions

The per-hand cost is dominated by card dealing, strategy evaluation, and payout calculation - all of which exist in the underlying Session/GameEngine code.

**Concern:** The object creation per session (Issue #1) may become noticeable with thousands of short sessions (e.g., 10,000 sessions of 100 hands each). For typical use cases (100 sessions of 1,000+ hands), this is negligible.

### Memory (Target: <4GB for 10M hands)

**Assessment:** The implementation should meet this target:

1. `SimulationResults` stores a list of `SessionResult` objects
2. `SessionResult` uses `slots=True` and contains only primitive types (no hand records stored)
3. No hand-by-hand storage in the controller layer

**Calculation for 10M hands across 1,000 sessions:**
- 1,000 `SessionResult` objects (each ~200 bytes with slots) = ~200KB
- `SimulationResults` wrapper = negligible
- Total controller overhead: <1MB

The memory budget allows plenty of room for the underlying Session/GameEngine operations.

---

## Recommendations Summary

| Priority | Issue | Recommendation | Effort |
|----------|-------|----------------|--------|
| Medium | Strategy/paytable created per session | Hoist to `run()` and reuse | Low |
| Low | Inner function in hot path | Move to module level | Very Low |
| Low | SimulationResults lacks slots | Add `slots=True` | Very Low |

---

## Test Coverage Notes

The integration tests are comprehensive and cover:
- Single/multiple sessions
- Session isolation
- Reproducibility with seeds
- Progress callbacks
- Stop conditions (win/loss limits, max hands)
- All strategy types

No performance benchmarks are included, which is appropriate for this PR (LIR-20 scope). Performance benchmarking should be added in a separate PR.

---

## Conclusion

This is a well-implemented sequential simulation controller that should meet performance targets. The code follows project conventions with `__slots__` usage and clean separation of concerns. The main optimization opportunity is to cache strategy and paytable objects across sessions rather than recreating them. This is a **low-effort, medium-impact** improvement that would reduce GC pressure for large simulation runs.

**Recommendation:** Approve with minor suggestions. The identified issues are optimizations, not blockers.
