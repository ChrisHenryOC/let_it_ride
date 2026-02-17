# Security Review -- PR #160

## Summary

This PR adds a standalone analytical module for progressive jackpot EV, breakeven, and house edge calculations, plus tracking of `total_progressive_won` through the session/table/aggregation pipeline and CSV export. The changes are primarily computational (pure math on internal data) with no external input handling, no file I/O on user-controlled paths, no deserialization, and no shell commands. The security risk surface is minimal.

## Findings

### High Severity

None

### Medium Severity

None

### Low Severity

**1. Missing input validation on `bet_amount` allows negative values (CWE-20: Improper Input Validation)**

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, lines 130-177 (`calculate_breakeven_jackpot`) and lines 180-213 (`calculate_house_edge`)
- **Description:** Both `calculate_breakeven_jackpot` and `calculate_house_edge` accept a `bet_amount` parameter with no validation that it is positive. A zero `bet_amount` in `calculate_house_edge` is handled (line 203: `if bet_amount > 0 else 0.0`), but a negative `bet_amount` would silently produce mathematically valid but semantically meaningless results (e.g., a negative breakeven jackpot). Similarly, `jackpot_amount` and `contribution_rate` have no bounds checks.
- **Recommendation:** Add validation at the top of public functions to reject negative or zero `bet_amount`, negative `jackpot_amount`, and `contribution_rate` outside [0, 1]. Since these are analytical functions operating on internal data rather than user-supplied input, this is low severity.

**2. Negative breakeven jackpot possible when `fixed_ev > bet_amount` (CWE-682: Incorrect Calculation)**

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, line 168
- **Description:** The formula `breakeven_jackpot = (bet_amount - fixed_ev) / percentage_ev_coefficient` can produce a negative result if `fixed_ev` exceeds `bet_amount`. This would mean the fixed payouts alone exceed the bet (the bet is always +EV regardless of jackpot), which is a valid mathematical outcome, but a consumer of `BreakevenResult` might not expect a negative `breakeven_jackpot` value and could misinterpret it.
- **Recommendation:** Document this edge case in the docstring, or add a note/field to `BreakevenResult` indicating that when `breakeven_jackpot < 0`, the bet is inherently +EV from fixed payouts alone.

### Informational

**1. Floating-point comparison for division-by-zero guard**

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, line 163
- **Description:** The check `if percentage_ev_coefficient == 0.0` uses exact float equality. In this specific context the coefficient is a sum of products of rational constants, so it will only be exactly 0.0 when there are truly no percentage payouts -- making this safe in practice. No change needed.

**2. `contribution_rate` is stored but unused in calculations**

- **File:** `/Users/chrishenry/source/let_it_ride/src/let_it_ride/analytics/progressive_analysis.py`, lines 133, 184
- **Description:** The `contribution_rate` parameter is accepted and stored in both `BreakevenResult` and `HouseEdgeResult` but is not actually used in the EV/breakeven/house-edge formulas. This is not a security issue but could mislead callers into thinking it affects the calculation. This appears intentional (for informational purposes in the result), but worth noting.

**3. No resource exhaustion concerns**

- The aggregation functions iterate over `list[SessionResult]` in a single pass with O(n) time and O(n) memory (for session_profits tuple). The analytical functions iterate over paytable entries (bounded, small set). No unbounded loops or allocations are present.

**4. No injection, XSS, CSRF, or authentication concerns**

- All changes are internal computational logic. No user-supplied strings are interpolated into queries, commands, or output formats. The CSV export field addition (`total_progressive_won`) follows the existing safe pattern of writing pre-validated numeric data.
