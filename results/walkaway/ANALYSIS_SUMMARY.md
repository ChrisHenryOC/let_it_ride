# Walk-Away Strategy Analysis Summary

**Generated:** 2024-12-22 (Updated with Extended Testing)
**Simulations:** 100,000 sessions per configuration
**Base Config:** $500 starting bankroll, $5 base bet, 200 max hands, single-seat table

---

## Executive Summary

After testing **51 strategy configurations** across multiple dimensions, two strategies stand out:

### **Best Win Rate: Fibonacci Betting + No Bonus + $100/$100 Limits**

| Metric | Value |
|--------|-------|
| Win Rate | **36.00%** |
| Avg Session Profit | **-$6.04** |
| EV per Hand | **-$0.52** |
| Volatility (Std Dev) | **$270** |

### **Lowest Loss: No Bonus + Ultra-Tight $25/$25 Limits**

| Metric | Value |
|--------|-------|
| Win Rate | **34.55%** |
| Avg Session Profit | **-$1.44** |
| EV per Hand | **-$0.17** |
| Volatility (Std Dev) | **$86** |

---

## Complete Results by Category

### Category 1: Original Walk-Away Strategies

| Strategy | Win Limit | Loss Limit | Description |
|----------|-----------|------------|-------------|
| Tight | $100 | $100 | Symmetric, leave early |
| Protect | $150 | $100 | Cut losses, modest wins |
| Chase | $400 | $150 | Ride winning sessions |
| Loose | $500 | $400 | Stay longer, bigger swings |

**Session Win Rates:**

| Bonus | Tight ($100/$100) | Protect ($150/$100) | Chase ($400/$150) | Loose ($500/$400) |
|-------|-------------------|---------------------|-------------------|-------------------|
| $5 | 31.23% | 25.62% | 21.85% | 33.07% |
| $15 | 29.10% | 21.57% | 17.14% | 30.55% |
| $30 | 32.50% | 24.18% | 13.94% | 25.40% |

**Average Session Profit:**

| Bonus | Tight | Protect | Chase | Loose |
|-------|-------|---------|-------|-------|
| $5 | -$13.94 | -$16.59 | -$37.60 | -$72.14 |
| $15 | -$10.55 | -$13.06 | -$26.99 | -$75.10 |
| $30 | -$7.18 | -$9.09 | -$23.86 | -$62.73 |

### Category 2: Asymmetric Strategies (Tight Loss, Variable Win)

| Bonus | asym_2x ($200/$100) | asym_3x ($300/$100) | asym_4x ($400/$100) | asym_5x ($500/$100) |
|-------|---------|---------|---------|---------|
| $5 Win Rate | 21.26% | 16.80% | 15.77% | 15.56% |
| $5 Avg Profit | -$19.34 | -$24.43 | -$26.58 | -$28.24 |
| $15 Win Rate | 17.19% | 13.34% | 12.08% | 11.06% |
| $15 Avg Profit | -$15.32 | -$17.90 | -$19.09 | -$20.53 |
| $30 Win Rate | 19.25% | 13.22% | 10.30% | 8.68% |
| $30 Avg Profit | -$10.80 | -$13.89 | -$15.93 | -$17.53 |

### Category 3: Very Tight Limits

| Strategy | Win Rate | Avg Profit | Std Dev | EV/Hand |
|----------|----------|------------|---------|---------|
| bonus_5_verytight_50 | 29.86% | -$5.00 | $126 | -$0.37 |
| bonus_5_verytight_75 | 30.01% | -$9.22 | $168 | -$0.38 |
| bonus_15_verytight_50 | 32.86% | -$3.75 | $132 | -$0.82 |
| bonus_15_verytight_75 | 30.72% | -$6.64 | $168 | -$0.78 |
| bonus_30_verytight_50 | 29.33% | -$3.98 | $161 | -$1.60 |
| bonus_30_verytight_75 | 33.33% | -$5.63 | $203 | -$1.48 |

### Category 4: No Bonus Strategies

| Strategy | Win Rate | Avg Profit | Std Dev | EV/Hand |
|----------|----------|------------|---------|---------|
| no_bonus_verytight_50 | 33.89% | -$4.52 | $136 | -$0.17 |
| no_bonus_verytight_75 | 33.05% | -$9.19 | $183 | -$0.18 |
| no_bonus_tight_100 | 32.27% | -$14.90 | $210 | -$0.19 |

