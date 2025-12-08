# Issue 26: LIR-23 Statistical Validation Module

**GitHub Issue:** https://github.com/anthropics/let_it_ride/issues/26

## Overview

Implement statistical validation that simulation results match theoretical probabilities.

## Key Components

### 1. Theoretical Probabilities (5-card poker hands)
From combinatorics, exact probabilities for 5-card poker hands:
- Royal Flush: 0.00000154
- Straight Flush: 0.0000139
- Four of a Kind: 0.000240
- Full House: 0.00144
- Flush: 0.00197
- Straight: 0.00392
- Three of a Kind: 0.0211
- Two Pair: 0.0475
- Pair: 0.423 (all pairs combined)
- High Card: 0.501

**Note:** The simulator distinguishes `pair_tens_or_better` and `pair_below_tens`, so we'll need to combine these for the chi-square test against theoretical "any pair" probability.

### 2. Chi-Square Goodness of Fit Test
- Compare observed hand frequencies vs theoretical
- Calculate chi-square statistic: Σ((O-E)²/E)
- p-value from chi-square distribution
- Degrees of freedom = number of hand types - 1

### 3. EV Convergence Testing
- Theoretical house edge for Let It Ride: ~3.5% (main game)
- Compare actual EV per hand vs theoretical
- Calculate deviation percentage

### 4. Confidence Intervals
- Wilson score interval for session win rate (binomial proportion)
- Use scipy.stats for statistical calculations

## Implementation Plan

1. Create `/src/let_it_ride/analytics/validation.py`:
   - THEORETICAL_HAND_PROBS constant
   - ChiSquareResult dataclass
   - ValidationReport dataclass
   - Helper functions for chi-square calculation
   - validate_simulation() main function

2. Create `/tests/unit/analytics/test_validation.py`:
   - Test with known distributions
   - Test edge cases
   - Test warning thresholds

## Dependencies
- scipy.stats for chi-square calculations
- AggregateStatistics from simulation.aggregation

## Files to Create
- `src/let_it_ride/analytics/validation.py`
- `tests/unit/analytics/test_validation.py`
