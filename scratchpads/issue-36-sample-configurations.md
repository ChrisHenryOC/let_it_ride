# Issue #36: LIR-33 Sample Configuration Files

GitHub Issue: https://github.com/chrishenry/let_it_ride/issues/36

## Overview

Create comprehensive sample configuration files demonstrating all features of the Let It Ride Strategy Simulator.

## Files to Create

1. `configs/README.md` - Documentation explaining each config file
2. `configs/basic_strategy.yaml` - Basic strategy with flat betting baseline
3. `configs/conservative.yaml` - Conservative strategy, low risk
4. `configs/aggressive.yaml` - Aggressive strategy, high variance
5. `configs/bonus_comparison.yaml` - Comparing bonus betting strategies
6. `configs/progressive_betting.yaml` - Martingale and Paroli examples

## Implementation Plan

### 1. configs/README.md
- Overview of the configs directory
- Brief description of each config file
- Links to documentation
- Quick start instructions

### 2. basic_strategy.yaml
- Uses mathematically optimal basic strategy
- Flat betting system
- Standard paytable
- No bonus betting
- Good baseline for comparisons
- 100k sessions, 200 hands/session

### 3. conservative.yaml
- Conservative strategy (only ride on strong hands)
- Flat betting
- Tight stop conditions
- Lower risk profile
- Demonstrates conservative settings

### 4. aggressive.yaml
- Aggressive strategy (ride on draws)
- Higher volatility settings
- Wider stop conditions
- Demonstrates high-variance play

### 5. bonus_comparison.yaml
- Enables bonus betting
- Demonstrates bankroll_conditional bonus strategy
- Scaling tiers based on session profit
- Uses paytable_b for bonus

### 6. progressive_betting.yaml
- Multiple betting system configurations
- Demonstrates Martingale and Paroli
- Shows D'Alembert configuration
- Fibonacci betting example

## Testing Requirements

- Create tests that validate all config files load correctly
- Verify configs conform to schema
- Test that configs run without errors in simulation

## Key Observations

- Existing `sample_config.yaml` shows commented examples
- Need to create focused configs that highlight specific features
- Each config should be fully documented with comments
- Use realistic parameters for actual use
