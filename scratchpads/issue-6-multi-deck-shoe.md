# Issue #6: Multi-Deck Shoe Implementation [CANCELLED]

**Issue Link:** https://github.com/ChrisHenryOC/let_it_ride/issues/6
**Status:** CANCELLED

## Decision Summary

**Date:** 2025-11-30

After analysis, it was determined that multi-deck shoes are not a realistic scenario for Let It Ride simulation. In actual casino play:

- Each hand is dealt from a freshly shuffled single deck
- The deck is reshuffled between hands
- There is no "shoe penetration" or card counting opportunity

Therefore, this issue and the related Composition-Dependent Strategy (Issue #39) have been cancelled.

## Impact Assessment

### Cancelled Issues
1. **Issue #6** (GitHub #6): Multi-Deck Shoe Implementation
2. **Issue #39** (GitHub #39): Composition-Dependent Strategy

### Updated Documents
1. `docs/let_it_ride_requirements.md`:
   - Removed Section 2.3.2 (Multi-Deck Shoe Mode)
   - Removed FR-107 through FR-110 (multi-deck requirements)
   - Removed FR-207 (composition-dependent strategy)
   - Removed FR-506 (multi-deck simulation mode)
   - Removed FR-610 (single vs multi-deck comparison)
   - Simplified deck configuration section
   - Removed composition_dependent strategy type
   - Removed deck composition variables from hand analysis
   - Updated example configs to remove multi-deck settings

2. `docs/let_it_ride_implementation_plan.md`:
   - Marked Issue #3 as CANCELLED
   - Marked Issue #36 as CANCELLED
   - Updated dependency graph
   - Updated summary table (40 → 38 issues)
   - Updated Game Engine (#13) dependencies

### Updated GitHub Issues
1. **#16** (Game Engine Orchestration): Removed shoe references, updated dependencies
2. **#11** (YAML Configuration): Removed multi-deck config options
3. **#36** (Sample Configurations): Removed multi_deck.yaml

### Deleted Files
- `src/let_it_ride/core/shoe.py` (partial implementation)

## Existing Implementation Status

The existing `Deck` class (`src/let_it_ride/core/deck.py`) from Issue #5 is sufficient:
- Standard 52-card deck
- Fisher-Yates shuffle with injectable RNG
- Card dealing and tracking
- Reset functionality for reshuffling between hands

No additional shoe/multi-deck functionality is needed.

## Technical Notes

For the simulator:
1. Create a single `Deck` instance per session
2. Before each hand: call `deck.reset()` then `deck.shuffle(rng)`
3. Deal 5 cards (3 player + 2 community)
4. Repeat for next hand

This matches real casino behavior where each hand starts with a fresh shuffle.
