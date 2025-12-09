.PHONY: help install install-dev clean format lint typecheck test test-unit test-integration test-performance test-cov check docs docs-serve run

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := uv pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
RUFF := $(PYTHON) -m ruff
MYPY := $(PYTHON) -m mypy

# Directories
SRC_DIR := src
TESTS_DIR := tests
DOCS_DIR := docs

help: ## Show this help message
	@echo "AAP Migration Tool - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv: ## Create virtual environment with uv
	uv venv --seed --python 3.12

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt
	$(PYTHON) -m pre_commit install

install-editable: ## Install package in editable mode
	$(PIP) install -e .

clean: ## Clean up generated files
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist .eggs htmlcov .coverage coverage.xml .pytest_cache .mypy_cache .ruff_cache
	rm -f migration_state.db*

format: ## Format code with black and isort
	$(BLACK) $(SRC_DIR) $(TESTS_DIR)
	$(ISORT) $(SRC_DIR) $(TESTS_DIR)

lint: ## Run linters (ruff)
	$(RUFF) check $(SRC_DIR) $(TESTS_DIR)

typecheck: ## Run type checking with mypy
	$(MYPY) $(SRC_DIR)

test: ## Run all tests
	$(PYTEST) $(TESTS_DIR)

test-unit: ## Run only unit tests
	$(PYTEST) $(TESTS_DIR)/unit -v

test-integration: ## Run only integration tests
	$(PYTEST) $(TESTS_DIR)/integration -v -m integration

test-performance: ## Run only performance tests
	$(PYTEST) $(TESTS_DIR)/performance -v -m performance

test-cov: ## Run tests with coverage report
	$(PYTEST) $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	$(PYTEST) $(TESTS_DIR) -f

check: format lint typecheck test ## Run all checks (format, lint, typecheck, test)

pre-commit: ## Run pre-commit hooks on all files
	$(PYTHON) -m pre_commit run --all-files

docs: ## Build documentation
	uv pip install -e ".[docs]"
	uv run mkdocs build

docs-serve: ## Serve documentation locally
	uv pip install -e ".[docs]"
	uv run mkdocs serve

run-example: ## Run example migration (requires config)
	$(PYTHON) -m aap_migration.cli migrate full --config config/config.yaml --dry-run

init-env: ## Initialize .env file from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created from .env.example"; \
		echo "Please edit .env with your actual configuration"; \
	else \
		echo ".env file already exists"; \
	fi

setup: install-dev install-editable init-env ## Complete development setup

version: ## Show current version
	@$(PYTHON) -c "from importlib.metadata import version; print(f'AAP Migration Tool v{version(\"aap-migration-tool\")}')" 2>/dev/null || echo "Package not installed"

.PHONY: all
all: check docs ## Run all checks and build docs
