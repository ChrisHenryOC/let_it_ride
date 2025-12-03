# Let It Ride - Implementation Todo List

This document provides an ordered list of remaining issues to complete, sequenced according to their dependencies.

**Last Updated:** 2025-12-03

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

---

## Remaining Issues (Ordered by Execution Sequence)

### Phase 2: Game Logic (Remaining)

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 1 | LIR-11 | Baseline Strategies (Always Ride / Always Pull) | LIR-10 ✅ | High |
| 2 | LIR-14 | Bonus Betting Strategies | LIR-8 ✅ | High |
| 3 | LIR-41 | Dealer Discard Mechanics | LIR-13 ✅ | Medium |

### Phase 3: Bankroll and Session (Remaining)

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 4 | LIR-17 | Progressive Betting Systems | LIR-16 ✅ | Medium |

### Phase 3.5: Multi-Player Foundation (NEW - BLOCKING)

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 5 | LIR-42 | Table Abstraction | LIR-13 ✅, LIR-41 | High |
| 6 | LIR-43 | Multi-Player Session Management | LIR-42, LIR-18 ✅ | High |

### Phase 4: Simulation Infrastructure

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 7 | LIR-20 | Simulation Controller (Sequential) | LIR-18 ✅ | Critical |
| 8 | LIR-21 | Parallel Session Execution | LIR-20 | High |
| 9 | LIR-22 | Simulation Results Aggregation | LIR-19 ✅ | Critical |
| 10 | LIR-23 | Statistical Validation Module | LIR-22 | High |
| 11 | LIR-24 | RNG Quality and Seeding | LIR-1 ✅ | Medium |

### Phase 5: Analytics and Reporting

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 12 | LIR-25 | Core Statistics Calculator | LIR-22 | Critical |
| 13 | LIR-26 | Strategy Comparison Analytics | LIR-25 | High |
| 14 | LIR-27 | CSV Export | LIR-22 | Critical |
| 15 | LIR-28 | JSON Export | LIR-22 | High |
| 16 | LIR-29 | Visualization - Session Outcome Histogram | LIR-22 | Medium |
| 17 | LIR-30 | Visualization - Bankroll Trajectory | LIR-29 | Medium |
| 18 | LIR-44 | Chair Position Analytics | LIR-43, LIR-25 | Medium |

### Phase 6: CLI and Integration

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 19 | LIR-31 | CLI Entry Point | LIR-8 ✅, LIR-20 | Critical |
| 20 | LIR-32 | Console Output Formatting | LIR-31 | High |
| 21 | LIR-33 | Sample Configuration Files | LIR-8 ✅ | High |
| 22 | LIR-34 | End-to-End Integration Test | All previous | Critical |
| 23 | LIR-35 | Performance Optimization and Benchmarking | LIR-34 | Medium |

### Phase 7: Advanced Features

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 24 | LIR-37 | Streak-Based Bonus Strategy | LIR-14 | Low |
| 25 | LIR-38 | Risk of Ruin Calculator | LIR-25 | Low |
| 26 | LIR-39 | HTML Report Generation | LIR-29, LIR-30 | Low |
| 27 | LIR-40 | Documentation and User Guide | All previous | Medium |

---

## Recommended Execution Order

The following sequence respects dependencies and prioritizes critical path items:

```
1.  LIR-11  Baseline Strategies (Always Ride / Always Pull)
2.  LIR-14  Bonus Betting Strategies
3.  LIR-41  Dealer Discard Mechanics (NEW)
4.  LIR-17  Progressive Betting Systems
5.  LIR-42  Table Abstraction (NEW - BLOCKING)
6.  LIR-43  Multi-Player Session Management (NEW)
    ─────── Phase 3.5 Complete (Multi-Player Foundation) ───────
7.  LIR-20  Simulation Controller (Sequential)
8.  LIR-22  Simulation Results Aggregation
9.  LIR-21  Parallel Session Execution
10. LIR-24  RNG Quality and Seeding
11. LIR-23  Statistical Validation Module
    ─────── Phase 4 Complete (Simulation Infrastructure) ───────
12. LIR-25  Core Statistics Calculator
13. LIR-27  CSV Export
14. LIR-28  JSON Export
15. LIR-26  Strategy Comparison Analytics
16. LIR-29  Visualization - Session Outcome Histogram
17. LIR-30  Visualization - Bankroll Trajectory
18. LIR-44  Chair Position Analytics (NEW)
    ─────── Phase 5 Complete (Analytics and Reporting) ───────
19. LIR-31  CLI Entry Point
20. LIR-33  Sample Configuration Files
21. LIR-32  Console Output Formatting
22. LIR-34  End-to-End Integration Test
23. LIR-35  Performance Optimization and Benchmarking
    ─────── Phase 6 Complete (CLI and Integration) ───────
24. LIR-37  Streak-Based Bonus Strategy
25. LIR-38  Risk of Ruin Calculator
26. LIR-39  HTML Report Generation
27. LIR-40  Documentation and User Guide
    ─────── Phase 7 Complete (Advanced Features) ───────
```

---

## Summary

| Category | Count |
|----------|-------|
| Completed | 15 |
| Cancelled | 2 |
| Remaining | 27 |
| **Total** | **44** |

**New Issues from POC Findings:**
- LIR-41: Dealer Discard Mechanics
- LIR-42: Table Abstraction
- LIR-43: Multi-Player Session Management
- LIR-44: Chair Position Analytics

**Critical Path:** LIR-20 → LIR-22 → LIR-25 → LIR-31 → LIR-34

**Blocking Dependency:** Phase 3.5 (LIR-42, LIR-43) must be completed before Phase 4 begins.
