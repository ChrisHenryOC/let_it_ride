# Let It Ride - Implementation Todo List

This document provides an ordered list of remaining issues to complete, sequenced according to their dependencies.

**Last Updated:** 2025-12-07 (Synced with GitHub issue statuses - PR #105 review complete)

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
| LIR-36 | Composition-Dependent Strategy | ❌ Cancelled |
| LIR-41 | Dealer Discard Mechanics | ✅ Complete |
| LIR-42 | Table Abstraction | ✅ Complete |
| LIR-43 | Multi-Player Session Management | ✅ Complete (PR #88) |
| LIR-45 | Table Integration Tests | ✅ Complete (PR #92) |
| LIR-46 | Extract Shared Hand Processing Logic | ✅ Complete (PR #85) |
| LIR-50 | Refactor Factory Functions to Registry Pattern | ✅ Complete (PR #102) |
| LIR-51 | Unit Tests for Controller Factory Functions | ✅ Complete (PR #103) |

---

## Remaining Issues (Ordered by Execution Sequence)

### Phase 4: Simulation Infrastructure

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 1 | LIR-52 | Error Handling and Edge Case Tests | LIR-20 ✅, LIR-51 ✅ | High |
| 2 | LIR-53 | Test Quality Improvements for SimulationController | LIR-20 ✅ | Medium |
| 3 | LIR-21 | Parallel Session Execution | LIR-20 ✅ | High |
| 4 | LIR-22 | Simulation Results Aggregation | LIR-19 ✅ | Critical |
| 5 | LIR-23 | Statistical Validation Module | LIR-22 | High |
| 6 | LIR-24 | RNG Quality and Seeding | LIR-1 ✅ | Medium |
| 7 | LIR-54 | Enhanced RNG Isolation Verification with Hand-Level Testing | LIR-53 | Medium |

### Phase 5: Analytics and Reporting

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 8 | LIR-25 | Core Statistics Calculator | LIR-22 | Critical |
| 9 | LIR-26 | Strategy Comparison Analytics | LIR-25 | High |
| 10 | LIR-27 | CSV Export | LIR-22 | Critical |
| 11 | LIR-28 | JSON Export | LIR-22 | High |
| 12 | LIR-29 | Visualization - Session Outcome Histogram | LIR-22 | Medium |
| 13 | LIR-30 | Visualization - Bankroll Trajectory | LIR-29 | Medium |
| 14 | LIR-44 | Chair Position Analytics | LIR-43 ✅, LIR-25 | Medium |

### Phase 6: CLI and Integration

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 15 | LIR-31 | CLI Entry Point | LIR-8 ✅, LIR-20 ✅ | Critical |
| 16 | LIR-32 | Console Output Formatting | LIR-31 | High |
| 17 | LIR-33 | Sample Configuration Files | LIR-8 ✅ | High |
| 18 | LIR-34 | End-to-End Integration Test | All previous | Critical |
| 19 | LIR-35 | Performance Optimization and Benchmarking | LIR-34 | Medium |

### Phase 7: Advanced Features

| # | LIR | Title | Dependencies | Priority |
|---|-----|-------|--------------|----------|
| 20 | LIR-37 | Streak-Based Bonus Strategy | LIR-14 ✅ | Low |
| 21 | LIR-38 | Risk of Ruin Calculator | LIR-25 | Low |
| 22 | LIR-39 | HTML Report Generation | LIR-29, LIR-30 | Low |
| 23 | LIR-40 | Documentation and User Guide | All previous | Medium |
| 24 | LIR-47 | Session API Consistency and DRY Refactoring | None | Low |
| 25 | LIR-48 | TableSession Performance Optimization | LIR-35 | Low |
| 26 | LIR-49 | Table Integration Test Coverage Improvements | LIR-45 ✅ | Low |

---

## Recommended Execution Order

The following sequence respects dependencies and prioritizes critical path items:

```
    ─────── Phase 3.5 Complete (Multi-Player Foundation) ───────
    LIR-51  Unit Tests for Controller Factory Functions ✅ (PR #103)
    ─────────────────────────────────────────────────────────────
1.  LIR-52  Error Handling and Edge Case Tests (PR #104 in review)
2.  LIR-53  Test Quality Improvements for SimulationController (PR #105 in review)
3.  LIR-22  Simulation Results Aggregation
4.  LIR-21  Parallel Session Execution
5.  LIR-24  RNG Quality and Seeding
6.  LIR-54  Enhanced RNG Isolation Verification (depends on LIR-53)
7.  LIR-23  Statistical Validation Module
    ─────── Phase 4 Complete (Simulation Infrastructure) ───────
8.  LIR-25  Core Statistics Calculator
9.  LIR-27  CSV Export
10. LIR-28  JSON Export
11. LIR-26  Strategy Comparison Analytics
12. LIR-29  Visualization - Session Outcome Histogram
13. LIR-30  Visualization - Bankroll Trajectory
14. LIR-44  Chair Position Analytics
    ─────── Phase 5 Complete (Analytics and Reporting) ───────
15. LIR-31  CLI Entry Point
16. LIR-33  Sample Configuration Files
17. LIR-32  Console Output Formatting
18. LIR-34  End-to-End Integration Test
19. LIR-35  Performance Optimization and Benchmarking
    ─────── Phase 6 Complete (CLI and Integration) ───────
20. LIR-37  Streak-Based Bonus Strategy
21. LIR-38  Risk of Ruin Calculator
22. LIR-39  HTML Report Generation
23. LIR-47  Session API Consistency and DRY Refactoring (anytime)
24. LIR-48  TableSession Performance Optimization (after LIR-35 profiling)
25. LIR-49  Table Integration Test Coverage Improvements
26. LIR-40  Documentation and User Guide
    ─────── Phase 7 Complete (Advanced Features) ───────
```

---

## Summary

| Category | Count |
|----------|-------|
| Completed | 26 |
| Cancelled | 2 |
| Remaining | 26 |
| **Total** | **54** |

**Recently Completed:**
- LIR-51: Unit Tests for Controller Factory Functions ✅ (PR #103)
- LIR-50: Refactor Factory Functions to Registry Pattern ✅ (PR #102)
- LIR-20: Simulation Controller (Sequential) ✅ (PR #96)
- LIR-45: Table Integration Tests ✅ (PR #92)
- LIR-43: Multi-Player Session Management ✅ (PR #88)

**In Review:**
- LIR-52: Error Handling and Edge Case Tests (GitHub #99, PR #104) - High priority, review fixes applied
- LIR-53: Test Quality Improvements for SimulationController (GitHub #100, PR #105) - Medium, review fixes applied

**New Issues (from PR #105 review):**
- LIR-54: Enhanced RNG Isolation Verification with Hand-Level Testing (GitHub #106) - Medium, requires infrastructure

**Other Open Issues (from earlier PR reviews):**
- LIR-47: Session API Consistency and DRY Refactoring (GitHub #89)
- LIR-48: TableSession Performance Optimization (GitHub #90)
- LIR-49: Table Integration Test Coverage Improvements (GitHub #93)

**Critical Path:** LIR-22 → LIR-25 → LIR-31 → LIR-34

**Next Up:**
- LIR-52 (Error Handling Tests) - PR #104 in review, fixes applied
- LIR-53 (Test Quality Improvements) - PR #105 in review, fixes applied
- LIR-22 (Results Aggregation) - critical path, all dependencies complete
