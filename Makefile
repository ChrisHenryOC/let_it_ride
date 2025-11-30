.PHONY: install test lint format typecheck all clean help

# Default target
.DEFAULT_GOAL := help

# Python and Poetry
PYTHON := python3
POETRY := poetry

help: ## Show this help message
	@echo "Let It Ride Strategy Simulator - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	$(POETRY) install

test: ## Run tests with pytest and coverage
	$(POETRY) run pytest

test-unit: ## Run unit tests only
	$(POETRY) run pytest tests/unit/

test-integration: ## Run integration tests only
	$(POETRY) run pytest tests/integration/

lint: ## Run ruff linter
	$(POETRY) run ruff check src/ tests/

lint-fix: ## Run ruff linter with auto-fix
	$(POETRY) run ruff check --fix src/ tests/

format: ## Format code with ruff
	$(POETRY) run ruff format src/ tests/

format-check: ## Check code formatting without changes
	$(POETRY) run ruff format --check src/ tests/

typecheck: ## Run mypy type checker
	$(POETRY) run mypy src/

all: format lint typecheck test ## Run all checks (format, lint, typecheck, test)

clean: ## Remove build artifacts and cache files
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

run: ## Run simulation (requires CONFIG=path/to/config.yaml)
	$(POETRY) run let-it-ride run $(CONFIG)

validate: ## Validate configuration (requires CONFIG=path/to/config.yaml)
	$(POETRY) run let-it-ride validate $(CONFIG)
