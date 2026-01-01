# Installation

## System Requirements

- Python 3.10 or higher
- 4GB RAM minimum (for large simulations)
- Operating System: macOS, Linux, or Windows

## Installation Methods

### Using Poetry (Recommended)

[Poetry](https://python-poetry.org/) is the recommended package manager for this project.

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/ChrisHenryOC/let_it_ride.git
cd let_it_ride

# Install dependencies
poetry install

# Verify installation
poetry run let-it-ride --version
```

### With Visualization Support

To enable chart generation (session histograms, bankroll trajectories):

```bash
poetry install --with viz
```

This installs optional dependencies: matplotlib and plotly.

### Using pip

```bash
# Clone the repository
git clone https://github.com/ChrisHenryOC/let_it_ride.git
cd let_it_ride

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Verify installation
let-it-ride --version
```

### Development Setup

For contributing or modifying the codebase:

```bash
# Clone and install with dev dependencies
git clone https://github.com/ChrisHenryOC/let_it_ride.git
cd let_it_ride
poetry install --with dev,viz

# Run tests to verify setup
poetry run pytest

# Run linting
poetry run ruff check src/ tests/

# Run type checking
poetry run mypy src/
```

## Verifying Installation

After installation, verify everything works:

```bash
# Check version
poetry run let-it-ride --version

# Validate a sample configuration
poetry run let-it-ride validate configs/sample_config.yaml

# Run a quick simulation
poetry run let-it-ride run configs/examples/basic_strategy.yaml --sessions 100
```

## Troubleshooting Installation

### Poetry not found

If `poetry` command is not found after installation:

```bash
# Add Poetry to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

### Python version mismatch

Ensure Python 3.10+ is installed:

```bash
python --version  # Should be 3.10 or higher

# If using pyenv
pyenv install 3.10.0
pyenv local 3.10.0
```

### Dependency conflicts

Try removing and reinstalling:

```bash
poetry env remove --all
poetry install
```

## Next Steps

- [Quick Start](quickstart.md) - Run your first simulation
- [Configuration Reference](configuration.md) - Customize simulations
