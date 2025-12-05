# Performance Review: PR #92 - Table Integration Tests (LIR-45)

## Summary

This PR adds 1,118 lines of integration tests for the Table and TableSession classes. The tests are well-structured but contain one notable performance concern: a seed-search loop in `test_single_seat_session_to_win_limit` that iterates up to 100 times to find a favorable RNG seed. The remaining test code follows good practices with appropriate fixture usage and reasonable iteration counts.

## Findings by Severity

### Medium

#### M1: Seed-Search Loop Could Slow Test Suite

**Location:** `tests/integration/test_table.py:129-155` (lines 129-155 in the new file)

**Issue:** The test `test_single_seat_session_to_win_limit` contains a loop that tries up to 100 different RNG seeds (1000-1099) searching for one that produces a win-limit condition. Each iteration creates new objects and runs a full session to completion.

```python
for seed in range(1000, 1100):
    config = TableSessionConfig(...)
    deck = Deck()
    rng = random.Random(seed)
    strategy = AlwaysRideStrategy()
    table = Table(deck, strategy, main_paytable, None, rng)
    betting_system = FlatBetting(5.0)

    session = TableSession(config, table, betting_system)
    result = session.run_to_completion()

    if result.stop_reason == StopReason.WIN_LIMIT:
        # ... assertions and return
```

**Impact:** In the worst case, this test could run 100 complete sessions before finding a suitable seed, or skip entirely if none is found. This adds unpredictable variance to test suite execution time.

**Recommendation:** Pre-determine a working seed and hardcode it, or use a mock/fixture that guarantees the win-limit condition. For example:

```python
def test_single_seat_session_to_win_limit(self, main_paytable: MainGamePaytable) -> None:
    """Verify single-seat session runs until win limit is reached."""
    # Seed 1042 verified to produce win limit with these parameters
    rng = random.Random(1042)
    config = TableSessionConfig(
        table_config=TableConfig(num_seats=1),
        starting_bankroll=500.0,
        base_bet=5.0,
        win_limit=100.0,
    )
    # ... rest of test
```

### Low

#### L1: Repeated Object Creation in Test Methods

**Location:** Multiple test methods throughout the file

**Issue:** Many tests create similar objects (Deck, Strategy, Table, etc.) in each test method rather than leveraging pytest fixtures more extensively. While this is acceptable for integration tests (ensuring isolation), it does add some overhead.

**Examples:**
- Lines 168-175, 200-211, 235-246: Each creates `Deck()`, strategy, `Table()` with similar patterns

**Impact:** Minor - the overhead is acceptable for integration tests and ensures test isolation.

**Recommendation:** Consider creating additional fixtures for common object combinations if test suite runtime becomes a concern. Current approach is acceptable for integration test purposes.

#### L2: Large Iteration Counts in Strategy Verification Tests

**Location:**
- `tests/integration/test_table.py:282` (100 iterations)
- `tests/integration/test_table.py:363` (100 iterations)
- `tests/integration/test_table.py:402` (50 iterations)

**Issue:** Tests iterate 100+ rounds to verify strategy behavior produces mixed decisions.

**Impact:** Minor - these are reasonable counts for statistical verification in integration tests.

**Recommendation:** No change needed. The iteration counts are appropriate for verifying probabilistic behavior.

### Informational

#### I1: Good Use of Fixtures

The PR demonstrates good pytest fixture usage for paytables and RNG:
- `main_paytable` fixture (lines 98-101)
- `bonus_paytable` fixture (lines 104-107)
- `rng` fixture with consistent seed (lines 110-113)

This promotes test consistency and reduces redundant setup.

#### I2: Test Isolation is Maintained

Each test method creates its own Table, Session, and Deck instances, ensuring no shared mutable state between tests. This is the correct approach for integration tests even though it has some performance cost.

## Resource Management Assessment

**Memory:** No memory leaks detected. Objects are created within test scope and properly garbage-collected after each test.

**File/Network Resources:** No external resources are opened. All tests use in-memory objects.

**Cleanup:** No explicit cleanup needed - Python's garbage collection handles all test objects appropriately.

## Parallelization Compatibility

The tests appear parallelization-safe:
- No shared mutable state between tests
- No file system operations
- No database connections
- Each test is self-contained

The tests should run correctly with `pytest-xdist` parallelization.

## Overall Assessment

The integration tests are well-designed from a performance perspective. The only actionable item is the seed-search loop in `test_single_seat_session_to_win_limit` which should be replaced with a known-good seed to ensure consistent, fast test execution.

**Test Suite Impact:** With the seed-search fix, these 1,100+ lines of tests should execute in under 5 seconds on typical hardware.
