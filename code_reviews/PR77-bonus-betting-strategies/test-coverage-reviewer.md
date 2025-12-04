# Test Coverage Review: PR #77 - Bonus Betting Strategies

## Summary

The test suite provides solid foundational coverage for the bonus betting strategies with 50 tests covering basic functionality, validation errors, and some edge cases. However, several critical scenarios are missing that could allow subtle bugs to slip through, particularly around boundary conditions at thresholds, the interaction between scaling tiers and profit_percentage, negative input amounts, zero/negative base_bet handling, and the unknown strategy type error path in the factory function.

---

## Findings by Severity

### Critical

#### 1. Missing Test: Unknown Strategy Type in Factory Function
**File:** `tests/unit/strategy/test_bonus.py`
**Impact:** The factory function has a final `raise ValueError` for unknown strategy types (bonus.py:358) that is never tested.

**Code Path (bonus.py:358):**
```python
raise ValueError(f"Unknown bonus strategy type: {strategy_type}")
```

**Recommendation:** Add test for completely unknown strategy type:
```python
def test_unknown_strategy_type_raises(self) -> None:
    """Test that unknown strategy type raises ValueError."""
    config = BonusStrategyConfig(type="never")
    object.__setattr__(config, "type", "unknown_strategy")
    with pytest.raises(ValueError, match="Unknown bonus strategy type"):
        create_bonus_strategy(config)
```

---

### High

#### 2. Missing Test: Boundary Condition at Exact min_session_profit Threshold
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~268-306 (TestBankrollConditionalBonusStrategy)
**Impact:** Tests exist for above/below threshold but not exactly AT the threshold. The code uses `<` comparison (bonus.py:256), so profit exactly at threshold should allow betting.

**Code Path (bonus.py:254-258):**
```python
if (
    self._min_session_profit is not None
    and context.session_profit < self._min_session_profit
):
    return 0.0
```

**Recommendation:** Add boundary test:
```python
def test_bets_when_exactly_at_min_session_profit(self) -> None:
    """Test that bet is placed when session profit equals minimum exactly."""
    strategy = BankrollConditionalBonusStrategy(
        base_amount=5.0,
        min_session_profit=100.0,
    )
    context = BonusContext(
        bankroll=1100.0,
        starting_bankroll=1000.0,
        session_profit=100.0,  # Exactly at threshold
        ...
    )
    result = strategy.get_bonus_bet(context)
    assert result == 5.0  # Should bet at exact threshold
```

#### 3. Missing Test: Boundary Condition at Exact max_drawdown Threshold
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~348-386 (drawdown tests)
**Impact:** Tests exist for above/below max_drawdown but not exactly AT the threshold. Code uses `>` (bonus.py:271), so drawdown exactly at threshold should allow betting.

**Code Path (bonus.py:267-272):**
```python
if self._max_drawdown is not None and context.starting_bankroll > 0:
    drawdown = (context.starting_bankroll - context.bankroll) / context.starting_bankroll
    if drawdown > self._max_drawdown:
        return 0.0
```

**Recommendation:** Add boundary test:
```python
def test_bets_when_exactly_at_max_drawdown(self) -> None:
    """Test that bet is placed when drawdown equals max exactly."""
    strategy = BankrollConditionalBonusStrategy(
        base_amount=5.0,
        max_drawdown=0.20,
    )
    context = BonusContext(
        bankroll=800.0,  # Exactly 20% drawdown
        starting_bankroll=1000.0,
        session_profit=-200.0,
        ...
    )
    result = strategy.get_bonus_bet(context)
    assert result == 5.0  # Should bet at exact threshold
```

#### 4. Missing Test: Boundary Condition at Exact min_bankroll_ratio Threshold
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~308-346
**Impact:** Same pattern - tests for above/below but not exactly at threshold. Code uses `<` (bonus.py:263).

**Recommendation:** Add test for `bankroll == starting_bankroll * min_bankroll_ratio` (ratio exactly 1.0).

#### 5. Missing Test: Negative Amount Passed to AlwaysBonusStrategy
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~145-186 (TestAlwaysBonusStrategy)
**Impact:** The `_clamp_bonus_bet` function handles negative bets by returning 0 (bonus.py:80-81), but this is never tested.

**Code Path (bonus.py:80-81):**
```python
if bet <= 0:
    return 0.0
```

