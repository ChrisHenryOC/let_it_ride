# LIR-44: Chair Position Analytics

**GitHub Issue:** #74
**Status:** In Progress

## Overview

Implement analytics for comparing results by seat position, answering the research question: "Does the seat you're in affect your winning percentage?"

## Dependencies (Verified)

- **LIR-43 (Multi-Player Session Management)**: Complete
  - `TableSessionResult` in `simulation/table_session.py:108-120`
  - `SeatSessionResult` wraps `SessionResult` with `seat_number` (1-based)

- **LIR-25 (Core Statistics Calculator)**: Complete
  - `calculate_wilson_confidence_interval()` in `analytics/validation.py:167-205`
  - `ChiSquareResult` dataclass for chi-square tests

## Design

### Data Flow

1. Input: `list[TableSessionResult]` (multiple table sessions)
2. Each `TableSessionResult` contains `seat_results: tuple[SeatSessionResult, ...]`
3. Each `SeatSessionResult` has `seat_number` (1-6) and `session_result`
4. `SessionResult.outcome` is `SessionOutcome.WIN/LOSS/PUSH`
5. Aggregate by seat position, calculate statistics, run chi-square test

### Key Insight

The chi-square test for seat position independence tests:
- **Null hypothesis**: Seat position does not affect outcomes (wins distributed uniformly)
- **Observed**: Count of wins per seat
- **Expected**: `total_wins / num_seats` per seat (uniform distribution)
- If `p_value > 0.05`: Cannot reject null, position appears independent

### Types

```python
@dataclass(frozen=True, slots=True)
class SeatStatistics:
    seat_number: int
    total_rounds: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    win_rate_ci_lower: float
    win_rate_ci_upper: float
    expected_value: float  # avg profit per round
    total_profit: float

@dataclass(frozen=True, slots=True)
class ChairPositionAnalysis:
    seat_statistics: tuple[SeatStatistics, ...]
    chi_square_statistic: float
    chi_square_p_value: float
    is_position_independent: bool  # True if p > 0.05
```

### Functions

```python
def analyze_chair_positions(
    results: list[TableSessionResult],
    confidence_level: float = 0.95,
    significance_level: float = 0.05,
) -> ChairPositionAnalysis:
    """Analyze outcomes by seat position to test independence."""

def _aggregate_seat_data(
    results: list[TableSessionResult],
) -> dict[int, _SeatAggregation]:
    """Aggregate session outcomes by seat number."""

def _calculate_seat_statistics(
    seat_number: int,
    aggregation: _SeatAggregation,
    confidence_level: float,
) -> SeatStatistics:
    """Calculate statistics for a single seat."""

def _test_seat_independence(
    seat_stats: list[SeatStatistics],
    significance_level: float,
) -> tuple[float, float, bool]:
    """Run chi-square test for seat independence."""
```

## Implementation Tasks

1. Create `src/let_it_ride/analytics/chair_position.py`
   - Define `SeatStatistics` and `ChairPositionAnalysis` dataclasses
   - Implement aggregation helper
   - Implement per-seat statistics with Wilson CI
   - Implement chi-square test for independence
   - Main `analyze_chair_positions()` function

2. Update `src/let_it_ride/analytics/__init__.py`
   - Export `SeatStatistics`, `ChairPositionAnalysis`, `analyze_chair_positions`

3. Create `tests/unit/analytics/test_chair_position.py`
   - Factory function for creating test `TableSessionResult`
   - Test edge cases: empty results, single seat, single round
   - Test uniform distribution (should be independent)
   - Test biased distribution (should NOT be independent)
   - Test Wilson CI calculations
   - Test dataclass immutability

## Test Strategy

### Test Cases

1. **Empty input**: Should raise `ValueError`
2. **Single seat**: Should work, chi-square not meaningful but computable
3. **Uniform wins across seats**: High p-value, `is_position_independent=True`
4. **Biased wins (one seat wins much more)**: Low p-value, `is_position_independent=False`
5. **All wins**: Edge case for CI calculation
6. **All losses**: Edge case for CI calculation
7. **Mixed outcomes**: Normal case verification

### Known Values

For uniform distribution with 6 seats, each with 100 sessions and ~30% win rate:
- Expected wins per seat: 30
- Chi-square should be low (close to 0)
- p-value should be high (close to 1)
