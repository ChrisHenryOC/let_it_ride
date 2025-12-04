# LIR-14: Bonus Betting Strategies (GitHub #17)

GitHub Issue: https://github.com/ChrisHenryOC/let_it_ride/issues/17

## Summary

Implemented bonus betting strategies for the Three-Card Bonus side bet in Let It Ride.

## Implementation

### Files Created
- `src/let_it_ride/strategy/bonus.py` - Core bonus strategy implementations
- `tests/unit/strategy/test_bonus.py` - Comprehensive unit tests (50 tests)

### Files Modified
- `src/let_it_ride/strategy/__init__.py` - Added exports for bonus strategy classes

### Key Types

#### BonusContext
A frozen dataclass providing session state to bonus strategies:
- `bankroll` / `starting_bankroll` - Current and initial bankroll
- `session_profit` - Current profit/loss
- `hands_played` - Number of hands this session
- `main_streak` / `bonus_streak` - Win/loss streaks
- `base_bet` - Main game base bet
- `min_bonus_bet` / `max_bonus_bet` - Table limits

#### BonusStrategy Protocol
Single method: `get_bonus_bet(context: BonusContext) -> float`

### Strategies Implemented

1. **NeverBonusStrategy** - Always returns 0 (disables bonus betting)
2. **AlwaysBonusStrategy** - Fixed amount on every hand
3. **StaticBonusStrategy** - Fixed amount OR ratio of base bet
4. **BankrollConditionalBonusStrategy** - Conditional betting with:
   - Minimum session profit threshold
   - Minimum bankroll ratio threshold
   - Maximum drawdown limit
   - Profit percentage betting
   - Profit-based scaling tiers

### Factory Function
`create_bonus_strategy(config: BonusStrategyConfig) -> BonusStrategy`
Creates strategy instances from config models.

### Not Yet Implemented
- `streak_based` strategy
- `session_conditional` strategy
- `combined` strategy
- `custom` strategy

These raise `NotImplementedError` when requested - can be added in future issues.

## Design Decisions

1. **Clamping Logic**: All strategies clamp to min/max limits. Below min returns 0.
2. **Zero Division Protection**: Ratio conditions skip check if starting_bankroll is 0.
3. **Config Integration**: Factory function converts Pydantic config models to strategy instances.
4. **Protocol Conformance**: All strategies implement BonusStrategy protocol without inheritance.

## Test Coverage

- 50 unit tests covering:
  - Basic functionality for each strategy
  - Edge cases (zero bankroll, large amounts, limits)
  - Protocol conformance
  - Factory function behavior
  - Configuration parsing

All tests pass with ruff and mypy clean.
