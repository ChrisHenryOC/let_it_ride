# LIR-11: Baseline Strategies (Always Ride / Always Pull)

**GitHub Issue:** [#14](https://github.com/ChrisHenryOC/let_it_ride/issues/14)

## Summary

Implement two baseline comparison strategies for variance analysis:
- `AlwaysRideStrategy` - always returns RIDE for both decisions (maximum variance)
- `AlwaysPullStrategy` - always returns PULL for both decisions (minimum variance)

## Implementation Plan

### 1. Create `src/let_it_ride/strategy/baseline.py`

Simple implementations that ignore the HandAnalysis and StrategyContext parameters:

```python
class AlwaysRideStrategy:
    """Maximum variance baseline - never pulls."""
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        return Decision.RIDE

    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        return Decision.RIDE

class AlwaysPullStrategy:
    """Minimum variance baseline - always pulls (only bet 3 remains)."""
    def decide_bet1(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        return Decision.PULL

    def decide_bet2(self, analysis: HandAnalysis, context: StrategyContext) -> Decision:
        return Decision.PULL
```

Note: Use `# noqa: ARG002` to suppress unused argument warnings since these strategies deliberately ignore the parameters.

### 2. Export from `strategy/__init__.py`

Add `AlwaysRideStrategy` and `AlwaysPullStrategy` to the imports and `__all__` list.

### 3. Write tests in `tests/unit/strategy/test_baseline.py`

Test cases:
- Both strategies return correct Decision for Bet 1 (3-card hands)
- Both strategies return correct Decision for Bet 2 (4-card hands)
- Both strategies conform to the Strategy protocol
- Verify they ignore context values (test with various context states)

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/let_it_ride/strategy/baseline.py` | Create |
| `src/let_it_ride/strategy/__init__.py` | Modify (add exports) |
| `tests/unit/strategy/test_baseline.py` | Create |

## Dependencies

Depends on:
- `Strategy` protocol from `base.py` (implemented in LIR-10, GitHub #10)
- `Decision`, `StrategyContext` types from `base.py`
- `HandAnalysis` from `core/hand_analysis.py`
