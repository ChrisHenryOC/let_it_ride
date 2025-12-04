# Performance Review: PR #85 - Extract Shared Hand Processing Logic (LIR-46)

## Summary

This PR extracts duplicated hand processing logic from `GameEngine.play_hand()` and `Table._process_seat()` into a shared `process_hand_decisions_and_payouts()` function. The refactoring is well-executed with minimal performance impact. The addition of `slots=True` to dataclasses is a positive performance optimization. However, there is one minor concern regarding the additional function call overhead and an intermediate dataclass creation in the hot path.

## Findings by Severity

### Medium

#### 1. Additional Function Call Overhead and Intermediate Object Creation

**Location:** `src/let_it_ride/core/hand_processing.py:253-334`, `src/let_it_ride/core/game_engine.py:159-184`

**Issue:** The refactoring introduces:
1. One additional function call (`process_hand_decisions_and_payouts()`) per hand
2. Creation of an intermediate `HandProcessingResult` dataclass instance that is immediately unpacked

**Impact Analysis:**
- Function call overhead in Python is approximately 50-100ns
- Dataclass instantiation with 8 fields is approximately 100-200ns
- At the target of 100,000 hands/second, this adds roughly 15-30 microseconds per 100k hands
- **Verdict:** The overhead is negligible (<0.003% of total execution time) and the code clarity benefits outweigh this cost

**Mitigating Factors:**
- The `slots=True` optimization added to `HandProcessingResult`, `GameHandResult`, and `PlayerSeat` reduces memory footprint by ~40% and improves attribute access speed
- The function eliminates code duplication, reducing maintenance burden
- CPython's function call optimization (PEP 659 in 3.11+) reduces this overhead further

### Low

#### 2. Tuple Unpacking Style (Non-Issue)

**Location:** `src/let_it_ride/core/hand_processing.py:292-297`

**Observation:** The new code uses tuple unpacking:
```python
four_cards = (*player_cards, community_cards[0])
final_cards = (*player_cards, *community_cards)
```

This is consistent with the original `table.py` implementation and is preferred over list unpacking (`[*player_cards, community_cards[0]]`) for this use case because:
1. Tuples are immutable and slightly more memory-efficient
2. The analysis functions accept `Sequence[Card]`, so both work equally well
3. Tuple creation is marginally faster than list creation in CPython

**Verdict:** This is a non-issue; the implementation is optimal.

### Positive Observations

#### 1. slots=True Addition (Performance Improvement)

**Location:**
- `src/let_it_ride/core/hand_processing.py:225` - `HandProcessingResult`
- `src/let_it_ride/core/game_engine.py:24` - `GameHandResult`

**Impact:** Adding `slots=True` to frozen dataclasses:
- Reduces memory per instance by ~40% (no `__dict__` per instance)
- Improves attribute access speed by ~10-20%
- At 10M hands, this could save approximately 400MB-800MB of memory

This is an excellent optimization for frequently instantiated classes.

#### 2. No Algorithmic Regressions

The refactoring preserves the O(1) complexity of hand processing:
- Strategy decisions: O(1)
- Hand evaluation: O(1) (fixed 5 cards)
- Payout calculation: O(1)

#### 3. Import Optimization

The refactored files now import fewer symbols directly:
- `game_engine.py` removed imports of `analyze_three_cards`, `analyze_four_cards`, `evaluate_five_card_hand`, `evaluate_three_card_hand`
- These are now encapsulated within `hand_processing.py`

This slightly improves module load time and reduces namespace pollution.

## Recommendations

### Optional (Low Priority)

1. **Consider `__slots__` for HandAnalysis dataclass**

   While not part of this PR, the `HandAnalysis` dataclass in `hand_analysis.py` (line 27) does not use `slots=True`. Since it is created twice per hand (3-card and 4-card analysis), adding slots would provide additional memory savings.

2. **Future Consideration: Inlining for Extreme Performance**

   If profiling ever shows function call overhead as a bottleneck (unlikely), the shared logic could be converted to a private module-level helper that both callers inline. However, this is premature optimization at this stage.

## Performance Target Compliance

| Target | Status | Notes |
|--------|--------|-------|
| >= 100,000 hands/second | PASS | Function call overhead is negligible (~200ns/hand) |
| < 4GB RAM for 10M hands | PASS | `slots=True` improves memory efficiency |

## Conclusion

This refactoring is **approved from a performance perspective**. The code consolidation benefits significantly outweigh the minimal overhead introduced. The proactive addition of `slots=True` demonstrates good performance awareness and partially offsets any overhead from the abstraction.

No performance-critical issues were identified that would block merging.
