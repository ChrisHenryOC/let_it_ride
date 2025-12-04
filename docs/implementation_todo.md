# Let It Ride - Implementation Todo List

This document provides an ordered list of remaining issues to complete, sequenced according to their dependencies.

**Last Updated:** 2025-12-04

## Completed Issues

| LIR | Title | Status |
|-----|-------|--------|
| LIR-1 | Project Scaffolding and Development Environment | ✅ Complete |
| LIR-2 | Card and Deck Implementation | ✅ Complete |
| LIR-3 | Multi-Deck Shoe Implementation | ❌ Cancelled |
| LIR-4 | Five-Card Hand Evaluation | ✅ Complete |
| LIR-5 | Three-Card Hand Evaluation (Bonus Bet) | ✅ Complete |
| LIR-6 | Paytable Configuration System | ✅ Complete |
| LIR-7 | Hand Analysis Utilities | ✅ Complete |
| LIR-8 | YAML Configuration Schema and Loader | ✅ Complete |
| LIR-9 | Let It Ride Hand State Machine | ✅ Complete |
| LIR-10 | Basic Strategy Implementation | ✅ Complete |
| LIR-12 | Custom Strategy Configuration Parser | ✅ Complete |
| LIR-13 | Game Engine Orchestration | ✅ Complete |
| LIR-15 | Bankroll Tracker | ✅ Complete |
| LIR-16 | Flat Betting System | ✅ Complete |
| LIR-18 | Session State Management | ✅ Complete |
| LIR-19 | Session Result Data Structures | ✅ Complete |
| LIR-36 | Composition-Dependent Strategy | ❌ Cancelled |
| LIR-41 | Dealer Discard Mechanics | ✅ Complete |
| LIR-42 | Table Abstraction | ✅ Complete (PR #80) |

---

## Remaining Issues (Ordered by Execution Sequence)

### Phase 2: Game Logic (Remaining)

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 1 | LIR-11 | Baseline Strategies (Always Ride / Always Pull) | LIR-10 ✅ | High |
| 2 | LIR-14 | Bonus Betting Strategies | LIR-8 ✅ | High |

### Phase 3: Bankroll and Session (Remaining)

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 3 | LIR-17 | Progressive Betting Systems | LIR-16 ✅ | Medium |

### Phase 3.5: Multi-Player Foundation

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 4 | LIR-43 | Multi-Player Session Management | LIR-42 ✅, LIR-18 ✅ | High |
| 5 | LIR-45 | Table Integration Tests | LIR-42 ✅, LIR-43 | Medium |

### Phase 4: Simulation Infrastructure

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 6 | LIR-20 | Simulation Controller (Sequential) | LIR-18 ✅ | Critical |
| 7 | LIR-21 | Parallel Session Execution | LIR-20 | High |
| 8 | LIR-22 | Simulation Results Aggregation | LIR-19 ✅ | Critical |
| 9 | LIR-23 | Statistical Validation Module | LIR-22 | High |
| 10 | LIR-24 | RNG Quality and Seeding | LIR-1 ✅ | Medium |

### Phase 5: Analytics and Reporting

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 11 | LIR-25 | Core Statistics Calculator | LIR-22 | Critical |
| 12 | LIR-26 | Strategy Comparison Analytics | LIR-25 | High |
| 13 | LIR-27 | CSV Export | LIR-22 | Critical |
| 14 | LIR-28 | JSON Export | LIR-22 | High |
| 15 | LIR-29 | Visualization - Session Outcome Histogram | LIR-22 | Medium |
| 16 | LIR-30 | Visualization - Bankroll Trajectory | LIR-29 | Medium |
| 17 | LIR-44 | Chair Position Analytics | LIR-43, LIR-25 | Medium |

### Phase 6: CLI and Integration

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 18 | LIR-31 | CLI Entry Point | LIR-8 ✅, LIR-20 | Critical |
| 19 | LIR-32 | Console Output Formatting | LIR-31 | High |
| 20 | LIR-33 | Sample Configuration Files | LIR-8 ✅ | High |
| 21 | LIR-34 | End-to-End Integration Test | All previous | Critical |
| 22 | LIR-35 | Performance Optimization and Benchmarking | LIR-34 | Medium |

### Phase 7: Advanced Features and Tech Debt

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 23 | LIR-37 | Streak-Based Bonus Strategy | LIR-14 | Low |
| 24 | LIR-38 | Risk of Ruin Calculator | LIR-25 | Low |
| 25 | LIR-39 | HTML Report Generation | LIR-29, LIR-30 | Low |
| 26 | LIR-40 | Documentation and User Guide | All previous | Medium |
| 27 | LIR-46 | Extract Shared Hand Processing Logic | LIR-42 ✅ | Low |

---

## Recommended Execution Order

The following sequence respects dependencies and prioritizes critical path items:

```
1.  LIR-11  Baseline Strategies (Always Ride / Always Pull)
2.  LIR-14  Bonus Betting Strategies
3.  LIR-17  Progressive Betting Systems
4.  LIR-43  Multi-Player Session Management
5.  LIR-45  Table Integration Tests
    ─────── Phase 3.5 Complete (Multi-Player Foundation) ───────
6.  LIR-20  Simulation Controller (Sequential)
7.  LIR-22  Simulation Results Aggregation
8.  LIR-21  Parallel Session Execution
9.  LIR-24  RNG Quality and Seeding
10. LIR-23  Statistical Validation Module
    ─────── Phase 4 Complete (Simulation Infrastructure) ───────
11. LIR-25  Core Statistics Calculator
12. LIR-27  CSV Export
13. LIR-28  JSON Export
14. LIR-26  Strategy Comparison Analytics
15. LIR-29  Visualization - Session Outcome Histogram
16. LIR-30  Visualization - Bankroll Trajectory
17. LIR-44  Chair Position Analytics
    ─────── Phase 5 Complete (Analytics and Reporting) ───────
18. LIR-31  CLI Entry Point
19. LIR-33  Sample Configuration Files
20. LIR-32  Console Output Formatting
21. LIR-34  End-to-End Integration Test
22. LIR-35  Performance Optimization and Benchmarking
    ─────── Phase 6 Complete (CLI and Integration) ───────
23. LIR-37  Streak-Based Bonus Strategy
24. LIR-38  Risk of Ruin Calculator
25. LIR-39  HTML Report Generation
26. LIR-40  Documentation and User Guide
27. LIR-46  Extract Shared Hand Processing Logic (Tech Debt)
    ─────── Phase 7 Complete (Advanced Features) ───────
```

---

## Summary

| Category | Count |
|----------|-------|
| Completed | 19 |
| Cancelled | 2 |
| Remaining | 27 |
| **Total** | **48** |

**Recently Completed:**
- LIR-41: Dealer Discard Mechanics ✅
- LIR-42: Table Abstraction ✅ (PR #80)

**New Issues from Code Review (PR #80):**
- LIR-45: Table Integration Tests (GitHub #81)
- LIR-46: Extract Shared Hand Processing Logic (GitHub #82)

**Critical Path:** LIR-20 → LIR-22 → LIR-25 → LIR-31 → LIR-34

**Next Up:** LIR-43 (Multi-Player Session Management) depends on LIR-42 ✅