### Category 5: Ultra-Tight Limits (NEW)

| Strategy | Win Rate | Avg Profit | Std Dev | EV/Hand |
|----------|----------|------------|---------|---------|
| **no_bonus_ultratight_25** | **34.55%** | **-$1.44** | $86 | -$0.17 |
| no_bonus_ultratight_30 | 34.66% | -$2.05 | $91 | -$0.18 |

### Category 6: Shorter Sessions (NEW)

| Strategy | Max Hands | Win Rate | Avg Profit | EV/Hand |
|----------|-----------|----------|------------|---------|
| no_bonus_short_50hands | 50 | 34.21% | -$4.08 | -$0.17 |
| no_bonus_short_100hands | 100 | 33.88% | -$4.48 | -$0.17 |

### Category 7: Reverse Asymmetric (NEW)

Tight win limit, loose loss limit - opposite of "chase wins" strategy.

| Strategy | Limits | Win Rate | Avg Profit | EV/Hand |
|----------|--------|----------|------------|---------|
| no_bonus_reverse_asym_50_150 | $50/$150 | **53.58%** | -$14.57 | -$0.19 |
| no_bonus_reverse_asym_75_200 | $75/$200 | 46.49% | -$22.16 | -$0.19 |

### Category 8: Alternative Betting Systems (NEW)

| Strategy | System | Win Rate | Avg Profit | EV/Hand |
|----------|--------|----------|------------|---------|
| martingale_nobonus_tight | Martingale (2x after loss) | 35.50% | -$6.11 | -$0.66 |
| dalembert_nobonus_tight | D'Alembert (+1 after loss) | 35.41% | -$6.88 | -$0.69 |
| **fibonacci_nobonus_tight** | Fibonacci sequence | **36.00%** | -$6.04 | -$0.52 |

### Category 9: Paroli Betting System

| Strategy | Win Rate | Avg Profit | Std Dev | EV/Hand |
|----------|----------|------------|---------|---------|
| paroli_5_tight | 31.65% | -$11.35 | $208 | -$0.43 |
| paroli_15_tight | 28.84% | -$10.00 | $232 | -$0.86 |
| paroli_30_tight | 32.27% | -$7.41 | $235 | -$1.50 |

### Category 10: Different Base Bets (NEW)

| Strategy | Base Bet | Win Rate | Avg Profit | EV/Hand |
|----------|----------|----------|------------|---------|
| basebet_10_nobonus_tight | $10 | 33.89% | -$9.04 | -$0.34 |
| basebet_15_nobonus_tight | $15 | 34.42% | -$7.54 | -$0.50 |

### Category 11: Multi-Seat Tables (NEW)

| Strategy | Seats | Win Rate | Avg Profit | EV/Hand |
|----------|-------|----------|------------|---------|
| multiseat_6_nobonus_tight | 6 | 32.02% | -$15.42 | -$0.10 |

Note: 600,000 total sessions (100,000 table sessions x 6 seats).

### Category 12: Different Bankrolls (NEW)

| Strategy | Bankroll | Win Rate | Avg Profit | EV/Hand |
|----------|----------|----------|------------|---------|
| bankroll_300_nobonus_tight | $300 | 32.27% | -$14.90 | -$0.19 |
| bankroll_1000_nobonus_tight | $1000 | 32.27% | -$14.90 | -$0.19 |

**Finding: Bankroll size has NO effect on outcomes when limits remain constant.**

### Category 13: Dealer Burn Cards (NEW)

| Strategy | Burns | Win Rate | Avg Profit | EV/Hand |
|----------|-------|----------|------------|---------|
| dealer_burn_nobonus_tight | 1 | 32.31% | -$13.97 | -$0.17 |

**Finding: Dealer burn cards have NO significant effect on outcomes.**

---

## Top 15 Strategies Ranked by Win Rate

