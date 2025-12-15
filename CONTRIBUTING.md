# Contributing to Let It Ride Strategy Simulator

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ChrisHenryOC/let_it_ride.git
cd let_it_ride

# Install dependencies (including dev tools)
poetry install --with dev,viz

# Verify setup
poetry run pytest
```

### Project Structure

```
let_it_ride/
├── src/let_it_ride/
│   ├── core/           # Game engine: cards, deck, hand evaluation
│   ├── strategy/       # Strategy implementations
│   ├── bankroll/       # Bankroll and betting systems
│   ├── simulation/     # Session management, parallelization
│   ├── analytics/      # Statistics, export, visualization
│   ├── config/         # Configuration parsing
│   └── cli/            # Command-line interface
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test data
├── configs/            # Sample configuration files
├── docs/               # Documentation
└── scratchpads/        # Development notes
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

Follow the code style guidelines below.

### 3. Run Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/unit/strategy/test_basic.py

# Run with coverage
poetry run pytest --cov=src/let_it_ride --cov-report=html
```

### 4. Check Code Quality

```bash
# Format code
poetry run ruff format src/ tests/

# Lint code
poetry run ruff check src/ tests/

# Fix auto-fixable issues
poetry run ruff check src/ tests/ --fix

# Type check
poetry run mypy src/
```

Or use Make commands:

```bash
make all  # Runs format, lint, typecheck, and test
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Maintenance

### 6. Create Pull Request

```bash
git push -u origin your-branch-name
```

Then create a PR on GitHub with:
- Clear description of changes
- Link to related issue (if any)
- Test coverage for new code

## Code Style

### Python Style

- Python 3.10+ syntax
- Type hints for all functions
- Docstrings for public functions and classes
- Maximum line length: 88 characters (Black default)

### Type Hints

```python
def calculate_payout(bet: float, multiplier: int) -> float:
    """Calculate payout for a winning hand.

    Args:
        bet: The bet amount in dollars.
        multiplier: The paytable multiplier.

    Returns:
        The payout amount.
    """
    return bet * multiplier
```

### Testing

- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Use pytest fixtures for common setup
- Aim for >90% code coverage

Example test:

```python
import pytest
from let_it_ride.core import Card, Rank, Suit, evaluate_five_card_hand

def test_royal_flush_detection():
    """Royal flush should be correctly identified."""
    cards = [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.QUEEN, Suit.SPADES),
        Card(Rank.JACK, Suit.SPADES),
        Card(Rank.TEN, Suit.SPADES),
    ]
    result = evaluate_five_card_hand(cards)
    assert result.rank == FiveCardHandRank.ROYAL_FLUSH
```

## Areas for Contribution

### Good First Issues

Look for issues labeled `good-first-issue` on GitHub.

### Documentation

- Improve existing docs
- Add examples
- Fix typos

### Testing

- Increase test coverage
- Add edge case tests
- Improve test fixtures

### Features

See `docs/let_it_ride_implementation_plan.md` for planned features.

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass: `poetry run pytest`
- [ ] Code is formatted: `poetry run ruff format src/ tests/`
- [ ] No lint errors: `poetry run ruff check src/ tests/`
- [ ] Type checks pass: `poetry run mypy src/`
- [ ] New code has tests
- [ ] Documentation updated if needed

### PR Description Template

```markdown
## Summary
Brief description of changes.

## Changes
- Change 1
- Change 2

## Testing
How to test these changes.

## Related Issues
Closes #123
```

## Getting Help

- Read the [documentation](docs/index.md)
- Check existing issues
- Ask questions in discussions

## Code of Conduct

Be respectful and constructive. We're all here to learn and improve.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
