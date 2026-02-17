# Documentation Accuracy Review -- PR #160

## Summary

This PR adds progressive jackpot EV/breakeven analysis with generally well-documented new code. The new `progressive_analysis.py` module has thorough docstrings on all public types and functions. However, there are several documentation inaccuracies: a stale docstring claiming `total_wagered` is "main game only" when it now includes progressive amounts, a missing attribute in `SessionResult`'s docstring, an unused parameter that is misleadingly documented, and the new module is not exported from the analytics package `__init__.py`.

## Findings

### High Severity

**1. `AggregateStatistics.total_wagered` docstring says "main game only" but now includes bonus and progressive**

The docstring on line 46 of `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/aggregation.py` states:

```python
total_wagered: Total amount wagered (main game only).
```

However, the code on line 159 computes it as:

```python
total_wagered = main_wagered + bonus_wagered + progressive_wagered
```

This is actively misleading -- anyone reading the docstring would expect `total_wagered` to exclude bonus and progressive amounts. This predates this PR (bonus was already included before), but the PR makes it worse by adding progressive.

**Recommendation:** Update the docstring to: `total_wagered: Total amount wagered across all bet types (main + bonus + progressive).`

---

**2. `SessionResult` docstring missing `total_progressive_won` attribute**

In `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/session.py`, lines 192-213, the `SessionResult` class docstring lists `total_progressive_wagered` but does not list the newly added `total_progressive_won` field (line 227):

```python
@dataclass(frozen=True, slots=True)
class SessionResult:
    """Complete results of a finished session.

    Attributes:
        ...
        total_progressive_wagered: Sum of all progressive bets placed.
        ...
    """
    ...
    total_progressive_wagered: float = 0.0
    total_progressive_won: float = 0.0  # <-- not in docstring
```

**Recommendation:** Add `total_progressive_won: Sum of all progressive payouts received.` to the Attributes section of the `SessionResult` docstring, after the `total_progressive_wagered` entry.

### Medium Severity

**3. `contribution_rate` parameter accepted but unused in calculations**

In `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, both `calculate_breakeven_jackpot()` (line 133) and `calculate_house_edge()` (line 184) accept a `contribution_rate` parameter documented as "Fraction of bet added to jackpot pool" but never use it in any calculation -- it is only stored in the result object. This is misleading because:

- A reader would expect the contribution rate to factor into the EV or breakeven calculation.
- The breakeven formula `J = (bet - E_fixed) / E_pct_coeff` does not account for the fact that only `contribution_rate * bet` actually goes into the pool.

The docstring does not clarify that this parameter is informational only and not used in the computation.

**Recommendation:** Add a note in the docstring clarifying that `contribution_rate` is stored for reference only and does not affect the calculation. Alternatively, consider whether the breakeven formula should incorporate the contribution rate (since the actual jackpot grows by `contribution_rate * bet` per hand, not `bet` per hand).

---

**4. `HouseEdgeResult.house_edge` docstring range is inaccurate**

In `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, line 57:

```python
house_edge: House edge as a fraction (0-1). Negative means player advantage.
```

The parenthetical "(0-1)" contradicts "Negative means player advantage." If the value can be negative, the range is not 0-1.

**Recommendation:** Change to: `house_edge: House edge as a fraction. Positive (0 to 1) means house advantage; negative means player advantage.`

---

**5. New module not exported from analytics package `__init__.py`**

The new `progressive_analysis.py` module with its public types (`BreakevenResult`, `HouseEdgeResult`) and functions (`calculate_expected_payout`, `calculate_breakeven_jackpot`, `calculate_house_edge`) is not re-exported from `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/__init__.py`. The package docstring also does not mention progressive analysis.

Every other analytics submodule (statistics, validation, comparison, risk_of_ruin, etc.) is exported from `__init__.py`. This inconsistency means users must know to import directly from the submodule.

**Recommendation:** Add imports and `__all__` entries for the new public types and functions in the analytics `__init__.py`. Update the package docstring to mention progressive analysis.

### Low Severity

**6. Test comment contradicts its own assertion range**

In `/Users/chrishenry/source/let_it_ride/tests/unit/analytics/test_progressive_analysis.py`, lines 634-639 of the diff (test class `TestCalculateBreakevenJackpot.test_standard_paytable_breakeven_range`):

```python
def test_standard_paytable_breakeven_range(self) -> None:
    """Standard paytable breakeven should be in ~$200K-$250K range."""
    ...
    # Breakeven should be roughly in the $100K-$200K range for $1 bet
    assert 100_000 < result.breakeven_jackpot < 200_000
```

The docstring says "$200K-$250K" but the comment and assertion check "$100K-$200K". The scratchpad says ~$134K. The docstring is wrong.

**Recommendation:** Update the docstring to match: `"""Standard paytable breakeven should be in ~$100K-$200K range."""`

---

**7. `aggregate_results()` docstring does not mention progressive breakdown**

In `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/aggregation.py`, lines 122-138, the `aggregate_results()` docstring mentions the main/bonus breakdown assumption but does not mention that progressive winnings are now tracked separately and subtracted from `main_won`:

```python
"""Aggregate multiple session results into summary statistics.

Note: SessionResult does not track main game and bonus payouts separately.
The main/bonus breakdown assumes bonus is break-even (bonus_won = bonus_wagered),
with all profit/loss attributed to the main game.
```

The note should mention that progressive winnings are tracked separately (via `total_progressive_won`) and are excluded from `main_won`.

**Recommendation:** Update the note to: "The main/bonus breakdown assumes bonus is break-even (bonus_won = bonus_wagered). Progressive winnings are tracked separately via total_progressive_won. Remaining profit/loss is attributed to the main game."

### Informational

**8. `_SeatState` class lacks attribute-level docstrings for new field**

The `_SeatState` class in `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/table_session.py` (line 126) is an internal class (prefixed with underscore) and uses `__slots__` without attribute docstrings. The new `total_progressive_won` slot follows the existing undocumented pattern. This is acceptable for an internal class but noted for completeness.

---

**9. Scratchpad breakeven value (~$134K) vs. standard progressive paytable analysis**

The scratchpad `/Users/chrishenry/source/let_it_ride/scratchpads/issue-157-progressive-ev-analysis.md` states "Breakeven jackpot for standard paytable: ~$134K (for $1 bet)." This is consistent with the test assertion range ($100K-$200K) but the scratchpad does not show the derivation. Given the standard paytable has Royal Flush at 100% and Straight Flush at 10%, the breakeven is dominated by the Royal Flush probability (4/2,598,960 ~ 1.54e-6), giving approximately $1 / (1.54e-6 * 1.0 + 1.39e-5 * 0.1) ~ $1 / (1.54e-6 + 1.39e-6) ~ $1 / 2.93e-6 ~ $341K before subtracting fixed EV. After subtracting fixed EV (~$0.566), the breakeven drops. The ~$134K figure appears plausible given the fixed EV contribution.

---

**10. No updates to configuration documentation or README**

The `docs/let_it_ride_implementation_plan.md` is marked as modified in git status, and the `CLAUDE.md` already documents `progressive` config options. Since this PR adds analytical functions (not new configuration keys or CLI features), no configuration documentation update appears necessary. However, if the progressive analysis functions are intended to be user-facing (e.g., callable from CLI or config), documentation would be needed in a future PR.
