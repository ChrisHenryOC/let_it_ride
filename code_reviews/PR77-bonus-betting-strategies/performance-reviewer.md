# Performance Review: PR #77 - Bonus Betting Strategies

## Summary

The bonus betting strategies implementation demonstrates solid performance-conscious design with appropriate use of `__slots__`, frozen dataclasses with `slots=True`, and minimal object allocation in hot paths. The code is well-suited for the target throughput of 100,000+ hands/second. One minor optimization opportunity exists in the `BankrollConditionalBonusStrategy` scaling tier iteration, but it does not represent a critical performance concern.

## Findings by Severity

### Critical Issues

**None identified.**

The implementation follows Python performance best practices appropriately.

---

### High Severity Issues

**None identified.**

---

### Medium Severity Issues

#### M1: Linear Tier Search in `BankrollConditionalBonusStrategy.get_bonus_bet()`

**Location:** `src/let_it_ride/strategy/bonus.py:406-413` (diff lines 278-285)

**Issue:** The scaling tier lookup iterates through all tiers linearly until a match is found:

```python
if self._scaling_tiers:
    for min_profit, max_profit, tier_amount in self._scaling_tiers:
        in_range = context.session_profit >= min_profit and (
            max_profit is None or context.session_profit < max_profit
        )
        if in_range:
            bet = tier_amount
            break
```

**Impact:** O(n) complexity per call where n = number of tiers. Given the expected small number of tiers (typically 3-5), this is acceptable for the target throughput. However, if configurations with many tiers are used, this could become a bottleneck.

**Recommendation:** For typical use (3-5 tiers), the current implementation is acceptable. If large tier configurations are expected, consider:
1. Storing tiers in sorted order and using binary search (`bisect`), or
2. Pre-computing a lookup table at initialization for common profit ranges

**Verdict:** Low impact for current use case - no immediate action required.

---

### Low Severity Issues

#### L1: Missing `__slots__` on Baseline Strategy Classes (Pre-existing Code)

**Location:** `src/let_it_ride/strategy/baseline.py` (not in this PR)

**Note:** The existing `AlwaysRideStrategy` and `AlwaysPullStrategy` classes lack `__slots__`, while this PR correctly adds `__slots__` to all new strategy classes. This is a pre-existing inconsistency, not a regression introduced by this PR.

---

#### L2: `StrategyContext` Dataclass Missing `slots=True` (Pre-existing Code)

**Location:** `src/let_it_ride/strategy/base.py:26-48` (not in this PR)

**Note:** The `StrategyContext` dataclass does not use `slots=True`, while the new `BonusContext` correctly does. This is a pre-existing issue that could be addressed in a separate PR for consistency.

---

## Positive Performance Observations

### P1: Excellent Use of `__slots__` on Strategy Classes

All new strategy classes properly declare `__slots__`:

```python
class NeverBonusStrategy:
    __slots__ = ()

class AlwaysBonusStrategy:
    __slots__ = ("_amount",)

class StaticBonusStrategy:
    __slots__ = ("_amount", "_ratio")

class BankrollConditionalBonusStrategy:
    __slots__ = (
        "_base_amount",
        "_min_session_profit",
        "_min_bankroll_ratio",
        "_profit_percentage",
        "_max_drawdown",
        "_scaling_tiers",
    )
```

**Benefit:** Reduced memory footprint per instance and faster attribute access. Since strategies are instantiated once per session and reused for all hands, this prevents per-instance dict overhead.

---

### P2: Frozen Dataclass with `slots=True` for `BonusContext`

**Location:** `src/let_it_ride/strategy/bonus.py:146-175` (diff lines 18-47)

```python
@dataclass(frozen=True, slots=True)
class BonusContext:
    ...
```

**Benefit:**
- `slots=True` reduces memory overhead per context instance
- `frozen=True` enables potential hash caching and immutability guarantees
- Context objects are created once per hand - memory efficiency is important at 100k+ hands/second

---

### P3: No Object Allocation in Hot Paths

The `get_bonus_bet()` methods in all strategies perform only:
- Simple arithmetic operations
- Attribute lookups
- Primitive comparisons

No new objects (lists, dicts, strings) are created during bet calculation, which is critical for the per-hand hot path.

---

### P4: Early Return Pattern for Condition Checks

**Location:** `src/let_it_ride/strategy/bonus.py:381-400`

The `BankrollConditionalBonusStrategy.get_bonus_bet()` uses early returns for failed conditions:

```python
if self._min_session_profit is not None and context.session_profit < self._min_session_profit:
    return 0.0

if self._min_bankroll_ratio is not None and context.starting_bankroll > 0:
    ...
```

**Benefit:** Avoids unnecessary computation when conditions fail early. This is optimal for the common case where many hands will not meet bonus betting thresholds.

---

### P5: Inline `_clamp_bonus_bet` Helper

**Location:** `src/let_it_ride/strategy/bonus.py:198-212` (diff lines 70-84)

The `_clamp_bonus_bet` function is a simple, short function that should be easily inlined by Python's interpreter for frequently called code paths. The function performs minimal work:

```python
def _clamp_bonus_bet(bet: float, context: BonusContext) -> float:
    if bet <= 0:
        return 0.0
    if bet < context.min_bonus_bet:
        return 0.0
    return min(bet, context.max_bonus_bet)
```

---

## Performance Impact Assessment

### Memory Usage

| Component | Memory Impact |
|-----------|---------------|
| `BonusContext` per hand | ~120 bytes (9 fields with slots) |
| Strategy instance | 48-128 bytes (depends on strategy type) |
| 10M hands (contexts only) | ~1.2 GB |

**Verdict:** Well within the 4GB budget, assuming contexts are not all held simultaneously (which they should not be - one context per hand in sequence).

### Throughput Impact

| Operation | Complexity | Hot Path? |
|-----------|------------|-----------|
| `NeverBonusStrategy.get_bonus_bet()` | O(1) | Yes |
| `AlwaysBonusStrategy.get_bonus_bet()` | O(1) | Yes |
| `StaticBonusStrategy.get_bonus_bet()` | O(1) | Yes |
| `BankrollConditionalBonusStrategy.get_bonus_bet()` | O(t) where t = tiers | Yes |

**Verdict:** All operations are O(1) or O(t) with small constant t. This implementation should not be a bottleneck for achieving 100k+ hands/second.

---

## Recommendations Summary

| Priority | Issue | Action |
|----------|-------|--------|
| None | M1: Linear tier search | Monitor if many tiers are used; optimize only if needed |
| N/A | L1/L2: Pre-existing slots issues | Consider addressing in separate cleanup PR |

---

## Conclusion

**This PR meets the performance requirements for the Let It Ride simulator.** The implementation demonstrates performance-conscious design with proper use of `__slots__`, frozen slotted dataclasses, early returns, and minimal object allocation. No changes are required before merging from a performance perspective.
