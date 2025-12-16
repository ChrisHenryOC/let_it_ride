# Let It Ride Strategy Simulator - Implementation Plan

## Overview

This document provides a high-level roadmap for the Let It Ride Strategy Simulator implementation. **Detailed issue specifications are maintained in GitHub Issues** - this document serves as an overview and dependency reference only.

## Issue Numbering Convention

Implementation items use **LIR-prefixed identifiers** (e.g., LIR-1, LIR-4) to distinguish them from GitHub's auto-assigned issue numbers. GitHub issue titles follow the format `LIR-N: Title`.

To find an issue: `gh issue list --search "LIR-N in:title"`

## Project Structure

```
let-it-ride-simulator/
├── src/
│   └── let_it_ride/
│       ├── core/           # Game engine components
│       ├── strategy/       # Strategy implementations
│       ├── bankroll/       # Bankroll management
│       ├── simulation/     # Simulation orchestration
│       ├── analytics/      # Statistics and reporting
│       └── config/         # Configuration handling
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── configs/                # Sample YAML configurations
└── docs/
```

---

## Phase Summary

| Phase | Items | Focus | Status |
|-------|-------|-------|--------|
| 1 | LIR-1, LIR-2, LIR-4 through LIR-8 | Foundation | Complete |
| 2 | LIR-9 through LIR-14, LIR-41 | Game Logic + Dealer Discard | Complete |
| 3 | LIR-15 through LIR-19 | Bankroll/Session | Complete |
| 3.5 | LIR-42, LIR-43 | Multi-Player Foundation | Complete |
| 4 | LIR-20 through LIR-24 | Simulation | Complete |
| 5 | LIR-25 through LIR-30, LIR-44, LIR-57 | Analytics + Seat Tracking | In Progress |
| 6 | LIR-31 through LIR-35, LIR-56 | CLI/Integration | Complete |
| 7 | LIR-37 through LIR-40, LIR-45 | Advanced Features | Not Started |

**Note:** LIR-3 (Multi-Deck Shoe) and LIR-36 (Composition-Dependent Strategy) are cancelled - not applicable for single-deck simulation.

---

## Dependency Graph

```
Phase 1: Foundation
LIR-1 ─┬─► LIR-2
       ├─► LIR-4 ─► LIR-6
       ├─► LIR-5 ─► LIR-6
       ├─► LIR-7
       └─► LIR-8

Phase 2: Game Logic
LIR-2,LIR-4,LIR-5 ─► LIR-9
LIR-7 ─► LIR-10 ─► LIR-11
LIR-7,LIR-8 ─► LIR-12
LIR-2,LIR-6,LIR-9,LIR-10 ─► LIR-13
LIR-8 ─► LIR-14
LIR-13 ─► LIR-41 (Dealer Discard)

Phase 3: Bankroll/Session
LIR-1 ─► LIR-15 ─► LIR-16 ─► LIR-17
LIR-13,LIR-15 ─► LIR-18
LIR-13 ─► LIR-19

Phase 3.5: Multi-Player Foundation
LIR-13,LIR-41 ─► LIR-42 (Table Abstraction)
LIR-42,LIR-18 ─► LIR-43 (Multi-Player Session)

Phase 4: Simulation
LIR-18 ─► LIR-20 ─► LIR-21
LIR-19 ─► LIR-22 ─► LIR-23
LIR-1 ─► LIR-24

Phase 5: Analytics
LIR-22 ─► LIR-25 ─► LIR-26
LIR-22 ─► LIR-27, LIR-28
LIR-22 ─► LIR-29 ─► LIR-30
LIR-56,LIR-27 ─► LIR-57 (Seat Position Tracking)
LIR-57,LIR-25 ─► LIR-44 (Chair Position Analytics)

Phase 6: CLI
LIR-8,LIR-20 ─► LIR-31 ─► LIR-32
LIR-8 ─► LIR-33
LIR-42,LIR-43,LIR-31 ─► LIR-56 (Table Config CLI)
All ─► LIR-34 ─► LIR-35

Phase 7: Advanced
LIR-14 ─► LIR-37
LIR-25 ─► LIR-38
LIR-29,LIR-30 ─► LIR-39
All ─► LIR-40
LIR-24 ─► LIR-45
```

---

## Issue Index

For detailed specifications, see GitHub Issues. Use `gh issue view <number>` or search by LIR identifier.

### Phase 1: Foundation
- LIR-1: Project Scaffolding
- LIR-2: Card and Deck
- LIR-4: Five-Card Hand Evaluation
- LIR-5: Three-Card Hand Evaluation
- LIR-6: Paytable Configuration
- LIR-7: Hand Analysis Utilities
- LIR-8: YAML Configuration

### Phase 2: Game Logic
- LIR-9: Hand State Machine
- LIR-10: Basic Strategy
- LIR-11: Baseline Strategies
- LIR-12: Custom Strategy Parser
- LIR-13: Game Engine
- LIR-14: Bonus Betting Strategies
- LIR-41: Dealer Discard Mechanics

### Phase 3: Bankroll/Session
- LIR-15: Bankroll Tracker
- LIR-16: Flat Betting System
- LIR-17: Progressive Betting Systems
- LIR-18: Session State Management
- LIR-19: Session Result Data Structures

### Phase 3.5: Multi-Player Foundation
- LIR-42: Table Abstraction
- LIR-43: Multi-Player Session Management

### Phase 4: Simulation
- LIR-20: Simulation Controller (Sequential)
- LIR-21: Parallel Session Execution
- LIR-22: Results Aggregation
- LIR-23: Statistical Validation
- LIR-24: RNG Quality and Seeding

### Phase 5: Analytics
- LIR-25: Core Statistics Calculator
- LIR-26: Strategy Comparison Analytics
- LIR-27: CSV Export
- LIR-28: JSON Export
- LIR-29: Session Outcome Histogram
- LIR-30: Bankroll Trajectory Visualization
- LIR-44: Chair Position Analytics
- LIR-57: Seat Position Tracking (GitHub #141)

### Phase 6: CLI/Integration
- LIR-31: CLI Entry Point
- LIR-32: Console Output Formatting
- LIR-33: Sample Configuration Files
- LIR-34: End-to-End Integration Tests
- LIR-35: Performance Optimization
- LIR-56: Table Configuration Integration
- LIR-59: Seat Replacement Mode YAML Configuration (GitHub #144)

### Phase 7: Advanced Features
- LIR-37: Streak-Based Bonus Strategy
- LIR-38: Risk of Ruin Calculator
- LIR-39: HTML Report Generation
- LIR-40: Documentation and User Guide
- LIR-45: Property-Based Testing

### Cancelled
- ~~LIR-3: Multi-Deck Shoe~~ - Not needed for single-deck simulation
- ~~LIR-36: Composition-Dependent Strategy~~ - Dependent on LIR-3

---

## Execution Guidelines

1. **Dependency Order**: Complete dependencies before starting dependent issues
2. **Testing**: Run full test suite after completing each phase
3. **Backwards Compatibility**: Multi-player features must not break single-player behavior
4. **Performance**: Target 100k hands/second throughput
