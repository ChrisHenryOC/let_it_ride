# Documentation Accuracy Review -- PR #159 (LIR-63: Progressive Bet Strategies)

**Reviewer focus:** Docstring accuracy, parameter documentation, return value documentation, inline comments, CLAUDE.md/configuration docs, and consistency between code behavior and documentation.

## Summary

The new `progressive.py` module is well documented with accurate docstrings, proper Attributes sections on dataclasses, and consistent parameter/return documentation across all strategy classes and the factory function. There are a few gaps: CLAUDE.md does not mention the new `ProgressiveStrategy` protocol or the `progressive_strategy` configuration section, the existing progressive jackpot example YAML config does not demonstrate the new strategy options, and one config model docstring is slightly misleading about its default behavior. Overall documentation quality is high for a new module.

---

## Findings

### Medium Severity

**M1. CLAUDE.md "Key abstractions" list does not include `ProgressiveStrategy` protocol**

The CLAUDE.md Key abstractions section (line 53-61) lists `BonusStrategy` protocol but omits the new `ProgressiveStrategy` protocol, which follows the same pattern and is equally important for understanding the codebase.

- File: `/Users/chrishenry/source/let_it_ride/CLAUDE.md`, line 54
- In PR Scope: Yes
- Actionable: Yes

---

**M2. CLAUDE.md "Configuration" section does not document the new `progressive_strategy` YAML section**

The Configuration section at line 69-79 lists all top-level YAML config keys. The new `progressive_strategy` key (with types `never`, `always`, `jackpot_threshold`, `bankroll_conditional`) is missing. Users reading CLAUDE.md to understand available config options will not discover this feature.

- File: `/Users/chrishenry/source/let_it_ride/CLAUDE.md`, line 77 (after `progressive:` entry)
- In PR Scope: Yes
- Actionable: Yes

---

**M3. Architecture description in CLAUDE.md does not mention "progressive" in the strategy directory comment**

Line 44 describes the `strategy/` directory as "Strategy implementations: basic, baseline, custom, bonus" but now it also contains `progressive.py`. This should include "progressive" for discoverability.

- File: `/Users/chrishenry/source/let_it_ride/CLAUDE.md`, line 44
- In PR Scope: Yes
- Actionable: Yes

---

**M4. Example YAML config `progressive_jackpot.yaml` does not demonstrate `progressive_strategy`**

The existing `configs/examples/progressive_jackpot.yaml` configures the progressive side bet with `progressive.enabled: true` and `progressive.bet_amount: 1.00`, but does not include a `progressive_strategy` section. Since this is the primary example file for progressive features, adding a commented example of the new strategy options would improve discoverability.

- File: `/Users/chrishenry/source/let_it_ride/configs/examples/progressive_jackpot.yaml`, after line 76
- In PR Scope: Yes (directly related to the feature)
- Actionable: Yes

---

### Low Severity

**L1. `BankrollConditionalProgressiveConfig.min_bankroll_ratio` docstring says "exceeds" but code uses `>=` (meets or exceeds)**

The docstring at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py` line 1014 states "Only bet when bankroll ratio exceeds this." However, the implementation in `BankrollConditionalProgressiveStrategy.get_progressive_bet()` at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py` line 197 checks `current_ratio < self._min_bankroll_ratio` (i.e., it bets when the ratio is greater than **or equal to** the threshold). The word "exceeds" implies strictly greater than. The same imprecision applies to `min_session_profit` -- "exceeds" vs the code checking `<` (which allows equal).

- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/config/models.py`, lines 1013-1014
- In PR Scope: Yes
- Actionable: Yes

---

**L2. `ProgressiveContext` docstring says "Extends the information available in BonusContext" but it does not inherit from or compose BonusContext**

The docstring at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py` line 25 says "Extends the information available in BonusContext." This is conceptually accurate (it has overlapping fields plus jackpot-specific ones), but the word "Extends" could be misread as inheritance. A phrasing like "Provides similar information to BonusContext, with additional jackpot state" would be more precise.

- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py`, line 25
- In PR Scope: Yes
- Actionable: Yes

---

**L3. `JackpotThresholdStrategy` class docstring says "exceeds a threshold" but code uses `>=`**

The class docstring at line 115 says "only bets when the jackpot exceeds a threshold" but `get_progressive_bet` at line 149 checks `context.current_jackpot >= self._min_jackpot`. The docstring should say "meets or exceeds" for accuracy.

- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py`, line 115
- In PR Scope: Yes
- Actionable: Yes

---

**L4. `_create_table_session` does not receive or use `progressive_strategy_factory`**

This is primarily a code gap rather than a documentation issue, but the docstring and implementation of `_create_table_session` at `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py` line 565 make no mention of progressive strategy support. If `TableSession` is intended to support progressive strategies in the future, a note would be helpful. As-is, progressive strategies only work for single-seat `Session` -- this limitation is undocumented.

- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, line 565
- In PR Scope: Partially (the PR adds progressive_strategy to Session but not TableSession)
- Actionable: Yes

---

**L5. Inline comment "Progressive strategy needs fresh state per session" is misleading for stateless strategies**

At `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py` line 552, the comment says "Progressive strategy needs fresh state per session." However, all four current strategy implementations (`NeverProgressiveStrategy`, `AlwaysProgressiveStrategy`, `JackpotThresholdStrategy`, `BankrollConditionalProgressiveStrategy`) are stateless -- they have no mutable instance attributes. The factory pattern is reasonable for future extensibility, but the comment implies the strategies carry per-session state, which is currently inaccurate.

- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/simulation/controller.py`, line 552
- In PR Scope: Yes
- Actionable: Yes

---

**L6. Module docstring for `progressive.py` lists strategies but does not mention the factory function**

The module docstring at line 1-13 lists the four strategy classes but does not mention `create_progressive_strategy()`, which is an important public entry point for creating strategies from config.

- File: `/Users/chrishenry/source/let_it_ride/src/let_it_ride/strategy/progressive.py`, lines 1-13
- In PR Scope: Yes
- Actionable: Yes

---

## Findings Summary

| ID | Severity | File | Description | In PR Scope | Actionable |
|----|----------|------|-------------|-------------|------------|
| M1 | Medium | CLAUDE.md:54 | Missing `ProgressiveStrategy` in Key abstractions | Yes | Yes |
| M2 | Medium | CLAUDE.md:77 | Missing `progressive_strategy` in Configuration section | Yes | Yes |
| M3 | Medium | CLAUDE.md:44 | Strategy directory comment missing "progressive" | Yes | Yes |
| M4 | Medium | progressive_jackpot.yaml | No example of `progressive_strategy` config | Yes | Yes |
| L1 | Low | config/models.py:1013-1014 | "exceeds" should be "meets or exceeds" | Yes | Yes |
| L2 | Low | strategy/progressive.py:25 | "Extends" could imply inheritance | Yes | Yes |
| L3 | Low | strategy/progressive.py:115 | "exceeds" should be "meets or exceeds" | Yes | Yes |
| L4 | Low | simulation/controller.py:565 | TableSession lacks progressive_strategy (undocumented limitation) | Partially | Yes |
| L5 | Low | simulation/controller.py:552 | "fresh state" comment misleading for stateless strategies | Yes | Yes |
| L6 | Low | strategy/progressive.py:1-13 | Module docstring missing factory function mention | Yes | Yes |