| Rank | Strategy | Limits | Win Rate | Avg Profit | EV/Hand |
|------|----------|--------|----------|------------|---------|
| 1 | **reverse_asym_50_150** | $50/$150 | **53.58%** | -$14.57 | -$0.19 |
| 2 | reverse_asym_75_200 | $75/$200 | 46.49% | -$22.16 | -$0.19 |
| 3 | **fibonacci_nobonus_tight** | $100/$100 | **36.00%** | -$6.04 | -$0.52 |
| 4 | martingale_nobonus_tight | $100/$100 | 35.50% | -$6.11 | -$0.66 |
| 5 | dalembert_nobonus_tight | $100/$100 | 35.41% | -$6.88 | -$0.69 |
| 6 | **no_bonus_ultratight_30** | $30/$30 | 34.66% | -$2.05 | -$0.18 |
| 7 | **no_bonus_ultratight_25** | $25/$25 | **34.55%** | **-$1.44** | -$0.17 |
| 8 | basebet_15_nobonus_tight | $100/$100 | 34.42% | -$7.54 | -$0.50 |
| 9 | no_bonus_short_50hands | $100/$100 | 34.21% | -$4.08 | -$0.17 |
| 10 | no_bonus_verytight_50 | $50/$50 | 33.89% | -$4.52 | -$0.17 |
| 11 | basebet_10_nobonus_tight | $100/$100 | 33.89% | -$9.04 | -$0.34 |
| 12 | no_bonus_short_100hands | $100/$100 | 33.88% | -$4.48 | -$0.17 |
| 13 | bonus_30_verytight_75 | $75/$75 | 33.33% | -$5.63 | -$1.48 |
| 14 | bonus_5_loose | $500/$400 | 33.07% | -$72.14 | -$0.41 |
| 15 | no_bonus_verytight_75 | $75/$75 | 33.05% | -$9.19 | -$0.18 |

---

## Top 10 Strategies Ranked by Lowest Average Loss

| Rank | Strategy | Limits | Avg Profit | Win Rate | EV/Hand |
|------|----------|--------|------------|----------|---------|
| 1 | **no_bonus_ultratight_25** | $25/$25 | **-$1.44** | 34.55% | -$0.17 |
| 2 | no_bonus_ultratight_30 | $30/$30 | -$2.05 | 34.66% | -$0.18 |
| 3 | bonus_15_verytight_50 | $50/$50 | -$3.75 | 32.86% | -$0.82 |
| 4 | bonus_30_verytight_50 | $50/$50 | -$3.98 | 29.33% | -$1.60 |
| 5 | no_bonus_short_50hands | $100/$100 | -$4.08 | 34.21% | -$0.17 |
| 6 | no_bonus_short_100hands | $100/$100 | -$4.48 | 33.88% | -$0.17 |
| 7 | no_bonus_verytight_50 | $50/$50 | -$4.52 | 33.89% | -$0.17 |
| 8 | bonus_5_verytight_50 | $50/$50 | -$5.00 | 29.86% | -$0.37 |
| 9 | bonus_30_verytight_75 | $75/$75 | -$5.63 | 33.33% | -$1.48 |
| 10 | fibonacci_nobonus_tight | $100/$100 | -$6.04 | 36.00% | -$0.52 |

---

## Key Findings

### 1. No Bonus Betting = Lowest House Edge

Removing bonus bets dramatically reduces EV loss per hand:

| Configuration | EV per Hand |
|---------------|-------------|
| No bonus | **-$0.17 to -$0.19** |
| $5 bonus | -$0.37 to -$0.43 |
| $15 bonus | -$0.78 to -$0.86 |
| $30 bonus | -$1.40 to -$1.60 |

**The bonus bet roughly doubles (or more) the house edge per hand.**

### 2. Ultra-Tight Limits = Minimal Losses

Average session profit by limit size (no bonus):

| Limit | Avg Profit | Win Rate |
|-------|------------|----------|
| $25/$25 | **-$1.44** | 34.55% |
| $30/$30 | -$2.05 | 34.66% |
| $50/$50 | -$4.52 | 33.89% |
| $75/$75 | -$9.19 | 33.05% |
| $100/$100 | -$14.90 | 32.27% |

**Tighter limits consistently reduce losses while maintaining similar win rates.**

### 3. Fibonacci Betting = Highest Win Rate (With Caveats)

| System | Win Rate | Avg Profit | EV/Hand |
|--------|----------|------------|---------|
| Fibonacci | **36.00%** | -$6.04 | -$0.52 |
| Martingale | 35.50% | -$6.11 | -$0.66 |
| D'Alembert | 35.41% | -$6.88 | -$0.69 |
| Flat | 32.27% | -$14.90 | -$0.19 |

