# Performance Review: PR #159 -- LIR-63 Progressive Bet Strategies

## Summary

This PR adds progressive jackpot betting strategies (never, always, jackpot_threshold, bankroll_conditional) with a `ProgressiveContext` frozen dataclass passed into the strategy on every hand. The strategy implementations themselves are lightweight (simple comparisons, no allocations). The primary performance concern is the per-hand `ProgressiveContext` dataclass allocation on the hot path, which mirrors the existing `BonusContext` pattern and adds incremental overhead to `play_hand()`.

## Findings

### Medium Severity

**M1: Per-hand ProgressiveContext allocation on the hot path**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py` lines 535-545
- The `ProgressiveContext` frozen dataclass is instantiated on every single hand when a progressive strategy is active. At 100,000+ hands/second, this creates significant GC pressure. The existing code already does this for `BonusContext` (line 498) and `StrategyContext` (line 514), so this PR adds a third per-hand dataclass allocation to the hot path.
- Each `ProgressiveContext` has 9 float/int fields with `__slots__`, so the per-object cost is relatively small (~120 bytes), but at scale (10M hands) this is ~1.2GB of short-lived allocations that the GC must reclaim.
- A mutable context object reused across hands (with field updates rather than fresh construction) would eliminate this allocation entirely. Alternatively, passing raw arguments to `get_progressive_bet()` would avoid the object overhead.
- In PR Scope: Yes
- Actionable: Yes -- but note this follows the established `BonusContext` pattern. Fixing this in isolation would create inconsistency. Consider a follow-up to refactor all three context types together.

**M2: Redundant condition checks on every hand when progressive is disabled**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py` lines 531-534
- When `_progressive_strategy` is `None` (the common case -- progressive is disabled by default), the code still evaluates two `is not None` checks per hand. This is trivial cost individually, but on the hot path at 100k+ hands/sec it adds up.
- The controller already knows at session creation time whether progressive is enabled. A cleaner design would use a strategy pattern where `NeverProgressiveStrategy` is the default (eliminating the None check), or split `play_hand` into specialized variants.
- In PR Scope: Yes
- Actionable: Yes, but low priority given the branch prediction will handle this well after warmup.

### Low Severity

**L1: progressive_strategy_factory creates new strategy instance per session unnecessarily**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py` lines 409-412
- The factory calls `create_progressive_strategy()` for each session, but all four strategy implementations are stateless (they hold only immutable configuration). A single instance could be shared across all sessions, similar to how `strategy` (the main play strategy) is created once and reused.
- For 1000 sessions this creates 1000 identical strategy objects. The cost is negligible in absolute terms but represents unnecessary work.
- In PR Scope: Yes
- Actionable: Yes -- create the progressive strategy once outside the loop (like `strategy = create_strategy(...)` on line 399) and pass it directly rather than via a factory.

**L2: Division in BankrollConditionalProgressiveStrategy on every hand**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py` line 171
- `context.bankroll / context.starting_bankroll` performs a float division on every hand. This is a micro-optimization concern -- the division is cheap, but the ratio could be pre-computed and stored in the context if `starting_bankroll` is constant (which it is).
- In PR Scope: Yes
- Actionable: No -- too micro to justify added complexity.

**L3: Two property accesses on ProgressiveJackpot per hand**
- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py` lines 542-543
- `self._progressive_jackpot.current_pool` and `self._progressive_jackpot.seed_amount` are Python property calls (method dispatch overhead) used to populate the context. These are simple attribute returns so the cost is small, but in CPython each property access involves descriptor protocol overhead.
- In PR Scope: Yes
- Actionable: No -- the overhead is negligible and properties are idiomatic Python.

## Performance Impact Assessment

**Throughput impact**: Minimal. The strategy logic itself is O(1) per hand -- just simple float comparisons. The main overhead is the `ProgressiveContext` dataclass allocation, which adds roughly 5-10% to the existing per-hand allocation budget (alongside `BonusContext` and `StrategyContext`). This should not threaten the 100,000 hands/second target on its own.

**Memory impact**: Negligible for steady-state. `ProgressiveContext` is short-lived (created and discarded within `play_hand()`), so peak memory remains bounded. The frozen dataclass with `__slots__` is the correct choice for this pattern.

**Verdict**: This PR is unlikely to cause the simulator to miss its performance targets. The patterns used are consistent with the existing codebase. The per-hand allocation concern (M1) is real but systemic -- it should be addressed holistically across all context types rather than just for progressive strategies.