**Recommendation:** Add test:
```python
def test_negative_amount_returns_zero(self, default_context: BonusContext) -> None:
    """Test that negative amount returns 0."""
    strategy = AlwaysBonusStrategy(amount=-5.0)
    result = strategy.get_bonus_bet(default_context)
    assert result == 0.0
```

#### 6. Missing Test: Zero Amount Passed to AlwaysBonusStrategy
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~145-186
**Impact:** Zero amount should return 0.0 per `_clamp_bonus_bet` (bonus.py:80-81).

**Recommendation:** Add test for `AlwaysBonusStrategy(amount=0.0)` returning 0.

---

### Medium

#### 7. Missing Test: Zero base_bet with StaticBonusStrategy Ratio Mode
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~189-253 (TestStaticBonusStrategy)
**Impact:** When `base_bet=0.0` and ratio mode is used, the result would be `0.0 * ratio = 0.0`. This edge case is untested.

**Code Path (bonus.py:188):**
```python
bet = context.base_bet * self._ratio
```

**Recommendation:** Add test:
```python
def test_ratio_with_zero_base_bet(self) -> None:
    """Test ratio mode with zero base_bet returns 0."""
    strategy = StaticBonusStrategy(ratio=0.5)
    context = BonusContext(
        ...,
        base_bet=0.0,
        min_bonus_bet=1.0,
        max_bonus_bet=25.0,
    )
    result = strategy.get_bonus_bet(context)
    assert result == 0.0  # Below min_bonus_bet
```

#### 8. Missing Test: Scaling Tiers with profit_percentage Interaction
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~431-520
**Impact:** When both `scaling_tiers` AND `profit_percentage` are set, profit_percentage overrides the tier (bonus.py:287-289). This interaction is not tested.

**Code Path (bonus.py:278-289):**
```python
# Check scaling tiers
if self._scaling_tiers:
    for min_profit, max_profit, tier_amount in self._scaling_tiers:
        ...
        if in_range:
            bet = tier_amount
            break

# Override with profit percentage if set
if self._profit_percentage is not None and context.session_profit > 0:
    bet = context.session_profit * self._profit_percentage
```

**Recommendation:** Add test:
```python
def test_profit_percentage_overrides_scaling_tiers(self) -> None:
    """Test that profit_percentage takes precedence over scaling tiers."""
    strategy = BankrollConditionalBonusStrategy(
        base_amount=1.0,
        profit_percentage=0.05,  # 5% of profit
        scaling_tiers=[
            (0.0, 100.0, 10.0),  # Would select 10.0 for profit 50
        ],
    )
    context = BonusContext(
        bankroll=1050.0,
        starting_bankroll=1000.0,
        session_profit=50.0,  # 5% = 2.5, tier would give 10.0
        ...
        min_bonus_bet=1.0,
        max_bonus_bet=25.0,
    )
    result = strategy.get_bonus_bet(context)
    assert result == 2.5  # profit_percentage wins over tier
```

#### 9. Missing Test: Scaling Tiers at Boundary Values
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~431-482
**Impact:** Tier boundaries use `>=` for min and `<` for max (bonus.py:280-281). Tests exist for values inside tiers but not exactly at boundaries.

**Recommendation:** Add tests for:
- `session_profit` exactly at tier min_profit boundary
- `session_profit` exactly at tier max_profit boundary (should fall into NEXT tier)

#### 10. Missing Test: Empty Scaling Tiers List
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~431-520
**Impact:** When `scaling_tiers=[]` (empty list), the code should use base_amount. This is different from `scaling_tiers=None`.

**Recommendation:** Add test:
```python
def test_empty_scaling_tiers_uses_base_amount(self) -> None:
    """Test that empty scaling tiers list uses base_amount."""
    strategy = BankrollConditionalBonusStrategy(
        base_amount=5.0,
        scaling_tiers=[],  # Empty list
    )
    ...
```

#### 11. Missing Test: Scaling Tiers with No Matching Tier
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~756-778 (test_negative_session_profit_with_scaling)
**Impact:** The existing test covers negative profit, but what about positive profit that doesn't match any tier? For example, tiers defined for 100+ but profit is 50.

**Recommendation:** Add test for gaps in tier coverage.

