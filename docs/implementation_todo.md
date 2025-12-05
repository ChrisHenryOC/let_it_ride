# Let It Ride - Implementation Todo List

This document provides an ordered list of remaining issues to complete, sequenced according to their dependencies.

**Last Updated:** 2025-12-05

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
| LIR-11 | Baseline Strategies (Always Ride / Always Pull) | ✅ Complete |
| LIR-12 | Custom Strategy Configuration Parser | ✅ Complete |
| LIR-13 | Game Engine Orchestration | ✅ Complete |
| LIR-14 | Bonus Betting Strategies | ✅ Complete |
| LIR-15 | Bankroll Tracker | ✅ Complete |
| LIR-16 | Flat Betting System | ✅ Complete |
| LIR-17 | Progressive Betting Systems | ✅ Complete |
| LIR-18 | Session State Management | ✅ Complete |
| LIR-19 | Session Result Data Structures | ✅ Complete |
| LIR-36 | Composition-Dependent Strategy | ❌ Cancelled |
| LIR-41 | Dealer Discard Mechanics | ✅ Complete |
| LIR-42 | Table Abstraction | ✅ Complete |
| LIR-43 | Multi-Player Session Management | ✅ Complete (PR #88) |
| LIR-46 | Extract Shared Hand Processing Logic | ✅ Complete (PR #85) |

---

## Remaining Issues (Ordered by Execution Sequence)

### Phase 3.5: Multi-Player Foundation

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 1 | LIR-45 | Table Integration Tests | LIR-42 ✅, LIR-43 ✅ | Medium |

### Phase 4: Simulation Infrastructure

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 2 | LIR-20 | Simulation Controller (Sequential) | LIR-18 ✅ | Critical |
| 3 | LIR-21 | Parallel Session Execution | LIR-20 | High |
| 4 | LIR-22 | Simulation Results Aggregation | LIR-19 ✅ | Critical |
| 5 | LIR-23 | Statistical Validation Module | LIR-22 | High |
| 6 | LIR-24 | RNG Quality and Seeding | LIR-1 ✅ | Medium |

### Phase 5: Analytics and Reporting

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 7 | LIR-25 | Core Statistics Calculator | LIR-22 | Critical |
| 8 | LIR-26 | Strategy Comparison Analytics | LIR-25 | High |
| 9 | LIR-27 | CSV Export | LIR-22 | Critical |
| 10 | LIR-28 | JSON Export | LIR-22 | High |
| 11 | LIR-29 | Visualization - Session Outcome Histogram | LIR-22 | Medium |
| 12 | LIR-30 | Visualization - Bankroll Trajectory | LIR-29 | Medium |
| 13 | LIR-44 | Chair Position Analytics | LIR-43 ✅, LIR-25 | Medium |

### Phase 6: CLI and Integration

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 14 | LIR-31 | CLI Entry Point | LIR-8 ✅, LIR-20 | Critical |
| 15 | LIR-32 | Console Output Formatting | LIR-31 | High |
| 16 | LIR-33 | Sample Configuration Files | LIR-8 ✅ | High |
| 17 | LIR-34 | End-to-End Integration Test | All previous | Critical |
| 18 | LIR-35 | Performance Optimization and Benchmarking | LIR-34 | Medium |

### Phase 7: Advanced Features

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 19 | LIR-37 | Streak-Based Bonus Strategy | LIR-14 ✅ | Low |
| 20 | LIR-38 | Risk of Ruin Calculator | LIR-25 | Low |
| 21 | LIR-39 | HTML Report Generation | LIR-29, LIR-30 | Low |
| 22 | LIR-40 | Documentation and User Guide | All previous | Medium |
| 23 | LIR-47 | Session API Consistency and DRY Refactoring | None | Low |
| 24 | LIR-48 | TableSession Performance Optimization | LIR-35 | Low |

---

## Recommended Execution Order

The following sequence respects dependencies and prioritizes critical path items:

```
1.  LIR-45  Table Integration Tests
    ─────── Phase 3.5 Complete (Multi-Player Foundation) ───────
2.  LIR-20  Simulation Controller (Sequential)
3.  LIR-22  Simulation Results Aggregation
4.  LIR-21  Parallel Session Execution
5.  LIR-24  RNG Quality and Seeding
6.  LIR-23  Statistical Validation Module
    ─────── Phase 4 Complete (Simulation Infrastructure) ───────
7.  LIR-25  Core Statistics Calculator
8.  LIR-27  CSV Export
9.  LIR-28  JSON Export
10. LIR-26  Strategy Comparison Analytics
11. LIR-29  Visualization - Session Outcome Histogram
12. LIR-30  Visualization - Bankroll Trajectory
13. LIR-44  Chair Position Analytics
    ─────── Phase 5 Complete (Analytics and Reporting) ───────
14. LIR-31  CLI Entry Point
15. LIR-33  Sample Configuration Files
16. LIR-32  Console Output Formatting
17. LIR-34  End-to-End Integration Test
18. LIR-35  Performance Optimization and Benchmarking
    ─────── Phase 6 Complete (CLI and Integration) ───────
19. LIR-37  Streak-Based Bonus Strategy
20. LIR-38  Risk of Ruin Calculator
21. LIR-39  HTML Report Generation
22. LIR-47  Session API Consistency and DRY Refactoring (anytime)
23. LIR-48  TableSession Performance Optimization (after LIR-35 profiling)
24. LIR-40  Documentation and User Guide
    ─────── Phase 7 Complete (Advanced Features) ───────
```

---

## Summary

| Category | Count |
|----------|-------|
| Completed | 24 |
| Cancelled | 2 |
| Remaining | 24 |
| **Total** | **50** |

**Recently Completed:**
- LIR-42: Table Abstraction ✅
- LIR-43: Multi-Player Session Management ✅ (PR #88)
- LIR-46: Extract Shared Hand Processing Logic ✅ (PR #85)

**New Issues (from PR #88 review):**
- LIR-47: Session API Consistency and DRY Refactoring (GitHub #89)
- LIR-48: TableSession Performance Optimization (GitHub #90)

**Critical Path:** LIR-20 → LIR-22 → LIR-25 → LIR-31 → LIR-34

**Next Up:** LIR-45 (Table Integration Tests) - all dependencies complete
