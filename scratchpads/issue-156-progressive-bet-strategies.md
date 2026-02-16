# Issue #156 — LIR-63: Progressive Bet Strategies

## Overview
Implement strategy classes that determine when a player places the optional progressive jackpot side bet.

## Files Changed
- `src/let_it_ride/strategy/progressive.py` — New module with ProgressiveContext, ProgressiveStrategy protocol, and 4 implementations
- `src/let_it_ride/config/models.py` — Added ProgressiveStrategyConfig, JackpotThresholdConfig, BankrollConditionalProgressiveConfig; added progressive_strategy to FullConfig
- `src/let_it_ride/core/progressive_jackpot.py` — Added `seed_amount` public property
- `src/let_it_ride/simulation/session.py` — Added progressive_strategy parameter; uses strategy to decide progressive bet dynamically
- `src/let_it_ride/simulation/controller.py` — Added progressive_strategy_factory; passes to Session creation
- `src/let_it_ride/strategy/__init__.py` — Added progressive strategy exports
- `tests/unit/strategy/test_progressive.py` — 40 unit tests

## Strategy Implementations
1. NeverProgressiveStrategy — Never bets
2. AlwaysProgressiveStrategy — Always bets the configured amount
3. JackpotThresholdStrategy — Only bets when jackpot >= min_jackpot
4. BankrollConditionalProgressiveStrategy — Bets when profit/bankroll conditions met

## YAML Config
```yaml
progressive_strategy:
  type: jackpot_threshold  # never | always | jackpot_threshold | bankroll_conditional
  jackpot_threshold:
    min_jackpot: 25000.0
  bankroll_conditional:
    min_session_profit: 50.0
    min_bankroll_ratio: 1.1
```
