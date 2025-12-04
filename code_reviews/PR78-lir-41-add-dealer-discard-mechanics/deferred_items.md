# Deferred Items - PR #78

## Summary

Items identified during code review that were deferred for future implementation.

## Items

| Severity | Issue | Reviewer | Reason | Target Issue |
|----------|-------|----------|--------|--------------|
| High | DeckEmptyError edge case test | test-coverage | Impossible with current constraints | LIR-34 (GitHub #37) |
| Medium | YAML loader test for dealer section | test-coverage | Outside PR scope | LIR-34 (GitHub #37) |

## Target Issue

Both items assigned to **LIR-34: End-to-End Integration Test** (GitHub #37)

## Details

### DeckEmptyError Edge Case Test

- **Original Finding:** When `discard_cards` is set high (e.g., 10) combined with 5 cards for player/community, this still fits in a 52-card deck. However, there is no test verifying behavior when the deck cannot satisfy the discard request.
- **Why Deferred:** Currently impossible with constraints (max 10 discard + 5 deal = 15 cards < 52). Defensive test for future constraint changes.
- **Target:** E2E test suite will include edge case boundary tests.

### YAML Loader Test for Dealer Section

- **Original Finding:** The PR adds `DealerConfig` to the configuration model but does not include tests verifying that YAML files with a `dealer:` section are correctly parsed and loaded.
- **Why Deferred:** Requires creating new test file (`test_loader.py`) outside the PR scope of dealer mechanics.
- **Target:** E2E test suite will test all configuration loading including dealer section.