#### 12. Missing Test: Factory Creates Functional Strategy (Integration)
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~522-626
**Impact:** Factory tests only verify `isinstance()`. They don't verify the created strategy actually works correctly with the config values.

**Recommendation:** Add at least one test that creates a strategy via factory and calls `get_bonus_bet()`:
```python
def test_factory_creates_functional_always_strategy(self) -> None:
    """Test that factory-created AlwaysBonusStrategy works correctly."""
    config = BonusStrategyConfig(
        type="always",
        always=AlwaysBonusConfig(amount=7.0),
    )
    strategy = create_bonus_strategy(config)
    context = BonusContext(...)
    assert strategy.get_bonus_bet(context) == 7.0
```

---

### Low

#### 13. Missing Test: Negative base_bet Value
**File:** `tests/unit/strategy/test_bonus.py`
**Impact:** While unlikely in practice, negative `base_bet` with ratio mode would produce a negative bet amount, which should be clamped to 0.

#### 14. Missing Test: Very Small Float Values (Precision)
**File:** `tests/unit/strategy/test_bonus.py`
**Impact:** Testing with very small values like `0.001` for amount/ratio could reveal floating-point precision issues.

#### 15. Missing Test: BonusContext Immutability Verification
**File:** `tests/unit/strategy/test_bonus.py`
**Impact:** BonusContext is `frozen=True`. A test verifying that modification raises `FrozenInstanceError` would document this contract.

#### 16. Missing Test: Protocol Runtime Check with typing.runtime_checkable
**File:** `tests/unit/strategy/test_bonus.py`
**Lines:** ~628-678
**Impact:** The protocol conformance tests check `hasattr` and `callable`, but don't verify actual protocol compliance using `isinstance()` with `@runtime_checkable`.

#### 17. Missing Test: StaticBonusStrategy Ratio Below min_bonus_bet
**File:** `tests/unit/strategy/test_bonus.py`
**Impact:** Test exists for amount below min, but not for ratio calculation resulting in value below min.

**Recommendation:**
```python
def test_ratio_result_below_min_returns_zero(self) -> None:
    """Test ratio result below min_bonus_bet returns 0."""
    strategy = StaticBonusStrategy(ratio=0.01)  # 1% of base_bet
    context = BonusContext(
        ...,
        base_bet=10.0,  # 10 * 0.01 = 0.1, below min_bonus_bet of 1.0
        min_bonus_bet=1.0,
        max_bonus_bet=25.0,
    )
    assert strategy.get_bonus_bet(context) == 0.0
```

---

## Coverage Summary

| Component | Tests | Coverage Assessment |
|-----------|-------|---------------------|
| NeverBonusStrategy | 6 | Good - covers multiple contexts |
| AlwaysBonusStrategy | 6 | Good - missing negative/zero amount |
| StaticBonusStrategy | 8 | Good - missing zero base_bet, ratio below min |
| BankrollConditionalBonusStrategy | 15 | Moderate - missing boundary conditions, tier interactions |
| create_bonus_strategy | 10 | Good - missing unknown type, functional verification |
| Protocol Conformance | 4 | Good |
| Edge Cases | 5 | Moderate - good coverage of zero/large values |

**Total Tests:** 50
**Estimated Missing Critical/High Tests:** 6
**Estimated Missing Medium/Low Tests:** 11

---

## Recommendations Summary

### Priority 1 (Critical/High - Should Add Before Merge)
1. Test unknown strategy type error path
2. Test boundary conditions (exact threshold values) for:
   - min_session_profit
   - min_bankroll_ratio
   - max_drawdown
3. Test negative/zero amount inputs

### Priority 2 (Medium - Should Add Soon)
4. Test zero base_bet with ratio mode
5. Test scaling_tiers + profit_percentage interaction
6. Test scaling tier boundary values
7. Test empty scaling tiers list
8. Add functional test for factory-created strategies

### Priority 3 (Low - Nice to Have)
9. Test very small float values
10. Test BonusContext immutability
11. Test ratio resulting in value below min_bonus_bet

---

## Code Quality Notes

The test file is well-organized with clear class structure and descriptive test names. The use of fixtures for common contexts is good practice. The parametrized test for NeverBonusStrategy is a good pattern that could be extended to other strategies.

Consider adding property-based testing with `hypothesis` for more thorough boundary exploration, particularly for the clamping logic and threshold comparisons.
