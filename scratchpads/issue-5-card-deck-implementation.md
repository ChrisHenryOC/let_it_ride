# Issue #5: Card and Deck Implementation

**Issue Link:** https://github.com/ChrisHenryOC/let_it_ride/issues/5

## Overview

Implement the fundamental card representation and single-deck management with Fisher-Yates shuffling.

## Acceptance Criteria

- [x] `Card` dataclass with rank, suit, and comparison methods
- [x] `Rank` enum (TWO through ACE) with proper ordering
- [x] `Suit` enum (CLUBS, DIAMONDS, HEARTS, SPADES)
- [x] `Deck` class with shuffle (Fisher-Yates), deal, reset methods
- [x] Deck tracks dealt cards for statistical validation
- [x] Comprehensive unit tests for card creation and deck operations
- [x] Shuffling produces statistically uniform distribution (test with chi-square)

## Dependencies

Blocked by: #1 (Project Scaffolding) - ✅ Completed

## Files Created

1. `src/let_it_ride/core/card.py` - Card, Rank, Suit definitions
2. `src/let_it_ride/core/deck.py` - Deck class with shuffle/deal/reset
3. `tests/unit/core/test_card.py` - Unit tests for Card and enums
4. `tests/unit/core/test_deck.py` - Unit tests for Deck operations

## Important Design Decisions

### ACE Can Be High or Low

In Let It Ride and many poker variants, ACE can function as both the highest card (above KING) or the lowest card (below TWO) depending on context. For example:
- A-K-Q-J-T is the highest straight (ace-high)
- A-2-3-4-5 is the lowest straight (wheel)

Implementation:
- **Default ordering**: ACE > KING (value 14) - used by standard comparison operators
- **Low ordering**: ACE < TWO (value 1) - use `Rank.low_value()` or `Rank.compare_ace_low()`

```python
# Default (ACE high)
assert Rank.ACE > Rank.KING  # True

# ACE low
assert Rank.ACE.low_value() == 1
assert Rank.ACE.compare_ace_low(Rank.TWO) < 0  # ACE < TWO when low
```

### No Suit Ordering

In Let It Ride, suits have no inherent ranking or ordering. All suits are equal - what matters is whether cards share the same suit (for flushes) or not. Therefore:
- **Suit enum has no comparison operators**
- **Card comparison is by rank only**
- Attempting to compare suits raises `TypeError`

```python
# This raises TypeError:
Suit.SPADES < Suit.HEARTS  # TypeError

# Cards with same rank but different suits are neither < nor >
ace_spades = Card(Rank.ACE, Suit.SPADES)
ace_hearts = Card(Rank.ACE, Suit.HEARTS)
assert not (ace_spades < ace_hearts)  # Neither is less
assert not (ace_spades > ace_hearts)  # Neither is greater
assert ace_spades != ace_hearts  # But they're not equal (different suits)
```

## Implementation Details

### Rank Enum
- Values TWO (2) through ACE (14)
- Standard comparison operators use integer values
- `low_value()` method returns 1 for ACE, standard value otherwise
- `compare_ace_low()` method compares treating ACE as 1

### Suit Enum
- Four suits: CLUBS, DIAMONDS, HEARTS, SPADES
- Single-character values for string representation (c, d, h, s)
- No ordering/comparison operators

### Card Dataclass
- Frozen (immutable)
- Comparison by rank only (suits not ordered)
- `__str__` returns two-character format (e.g., "Ah")
- `__repr__` returns debug format (e.g., "Card(ACE, HEARTS)")

### Deck Class
- Standard 52-card deck
- Fisher-Yates shuffle with injectable RNG
- Tracks dealt cards for statistical validation
- `DeckEmptyError` raised when dealing from empty deck

## Technical Decisions

1. **Frozen dataclass** for Card - immutability prevents bugs
2. **Integer values for Rank** - enables natural ordering (2-14)
3. **ACE dual value** - `low_value()` method for straight detection
4. **No suit ordering** - matches game rules where suits are equal
5. **Fisher-Yates shuffle** - O(n) time, proven uniform distribution
6. **Dependency injection for RNG** - enables reproducible tests

## Test Coverage

- 100% code coverage on card.py and deck.py
- Chi-square statistical tests verify uniform shuffle distribution
- Tests for ACE low comparison
- Tests verifying suits cannot be compared
