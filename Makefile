# Python Project Makefile
# Generated for testing streamlined Claude Code structure

.PHONY: help quality test test-full format lint typecheck clean install version-sync version-check

# Default target
help: ## Show this help message
	@echo "Streamlined Claude Code Template - Python Project"
	@echo "Available targets:"
	@echo "  quality     - Run complete quality pipeline (format + lint + typecheck)"
	@echo "  test        - Run test suite (quick)"
	@echo "  test-full   - Run tests with coverage report"
	@echo "  format      - Format code with ruff"
	@echo "  lint        - Lint code with ruff"
	@echo "  typecheck   - Type check with mypy"
	@echo "  clean       - Clean build artifacts and cache"
	@echo "  install     - Install project in development mode"

# Quality pipeline (used by enhanced git-flow commands)
quality: format lint typecheck ## Run complete quality pipeline

format: ## Format code with ruff
	ruff format .

lint: ## Lint code with ruff
	ruff check .

typecheck: ## Type check with mypy
	mypy .

# Testing (used by enhanced git-flow commands)
test: ## Run test suite quickly
	pytest -q

test-full: ## Run tests with coverage
	pytest --cov=src --cov-report=html --cov-report=term

# Development
install: ## Install project dependencies
	pip install -e .
	@if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/
	rm -rf htmlcov/ .coverage .pytest_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Version management (used by /bump-version command)
version-sync: ## Sync VERSION file to Python project files
	@if [ -f VERSION ]; then \
		VERSION=$$(cat VERSION) && \
		if [ -f pyproject.toml ]; then \
			sed -i.bak 's/version = ".*"/version = "'$$VERSION'"/' pyproject.toml && rm pyproject.toml.bak; \
		fi && \
		echo "✅ Synced version $$VERSION to Python project files"; \
	else \
		echo "❌ No VERSION file found"; \
	fi

version-check: ## Validate version consistency
	@if [ -f VERSION ]; then \
		VERSION=$$(cat VERSION) && \
		echo "Checking version consistency for $$VERSION..." && \
		if [ -f pyproject.toml ]; then \
			grep -q "version = \"$$VERSION\"" pyproject.toml || echo "⚠️  pyproject.toml version mismatch"; \
		fi && \
		echo "✅ Version consistency check complete"; \
	else \
		echo "❌ No VERSION file found"; \
	fi