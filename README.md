# Let It Ride Strategy Simulator

A Python application to simulate the casino card game "Let It Ride" and analyze various play and betting strategies to identify approaches that maximize the probability of profitable sessions.

**Read the article that goes with this repo:** [Managing Your AI Developer: A Practical Guide](https://chenryventures.substack.com/p/managing-your-ai-developer-a-practical?r=74h1kf)

## Rules
Rules documentation in /docs/BGC_let_it_ride.pdf.  (ignore commit message referring to British Gaming Commission, Claude made that up)
Source: https://oag.ca.gov/sites/all/files/agweb/pdfs/gambling/BGC_let_it_ride.pdf

## Features

- **Accurate Game Simulation**: Full implementation of Let It Ride rules with configurable paytables
- **Multiple Strategies**: Basic (optimal), conservative, aggressive, and custom strategies
- **Bonus Betting**: Three Card Bonus side bet with multiple betting strategies
- **Bankroll Management**: Six betting progression systems (Flat, Martingale, Reverse Martingale, Paroli, D'Alembert, Fibonacci)
- **Multi-Player Tables**: Simulate 1-6 players sharing community cards with per-seat tracking
- **Dealer Configuration**: Optional dealer discard (burn cards) before community cards
- **Statistical Analysis**: Session win rates, drawdown tracking, and bankroll trajectories
- **Parallel Execution**: Scale simulations across multiple CPU cores (in progress)
- **Export Options**: CSV, JSON, and HTML report generation (in progress)
- **Visualizations**: Session outcome histograms and bankroll trajectories (in progress)

## Installation

### Prerequisites

- Python 3.10 or higher
- [Poetry](https://python-poetry.org/) for dependency management

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/ChrisHenryOC/let_it_ride.git
cd let_it_ride

# Install dependencies with Poetry
poetry install

# Or install with visualization support
poetry install --with viz
```

## Usage

### Command Line Interface

```bash
# Show version
poetry run let-it-ride --version

# Run a simulation
poetry run let-it-ride run configs/examples/basic_strategy.yaml

# Run with options
poetry run let-it-ride run configs/examples/basic_strategy.yaml --output ./results --seed 42

# Quiet mode (minimal output, no progress bar)
poetry run let-it-ride run configs/examples/basic_strategy.yaml --quiet

# Verbose mode (include per-session details)
poetry run let-it-ride run configs/examples/basic_strategy.yaml --verbose

# Override session count
poetry run let-it-ride run configs/examples/basic_strategy.yaml --sessions 1000

# Validate a configuration file
poetry run let-it-ride validate configs/sample_config.yaml
```

### Using Make Commands

```bash
# Show all available commands
make help

# Install dependencies
make install

# Run all tests
make test

# Run linting
make lint

# Format code
make format

# Run type checking
make typecheck

# Run all checks
make all
```

## Development

### Running Tests

```bash
# Run all tests with coverage
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run specific test
poetry run pytest tests/unit/test_package.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linter
make lint

# Fix linting issues automatically
make lint-fix

# Run type checker
make typecheck
```

## Project Structure

```
let_it_ride/
├── src/let_it_ride/
│   ├── core/           # Game engine: Card, Deck, Table, hand evaluators
│   ├── strategy/       # Strategy implementations (basic, bonus, custom)
│   ├── bankroll/       # Bankroll tracking and betting systems
│   ├── simulation/     # Session and TableSession management
│   ├── analytics/      # Statistics, export, visualizations
│   ├── config/         # YAML configuration with Pydantic models
│   └── cli.py          # Command-line interface
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test data and fixtures
├── configs/            # Sample YAML configurations
├── docs/               # Documentation
├── scratchpads/        # POC scripts and experiments
└── pyproject.toml      # Project configuration
```

## Configuration

Simulations are configured via YAML files. See `configs/sample_config.yaml` for a complete example.

Key configuration sections:
- `simulation`: Number of sessions, hands per session, random seed, workers
- `table`: Number of seats (1-6) for multi-player simulation
- `dealer`: Discard settings (burn cards before community cards)
- `deck`: Shuffle algorithm (fisher_yates or cryptographic)
- `bankroll`: Starting amount, base bet, stop conditions, betting system
- `strategy`: Pull/ride decision strategy (basic, conservative, aggressive, custom)
- `bonus_strategy`: Three Card Bonus betting (never, always, static, bankroll_conditional, streak_based)
- `paytables`: Main game and bonus payout tables
- `output`: Export formats and visualization options

## Game Rules

Let It Ride is a casino poker variant:

1. Player places 3 equal bets
2. Player receives 3 cards, 2 community cards dealt face down
3. **Decision 1**: View 3 cards, choose to pull Bet 1 or let it ride
4. First community card revealed (4 cards visible)
5. **Decision 2**: Choose to pull Bet 2 or let it ride
6. Second community card revealed, hands evaluated
7. Remaining bets pay according to paytable (pair of 10s or better wins)

Optional Three Card Bonus: Side bet on player's initial 3-card hand.

## Performance Targets

- Throughput: ≥100,000 hands/second
- Memory: <4GB RAM for 10M hands
- Hand evaluation accuracy: 100%

## License

This project is for educational and research purposes.

## Contributing

Contributions welcome! Please ensure all tests pass and code follows the project style:

```bash
make all  # Runs format, lint, typecheck, and test
```
