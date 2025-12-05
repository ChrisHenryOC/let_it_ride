# Code Quality Review: PR #92 - LIR-45: Table Integration Tests

## Summary

This PR adds a comprehensive 1069-line integration test suite for the Table and TableSession classes. The tests are well-organized into logical test classes covering lifecycle, strategies, bankroll tracking, bonus bets, reproducibility, and edge cases. While the overall quality is good with clear naming and appropriate test isolation, there are opportunities to reduce code duplication through shared helper methods and fixtures, and a few test patterns could be improved for robustness.

## Findings by Severity

### Medium

#### M1: Repeated Table/Session Setup Pattern (DRY Violation)

**File:** `tests/integration/test_table.py`
**Lines:** 129-142, 163-175, 188-213, 223-248, and many more throughout

The same Table and TableSession setup pattern is repeated extensively throughout the test file. Nearly every test method creates:
1. A `TableSessionConfig`
2. A `Deck` instance
3. A strategy instance
4. A `Table` instance with nearly identical parameters
5. A `FlatBetting` system

**Example (repeated ~20+ times):**
```python
config = TableSessionConfig(
    table_config=TableConfig(num_seats=N),
    starting_bankroll=X,
    base_bet=Y,
    max_hands=Z,
)
deck = Deck()
strategy = SomeStrategy()
table = Table(deck, strategy, main_paytable, None, rng, table_config=TableConfig(num_seats=N))
betting_system = FlatBetting(Y)
session = TableSession(config, table, betting_system)
```

**Recommendation:** Create a helper method or factory fixture to reduce this boilerplate:

```python
def _create_session(
    self,
    main_paytable: MainGamePaytable,
    rng: random.Random,
    num_seats: int = 1,
    starting_bankroll: float = 500.0,
    base_bet: float = 5.0,
    max_hands: int | None = None,
    win_limit: float | None = None,
    loss_limit: float | None = None,
    strategy: Strategy | None = None,
    bonus_paytable: BonusPaytable | None = None,
    bonus_bet: float = 0.0,
    dealer_config: DealerConfig | None = None,
) -> TableSession:
    """Factory method for creating TableSession with common defaults."""
    ...
```

---

#### M2: Test Using Loop to Find Favorable Seed is Fragile

**File:** `tests/integration/test_table.py`
**Lines:** 129-155

```python
def test_single_seat_session_to_win_limit(
    self,
    main_paytable: MainGamePaytable,
) -> None:
    """Verify single-seat session runs until win limit is reached."""
    # Use a specific seed that produces early wins
    # Seed 999 tested to produce wins that hit the limit
    for seed in range(1000, 1100):
        config = TableSessionConfig(...)
        ...
        if result.stop_reason == StopReason.WIN_LIMIT:
            ...
            return

    pytest.skip("Could not find seed that produces win limit condition")
```

**Issues:**
1. The test may succeed today but fail if the underlying game logic changes
2. Looping through 100 seeds adds unnecessary test execution time
3. The comment mentions "Seed 999" but the loop starts at 1000

**Recommendation:** Either:
- Find and hard-code a known working seed with a comment explaining why it works
- Or create a mock/controlled scenario that guarantees the win limit is hit

---

#### M3: Duplicate TableConfig Instantiation

**File:** `tests/integration/test_table.py`
**Lines:** 195-209, 229-245, 583-591

The `TableConfig` is instantiated twice with the same parameters - once in `TableSessionConfig` and again when creating the `Table`:

```python
config = TableSessionConfig(
    table_config=TableConfig(num_seats=3),  # First instantiation
    ...
)
table = Table(
    ...
    table_config=TableConfig(num_seats=3),  # Duplicate instantiation
)
```

**Recommendation:** Create the `TableConfig` once and reuse it:

```python
table_config = TableConfig(num_seats=3)
config = TableSessionConfig(table_config=table_config, ...)
table = Table(..., table_config=table_config)
```

---

### Low

#### L1: Magic Numbers for Test Configuration

