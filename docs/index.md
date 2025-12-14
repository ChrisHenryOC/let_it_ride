# Let It Ride Strategy Simulator Documentation

Welcome to the Let It Ride Strategy Simulator documentation. This tool simulates millions of hands of the casino card game "Let It Ride" to analyze various play and betting strategies.

## Getting Started

- **[Installation](installation.md)** - Set up the simulator on your system
- **[Quick Start](quickstart.md)** - Run your first simulation in 5 minutes

## User Guide

- **[Configuration Reference](configuration.md)** - All configuration options with examples
- **[Strategies](strategies.md)** - Main game strategy guide with basic strategy charts
- **[Bonus Strategies](bonus_strategies.md)** - Three Card Bonus betting strategies
- **[Output Formats](output_formats.md)** - Understanding CSV, JSON, and HTML output

## Reference

- **[API Documentation](api.md)** - Using the simulator as a Python library
- **[Examples](examples.md)** - Common workflows and use cases
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Additional Resources

- **[Requirements Specification](let_it_ride_requirements.md)** - Full requirements document
- **[Implementation Plan](let_it_ride_implementation_plan.md)** - Development roadmap
- **[Performance](performance.md)** - Performance benchmarks and targets
- **[Contributing](../CONTRIBUTING.md)** - How to contribute to the project

## Game Overview

Let It Ride is a casino poker variant where:

1. Player places 3 equal bets
2. Player receives 3 cards, 2 community cards dealt face down
3. **Decision 1**: View 3 cards, choose to pull Bet 1 or let it ride
4. First community card revealed
5. **Decision 2**: Choose to pull Bet 2 or let it ride
6. Second community card revealed, hands evaluated
7. Remaining bets pay on pair of 10s or better

The simulator helps answer questions like:
- What strategy maximizes session win rates?
- How do stop limits affect outcomes?
- Is bonus betting worthwhile under different conditions?
- What bankroll sizing provides optimal results?