Progressive betting systems increase win rate but also increase EV loss per hand due to larger average bet sizes.

### 4. Reverse Asymmetric = Highest Win Rate (But Costly)

| Strategy | Win Rate | Avg Profit |
|----------|----------|------------|
| $50/$150 (lock in small wins) | **53.58%** | -$14.57 |
| $75/$200 (lock in small wins) | 46.49% | -$22.16 |
| $100/$100 (baseline) | 32.27% | -$14.90 |

High win rates are achievable by accepting small wins and tolerating larger losses, but this increases average loss per session.

### 5. Asymmetric (Chase Wins) Underperforms

Counterintuitively, increasing the win target while keeping tight loss limits **decreases** both win rate AND average profit:

| Ratio | Win Rate (avg) | Why It Fails |
|-------|----------------|--------------|
| 1:1 (Tight) | ~31% | Baseline |
| 2:1 | ~19% | More exposure before hitting win target |
| 3:1 | ~14% | Even more exposure |
| 4:1 | ~12% | House edge grinds you down |
| 5:1 | ~11% | Rarely reach the win target |

### 6. Bankroll Size Has No Effect

With the same limits ($100/$100), bankroll size doesn't change outcomes:
- $300 bankroll: 32.27% win rate, -$14.90 avg
- $500 bankroll: 32.27% win rate, -$14.90 avg
- $1000 bankroll: 32.27% win rate, -$14.90 avg

### 7. Dealer Burn Cards Have No Effect

Burn cards (32.31% win rate) vs no burn (32.27% win rate) - difference is noise.

### 8. Multi-Seat Tables = Lower Per-Seat Win Rate

6-seat table: 32.02% per-seat win rate vs 32.27% single-seat

---

## Recommendations

### For Minimizing Losses: Ultra-Tight $25/$25, No Bonus
- **Win rate**: 34.55%
- **Average loss**: -$1.44/session
- **EV per hand**: -$0.17
- **Best for**: Maximum entertainment per dollar

### For Maximizing Win Rate: Fibonacci Betting, No Bonus, $100/$100
- **Win rate**: 36.00%
- **Average loss**: -$6.04/session
- **EV per hand**: -$0.52
- **Best for**: Highest probability of walking away up

### For "Winning Most Sessions": Reverse Asymmetric $50/$150, No Bonus
- **Win rate**: 53.58%
- **Average loss**: -$14.57/session
- **Best for**: Psychological satisfaction of winning more often

### If Playing Bonus: $30 Bonus, $75/$75 Limits
- **Win rate**: 33.33%
- **Average loss**: -$5.63/session
- **Best for**: Jackpot potential while limiting losses

### Avoid These Strategies:
1. **Asymmetric (chase wins)**: Lower win rates, higher losses
2. **Loose limits ($500/$400)**: High average losses despite good win rates
3. **Large bonus + wide limits**: Maximum house edge exposure

---

## Complete Config -> Results Mapping

