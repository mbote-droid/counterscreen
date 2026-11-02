# counterscreen developer entry points.
#
# `make check` runs CI's lint/type/architecture/test job, in the same order
# and against the same locked environment. Two CI jobs are deliberately not
# in it, because neither can run unconditionally: `evidence` needs a base ref
# to diff against (`make evidence BASE=<ref>`), and `image` needs a Docker
# daemon (`make image`). Nothing here needs a GPU or the network: every
# heavyweight model is driven as an external process behind an adapter.
#
# Every target runs --frozen, per build_rules section 4.1: a run must never
# silently re-resolve the lockfile, or a local pass can mean a different
# dependency set from the one CI tested.

.DEFAULT_GOAL := help
SHELL := /bin/bash

UV ?= uv
BASE ?= @{u}
RUN := $(UV) run --frozen

.PHONY: help setup lock lock-check fmt lint type arch test cov evidence image check clean

help: ## List available targets.
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

setup: ## Create the virtual environment and install dev dependencies.
	$(UV) sync --locked --group dev

lock: ## Re-resolve the lockfile after touching dependencies.
	$(UV) lock

lock-check: ## Fail if the lockfile is stale against pyproject.toml.
	$(UV) lock --check

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

evidence: ## CI's evidence job: committed measurements must not be rewritten.
	$(RUN) python scripts/check_append_only.py $(BASE)

image: ## CI's image job: build the Dockerfile and smoke-test the entrypoint.
	docker build -t counterscreen:local .
	docker run --rm counterscreen:local version

check: lock-check lint type arch test ## CI's lint/type/architecture/test job.

clean: ## Remove caches and build artefacts. Never touches results.
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml \
		htmlcov dist build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
