# counterscreen developer entry points.
#
# `make check` runs exactly what CI runs, in the same order, so a green
# local run means a green pipeline. Nothing here needs a GPU or the network:
# every heavyweight model is driven as an external process behind an adapter.

.DEFAULT_GOAL := help
SHELL := /bin/bash

UV ?= uv
RUN := $(UV) run

.PHONY: help setup lock fmt lint type arch test cov check clean

help: ## List available targets.
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

setup: ## Create the virtual environment and install dev dependencies.
	$(UV) sync --group dev

lock: ## Re-resolve the lockfile after touching dependencies.
	$(UV) lock

fmt: ## Format in place.
	$(RUN) ruff format .
	$(RUN) ruff check . --fix

lint: ## Lint and verify formatting.
	$(RUN) ruff check .
	$(RUN) ruff format --check .

type: ## Type-check under mypy strict.
	$(RUN) mypy

arch: ## Enforce the DESIGN.md section 1 dependency table.
	$(RUN) lint-imports

test: ## Run the test suite, excluding GPU and network tests.
	$(RUN) pytest -m "not gpu and not network"

cov: ## Run the suite with a coverage report.
	$(RUN) pytest -m "not gpu and not network" \
		--cov --cov-report=term-missing --cov-report=xml

check: lint type arch test ## Everything CI runs.

clean: ## Remove caches and build artefacts. Never touches results.
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml \
		htmlcov dist build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