### Original Strategies

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/with_bonus/bonus_5_tight.yaml` | `results/walkaway/bonus_5_tight/` | $5 bonus, $100/$100 |
| `configs/walkaway/with_bonus/bonus_5_protect.yaml` | `results/walkaway/bonus_5_protect/` | $5 bonus, $150/$100 |
| `configs/walkaway/with_bonus/bonus_5_chase.yaml` | `results/walkaway/bonus_5_chase/` | $5 bonus, $400/$150 |
| `configs/walkaway/with_bonus/bonus_5_loose.yaml` | `results/walkaway/bonus_5_loose/` | $5 bonus, $500/$400 |
| `configs/walkaway/with_bonus/bonus_15_tight.yaml` | `results/walkaway/bonus_15_tight/` | $15 bonus, $100/$100 |
| `configs/walkaway/with_bonus/bonus_15_protect.yaml` | `results/walkaway/bonus_15_protect/` | $15 bonus, $150/$100 |
| `configs/walkaway/with_bonus/bonus_15_chase.yaml` | `results/walkaway/bonus_15_chase/` | $15 bonus, $400/$150 |
| `configs/walkaway/with_bonus/bonus_15_loose.yaml` | `results/walkaway/bonus_15_loose/` | $15 bonus, $500/$400 |
| `configs/walkaway/with_bonus/bonus_30_tight.yaml` | `results/walkaway/bonus_30_tight/` | $30 bonus, $100/$100 |
| `configs/walkaway/with_bonus/bonus_30_protect.yaml` | `results/walkaway/bonus_30_protect/` | $30 bonus, $150/$100 |
| `configs/walkaway/with_bonus/bonus_30_chase.yaml` | `results/walkaway/bonus_30_chase/` | $30 bonus, $400/$150 |
| `configs/walkaway/with_bonus/bonus_30_loose.yaml` | `results/walkaway/bonus_30_loose/` | $30 bonus, $500/$400 |

### Asymmetric Strategies

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/with_bonus/bonus_5_asym_2x.yaml` | `results/walkaway/bonus_5_asym_2x/` | $5 bonus, $200/$100 |
| `configs/walkaway/with_bonus/bonus_5_asym_3x.yaml` | `results/walkaway/bonus_5_asym_3x/` | $5 bonus, $300/$100 |
| `configs/walkaway/with_bonus/bonus_5_asym_4x.yaml` | `results/walkaway/bonus_5_asym_4x/` | $5 bonus, $400/$100 |
| `configs/walkaway/with_bonus/bonus_5_asym_5x.yaml` | `results/walkaway/bonus_5_asym_5x/` | $5 bonus, $500/$100 |
| `configs/walkaway/with_bonus/bonus_15_asym_2x.yaml` | `results/walkaway/bonus_15_asym_2x/` | $15 bonus, $200/$100 |
| `configs/walkaway/with_bonus/bonus_15_asym_3x.yaml` | `results/walkaway/bonus_15_asym_3x/` | $15 bonus, $300/$100 |
| `configs/walkaway/with_bonus/bonus_15_asym_4x.yaml` | `results/walkaway/bonus_15_asym_4x/` | $15 bonus, $400/$100 |
| `configs/walkaway/with_bonus/bonus_15_asym_5x.yaml` | `results/walkaway/bonus_15_asym_5x/` | $15 bonus, $500/$100 |
| `configs/walkaway/with_bonus/bonus_30_asym_2x.yaml` | `results/walkaway/bonus_30_asym_2x/` | $30 bonus, $200/$100 |
| `configs/walkaway/with_bonus/bonus_30_asym_3x.yaml` | `results/walkaway/bonus_30_asym_3x/` | $30 bonus, $300/$100 |
| `configs/walkaway/with_bonus/bonus_30_asym_4x.yaml` | `results/walkaway/bonus_30_asym_4x/` | $30 bonus, $400/$100 |
| `configs/walkaway/with_bonus/bonus_30_asym_5x.yaml` | `results/walkaway/bonus_30_asym_5x/` | $30 bonus, $500/$100 |

### Very Tight Strategies

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/with_bonus/bonus_5_verytight_50.yaml` | `results/walkaway/bonus_5_verytight_50/` | $5 bonus, $50/$50 |
| `configs/walkaway/with_bonus/bonus_5_verytight_75.yaml` | `results/walkaway/bonus_5_verytight_75/` | $5 bonus, $75/$75 |
| `configs/walkaway/with_bonus/bonus_15_verytight_50.yaml` | `results/walkaway/bonus_15_verytight_50/` | $15 bonus, $50/$50 |
| `configs/walkaway/with_bonus/bonus_15_verytight_75.yaml` | `results/walkaway/bonus_15_verytight_75/` | $15 bonus, $75/$75 |
| `configs/walkaway/with_bonus/bonus_30_verytight_50.yaml` | `results/walkaway/bonus_30_verytight_50/` | $30 bonus, $50/$50 |
| `configs/walkaway/with_bonus/bonus_30_verytight_75.yaml` | `results/walkaway/bonus_30_verytight_75/` | $30 bonus, $75/$75 |

### No Bonus Strategies

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/no_bonus/no_bonus_verytight_50.yaml` | `results/walkaway/no_bonus_verytight_50/` | No bonus, $50/$50 |
| `configs/walkaway/no_bonus/no_bonus_verytight_75.yaml` | `results/walkaway/no_bonus_verytight_75/` | No bonus, $75/$75 |
| `configs/walkaway/no_bonus/no_bonus_tight_100.yaml` | `results/walkaway/no_bonus_tight_100/` | No bonus, $100/$100 |