**File:** `tests/integration/test_table.py`
**Lines:** Various (e.g., 132-135, 164-167, 194-199, etc.)

Test configurations use various magic numbers without explanation:
- `starting_bankroll=500.0`, `200.0`, `1000.0`, `1_000_000.0`
- `base_bet=5.0`, `10.0`, `100.0`
- `max_hands=20`, `30`, `50`, `100`
- `win_limit=100.0`, `loss_limit=100.0`

**Recommendation:** For commonly used values, define constants at module level:

```python
# Test constants
DEFAULT_STARTING_BANKROLL = 500.0
DEFAULT_BASE_BET = 5.0
DEFAULT_MAX_HANDS = 50
```

Or use the existing fixture values more consistently.

---

#### L2: Assertions Could Be More Specific

**File:** `tests/integration/test_table.py`
**Lines:** 501-507

```python
# Peak should be at least starting (if never went above) or higher
assert (
    sr.peak_bankroll >= sr.starting_bankroll
    or sr.peak_bankroll >= sr.final_bankroll
)
```

This assertion is always true because `peak_bankroll` is by definition the maximum value reached. The condition `sr.peak_bankroll >= sr.final_bankroll` is always true. Consider simplifying:

```python
# Peak must be at least as high as starting bankroll (minimum case: no wins)
assert sr.peak_bankroll >= sr.starting_bankroll
```

---

#### L3: Unused Fixture Import

**File:** `tests/integration/test_table.py`
**Lines:** 104-107

The `bonus_paytable` fixture is defined but only used in a few tests. Most tests could benefit from using `bonus_paytable_b()` directly where needed, or the fixture could be made more widely available.

---

#### L4: Context Tracking Strategy Uses Tuple Instead of Named Structure

**File:** `tests/integration/test_table.py`
**Lines:** 1078-1098

```python
class ContextTrackingStrategy:
    context_history: list[tuple[float, int, int, float]]

    def decide_bet1(...):
        self.context_history.append(
            (
                context.session_profit,
                context.hands_played,
                context.streak,
                context.bankroll,
            )
        )
```

Using a tuple makes accessing values later less readable. Consider using `StrategyContext` directly or a named tuple.

**Recommendation:**
```python
context_history: list[StrategyContext]

def decide_bet1(...):
    self.context_history.append(context)
```

---

#### L5: Test Class Without Shared Setup

**File:** `tests/integration/test_table.py`
**Lines:** 263-407

`TestTableWithStrategies` has multiple test methods that all create very similar Table configurations. A `setup_method` or class-level fixtures could reduce duplication.

---

### Positive Observations

1. **Excellent Test Organization:** Tests are well-organized into logical test classes by functionality (lifecycle, strategies, bankroll, bonus, reproducibility, edge cases)

2. **Clear Test Naming:** Test method names clearly describe what is being tested (e.g., `test_same_seed_produces_identical_session`, `test_bonus_bet_evaluated_per_seat`)

3. **Good Edge Case Coverage:** Tests cover boundary conditions like maximum seats with maximum discard, minimum bankroll, and large bankrolls

4. **Proper Type Hints:** All fixtures and test methods include proper type hints as required by project standards

5. **Custom Strategy Classes:** The inline `ContextCapturingStrategy` and `ContextTrackingStrategy` classes effectively test context passing without needing external mock frameworks

6. **Reproducibility Testing:** Strong tests verifying that the same seed produces identical results across separate runs

## Recommendations Summary

1. **High Priority:** Create a helper method or factory fixture for TableSession setup to reduce the ~500+ lines of repeated boilerplate code

2. **Medium Priority:** Fix the fragile seed-searching test by identifying a known working seed or using a controlled test setup

3. **Medium Priority:** Eliminate duplicate `TableConfig` instantiations by storing in a variable and reusing

4. **Low Priority:** Consider defining test constants for commonly used values to improve readability and maintainability

5. **Low Priority:** Simplify the peak bankroll assertion logic
