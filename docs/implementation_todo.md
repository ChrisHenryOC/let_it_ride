# Let It Ride - Implementation Todo List

This document provides an ordered list of remaining issues to complete, sequenced according to their dependencies.

**Last Updated:** 2025-12-13 (Synced with GitHub issue statuses)

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
| LIR-20 | Simulation Controller (Sequential) | ✅ Complete (PR #96) |
| LIR-21 | Parallel Session Execution | ✅ Complete (PR #107) |
| LIR-22 | Simulation Results Aggregation | ✅ Complete (PR #111) |
| LIR-23 | Statistical Validation Module | ✅ Complete (PR #112) |
| LIR-24 | RNG Quality and Seeding | ✅ Complete (PR #115) |
| LIR-25 | Core Statistics Calculator | ✅ Complete (PR #113) |
| LIR-26 | Strategy Comparison Analytics | ✅ Complete |
| LIR-27 | CSV Export | ✅ Complete |
| LIR-28 | JSON Export | ✅ Complete |
| LIR-29 | Visualization - Session Outcome Histogram | ✅ Complete |
| LIR-30 | Visualization - Bankroll Trajectory | ✅ Complete |
| LIR-31 | CLI Entry Point | ✅ Complete |
| LIR-32 | Console Output Formatting | ✅ Complete |
| LIR-33 | Sample Configuration Files | ✅ Complete |
| LIR-34 | End-to-End Integration Test | ✅ Complete (PR #129) |
| LIR-36 | Composition-Dependent Strategy | ❌ Cancelled |
| LIR-41 | Dealer Discard Mechanics | ✅ Complete |
| LIR-42 | Table Abstraction | ✅ Complete |
| LIR-43 | Multi-Player Session Management | ✅ Complete (PR #88) |
| LIR-44 | Chair Position Analytics | ✅ Complete (PR #114) |
| LIR-45 | Table Integration Tests | ✅ Complete (PR #92) |
| LIR-46 | Extract Shared Hand Processing Logic | ✅ Complete (PR #85) |
| LIR-50 | Refactor Factory Functions to Registry Pattern | ✅ Complete (PR #102) |
| LIR-51 | Unit Tests for Controller Factory Functions | ✅ Complete (PR #103) |
| LIR-52 | Error Handling and Edge Case Tests | ✅ Complete (PR #104) |
| LIR-53 | Test Quality Improvements for SimulationController | ✅ Complete (PR #105) |
| LIR-54 | Enhanced RNG Isolation Verification with Hand-Level Testing | ✅ Complete (PR #117) |

---

## Remaining Issues (Ordered by Execution Sequence)

### Phase 7: Advanced Features and Polish

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 1 | LIR-35 | Performance Optimization and Benchmarking | LIR-34 ✅ | Medium |
| 2 | LIR-37 | Streak-Based Bonus Strategy | LIR-14 ✅ | Low |
| 3 | LIR-38 | Risk of Ruin Calculator | LIR-25 ✅ | Low |
| 4 | LIR-39 | HTML Report Generation | LIR-29 ✅, LIR-30 ✅ | Low |
| 5 | LIR-40 | Documentation and User Guide | All previous | Medium |
| 6 | LIR-47 | Session API Consistency and DRY Refactoring | None | Low |
| 7 | LIR-48 | TableSession Performance Optimization | LIR-35 | Low |
| 8 | LIR-49 | Table Integration Test Coverage Improvements | LIR-45 ✅ | Low |
| 9 | LIR-55 | Property-Based Testing with Hypothesis | None | Low |

---

## Recommended Execution Order

The following sequence respects dependencies and prioritizes critical path items:

```
    ─────── Phase 5 Complete (Analytics and Reporting) ───────
    LIR-27  CSV Export ✅
    LIR-28  JSON Export ✅
    LIR-26  Strategy Comparison Analytics ✅
    LIR-29  Visualization - Session Outcome Histogram ✅
    LIR-30  Visualization - Bankroll Trajectory ✅
    ─────── Phase 6 Complete (CLI and Integration) ───────
    LIR-31  CLI Entry Point ✅
    LIR-33  Sample Configuration Files ✅
    LIR-32  Console Output Formatting ✅
    LIR-34  End-to-End Integration Test ✅ (PR #129)
    ─────────────────────────────────────────────────────────────
1.  LIR-35  Performance Optimization and Benchmarking
2.  LIR-37  Streak-Based Bonus Strategy
3.  LIR-38  Risk of Ruin Calculator
4.  LIR-39  HTML Report Generation
5.  LIR-47  Session API Consistency and DRY Refactoring (anytime)
6.  LIR-48  TableSession Performance Optimization (after LIR-35 profiling)
7.  LIR-49  Table Integration Test Coverage Improvements
8.  LIR-55  Property-Based Testing with Hypothesis (anytime)
9.  LIR-40  Documentation and User Guide
    ─────── Phase 7 Complete (Advanced Features) ───────
```

---

## Summary

| Category | Count |
|----------|-------|
| Completed | 45 |
| Cancelled | 2 |
| Remaining | 9 |
| **Total** | **56** |

**Recently Completed:**
- LIR-34: End-to-End Integration Test ✅ (PR #129)
- LIR-32: Console Output Formatting ✅
- LIR-33: Sample Configuration Files ✅
- LIR-31: CLI Entry Point ✅
- LIR-30: Visualization - Bankroll Trajectory ✅
- LIR-29: Visualization - Session Outcome Histogram ✅

**Open Issues (from PR reviews):**
- LIR-47: Session API Consistency and DRY Refactoring (GitHub #89)
- LIR-48: TableSession Performance Optimization (GitHub #90)
- LIR-49: Table Integration Test Coverage Improvements (GitHub #93)
- LIR-55: Property-Based Testing with Hypothesis (GitHub #116)

**Next Up:**
- LIR-35 (Performance Optimization) - all dependencies complete
- LIR-40 (Documentation) - can be started anytime

**Project Status:** Core functionality complete (Phases 1-6). Only advanced features and polish remaining.