### Ultra-Tight Strategies (NEW)

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/no_bonus/no_bonus_ultratight_25.yaml` | `results/walkaway/no_bonus_ultratight_25/` | No bonus, $25/$25 |
| `configs/walkaway/no_bonus/no_bonus_ultratight_30.yaml` | `results/walkaway/no_bonus_ultratight_30/` | No bonus, $30/$30 |

### Shorter Sessions (NEW)

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/no_bonus/no_bonus_short_50hands.yaml` | `results/walkaway/no_bonus_short_50hands/` | No bonus, 50 max hands |
| `configs/walkaway/no_bonus/no_bonus_short_100hands.yaml` | `results/walkaway/no_bonus_short_100hands/` | No bonus, 100 max hands |

### Reverse Asymmetric (NEW)

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/no_bonus/no_bonus_reverse_asym_50_150.yaml` | `results/walkaway/no_bonus_reverse_asym_50_150/` | No bonus, $50 win/$150 loss |
| `configs/walkaway/no_bonus/no_bonus_reverse_asym_75_200.yaml` | `results/walkaway/no_bonus_reverse_asym_75_200/` | No bonus, $75 win/$200 loss |

### Alternative Betting Systems (NEW)

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/betting_systems/martingale_nobonus_tight.yaml` | `results/walkaway/martingale_nobonus_tight/` | Martingale, no bonus, $100/$100 |
| `configs/walkaway/betting_systems/dalembert_nobonus_tight.yaml` | `results/walkaway/dalembert_nobonus_tight/` | D'Alembert, no bonus, $100/$100 |
| `configs/walkaway/betting_systems/fibonacci_nobonus_tight.yaml` | `results/walkaway/fibonacci_nobonus_tight/` | Fibonacci, no bonus, $100/$100 |

### Paroli Betting Strategies

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/with_bonus/paroli_5_tight.yaml` | `results/walkaway/paroli_5_tight/` | $5 bonus, Paroli, $100/$100 |
| `configs/walkaway/with_bonus/paroli_15_tight.yaml` | `results/walkaway/paroli_15_tight/` | $15 bonus, Paroli, $100/$100 |
| `configs/walkaway/with_bonus/paroli_30_tight.yaml` | `results/walkaway/paroli_30_tight/` | $30 bonus, Paroli, $100/$100 |

### Different Base Bets (NEW)

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/no_bonus/basebet_10_nobonus_tight.yaml` | `results/walkaway/basebet_10_nobonus_tight/` | $10 base bet, no bonus, $100/$100 |
| `configs/walkaway/no_bonus/basebet_15_nobonus_tight.yaml` | `results/walkaway/basebet_15_nobonus_tight/` | $15 base bet, no bonus, $100/$100 |

### Multi-Seat Tables (NEW)

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/no_bonus/multiseat_6_nobonus_tight.yaml` | `results/walkaway/multiseat_6_nobonus_tight/` | 6 seats, no bonus, $100/$100 |

### Different Bankrolls (NEW)

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/no_bonus/bankroll_300_nobonus_tight.yaml` | `results/walkaway/bankroll_300_nobonus_tight/` | $300 bankroll, no bonus, $100/$100 |
| `configs/walkaway/no_bonus/bankroll_1000_nobonus_tight.yaml` | `results/walkaway/bankroll_1000_nobonus_tight/` | $1000 bankroll, no bonus, $100/$100 |

### Dealer Burn Cards (NEW)

| Config File | Results Directory | Description |
|-------------|-------------------|-------------|
| `configs/walkaway/no_bonus/dealer_burn_nobonus_tight.yaml` | `results/walkaway/dealer_burn_nobonus_tight/` | 1 burn card, no bonus, $100/$100 |

---

## Methodology Notes

- All simulations used 100,000 sessions for statistical significance
- Same random seed (42) for reproducibility
- Single-seat table configuration (except multi-seat test)
- Basic strategy for bet decisions
- Fisher-Yates shuffle algorithm
- $500 starting bankroll (except bankroll variation tests)
- $5 base bet (except base bet variation tests)
- 200 max hands per session (except shorter session tests)
