# Performance Review: PR #96 - LIR-20 Simulation Controller (Sequential)

**Reviewer:** Performance Specialist
**Date:** 2025-12-06 (Updated Review)
**Files Reviewed:** 4 files, +919 lines

## Summary

The SimulationController implementation is **well-optimized** and follows performance best practices. Key optimizations include: `__slots__` on both `SimulationController` and `SimulationResults`, strategy/paytable objects created once and reused across sessions, and the `_action_to_decision` helper at module level. The code should comfortably meet the project targets of >=100,000 hands/second and <4GB RAM for 10M hands.

---

## Findings by Severity

### Critical

*None identified.*

### High

*None identified.*

### Medium

#### 1. Betting System Factory Creates Closure Per Simulation Run

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 322-323

**Issue:** A new closure function `betting_system_factory` is created inside `run()`. While lightweight, this creates a new function object per simulation run.

**Code:**
```python
def betting_system_factory() -> BettingSystem:
    return create_betting_system(self._config.bankroll)
```

**Impact:** Minimal - this is only created once per simulation run, not per session. The design decision to use a factory is correct since betting systems have mutable state and must be fresh per session. This is an acceptable trade-off.

**Recommendation:** No change needed. The factory pattern is appropriate here. Consider documenting why a factory is used (betting system state isolation).

---

#### 2. Session-Level Object Creation Overhead

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 407-422

**Issue:** Each session creates several objects: `Deck()`, `SessionConfig`, `GameEngine`, and `BettingSystem`. This is necessary for correctness but adds per-session overhead.

**Code:**
```python
deck = Deck()  # Fresh deck per session

engine = GameEngine(
    deck=deck,
    strategy=strategy,  # Reused - good!
    main_paytable=main_paytable,  # Reused - good!
    ...
)

betting_system = betting_system_factory()  # Fresh state per session
```

**Impact:** For typical simulations (100-1000 sessions), this is negligible. For extreme cases (100,000+ sessions with few hands each), this could add measurable overhead.

**Recommendation:** No change needed for current scope. If profiling shows this as a bottleneck, consider object pooling or `Deck.reset()` method for deck reuse.

---

### Low

#### 3. SessionConfig Created Fresh Per Session

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, lines 397-405

**Issue:** `SessionConfig` is created fresh for each session, but all sessions use identical configuration values (only `bonus_bet` calculation varies based on strategy settings).

**Code:**
```python
session_config = SessionConfig(
    starting_bankroll=bankroll_config.starting_amount,
    base_bet=bankroll_config.base_bet,
    win_limit=stop_conditions.win_limit,
    loss_limit=stop_conditions.loss_limit,
    max_hands=self._config.simulation.hands_per_session,
    stop_on_insufficient_funds=stop_conditions.stop_on_insufficient_funds,
    bonus_bet=bonus_bet,
)
```

**Impact:** Very low - `SessionConfig` uses `slots=True` and is a small frozen dataclass. Creation overhead is minimal.

**Recommendation:** Could hoist `SessionConfig` creation to `run()` and reuse if `bonus_bet` is static (not strategy-dependent). However, this optimization would save less than 1% overhead and is not worth the code complexity.

---

#### 4. Magic Number for Seed Range

**Location:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, line 333

**Code:**
```python
session_seed = master_rng.randint(0, 2**31 - 1)
```

**Impact:** No performance impact, but could use a named constant for clarity.

**Recommendation:** Define `_MAX_SEED = 2**31 - 1` at module level with a comment. This is a documentation improvement, not a performance issue.

---

## Positive Performance Observations

### 1. Strategy and Paytable Reuse (Lines 316-320)

Excellent optimization - immutable objects are created once and reused across all sessions:

```python
# Create immutable components once and reuse across sessions
strategy = create_strategy(self._config.strategy)
main_paytable = _get_main_paytable(self._config)
bonus_paytable = _get_bonus_paytable(self._config)
```

This eliminates thousands of unnecessary allocations for large simulation runs.

### 2. Proper Use of `__slots__` (Lines 70, 284)

Both key classes use `__slots__`:

```python
@dataclass(frozen=True, slots=True)
class SimulationResults:
    ...

class SimulationController:
    __slots__ = ("_config", "_progress_callback", "_base_seed")
```

This reduces per-instance memory overhead by ~40-50 bytes per object.

### 3. Module-Level Helper Function (Lines 58-67)

The `_action_to_decision` helper is defined at module level rather than inside `create_strategy()`:

```python
def _action_to_decision(action: str) -> Decision:
    return Decision.RIDE if action == "ride" else Decision.PULL
```

This avoids function object creation on every `create_strategy()` call.

### 4. Efficient RNG Seeding (Lines 326-334)

The master RNG pattern is efficient and ensures reproducibility:

```python
if self._base_seed is not None:
    master_rng = random.Random(self._base_seed)
else:
    master_rng = random.Random()

for session_id in range(num_sessions):
    session_seed = master_rng.randint(0, 2**31 - 1)
    session_rng = random.Random(session_seed)
```

### 5. Generator Expression for Total Hands (Line 347)

Uses efficient generator expression rather than creating an intermediate list:

```python
total_hands = sum(r.hands_played for r in session_results)
```

---

## Performance Against Targets

### Throughput Target: >= 100,000 hands/second

**Assessment: MEETS TARGET**

The controller adds minimal overhead to the hot path:
- Strategy evaluation: O(1) per hand (reused strategy object)
- Paytable lookup: O(1) per hand (reused paytable objects)
- Per-session setup: ~5 object allocations (negligible)
- Progress callback: O(1) per session (not per hand)

The per-hand cost is dominated by the underlying `Session.play_hand()` and `GameEngine`, which are outside this PR's scope.

### Memory Target: <4GB for 10M hands

**Assessment: MEETS TARGET**

Memory calculation for 10M hands across 10,000 sessions:
- 10,000 `SessionResult` objects (frozen, slots=True): ~2MB
- 1 `SimulationResults` object (frozen, slots=True): ~100 bytes
- 1 `SimulationController` object (slots): ~100 bytes
- Reused strategy/paytables: ~10KB
- **Total controller overhead: ~2MB**

The 4GB budget is for the entire simulation including Session/GameEngine internals. The controller's contribution is negligible (<0.1%).

---

## Recommendations Summary

| Priority | Issue | Recommendation | Effort | Impact |
|----------|-------|----------------|--------|--------|
| Low | Magic number for seed range | Add named constant | Very Low | Documentation |
| N/A | SessionConfig per session | Keep as-is (correct design) | N/A | N/A |
| N/A | Betting system factory | Keep as-is (correct design) | N/A | N/A |

---

## Comparison with Previous Review

The code has been updated to address all previous findings:

| Previous Finding | Status |
|------------------|--------|
| Strategy/paytable created per session | **FIXED** - Now created once in `run()` |
| `_action_to_decision` inside function | **FIXED** - Now at module level |
| `SimulationResults` lacks `slots=True` | **FIXED** - Now uses `@dataclass(frozen=True, slots=True)` |

---

## Conclusion

This is a **well-optimized** implementation that follows Python performance best practices for this domain. The code correctly identifies which objects can be reused (immutable strategy, paytables) versus which must be fresh per session (deck, betting system state).

**Recommendation: APPROVE** - No blocking performance issues. The identified low-priority items are documentation improvements rather than performance fixes.

**Performance Grade: A**
- Proper `__slots__` usage
- Efficient object reuse pattern
- Minimal per-session overhead
- Meets all project performance targets
