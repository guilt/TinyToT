-include Makefile.user

# === Find bash for cross-platform compatibility (Git Bash on Windows, /bin/bash on Unix) ===
ifneq ($(wildcard /bin/bash),)
  BASH := /bin/bash
else ifneq ($(wildcard C:/Program Files/Git/bin/bash.exe),)
  BASH := C:/Program Files/Git/bin/bash.exe
else ifneq ($(wildcard C:/Program Files (x86)/Git/bin/bash.exe),)
  BASH := C:/Program Files (x86)/Git/bin/bash.exe
else
  BASH := bash
endif

SHELL := $(BASH)
.SHELLFLAGS := -c

# OS-specific defaults
ifeq ($(OS),Windows_NT)
  PYTHON ?= python
  CURL    = curl.exe
else
  PYTHON ?= python3
  CURL    = curl
endif

# Defaults — overridable in Makefile.user
PYTHON_VERSION ?= 3.8
PORT ?= 11434

.DEFAULT_GOAL := help

.PHONY: help \
	pre-check install-deps install clean clean-dist \
	test tests pytest unit-tests \
	precommit format lint \
	run stop \
	docs build-docs docs-serve live-docs \
	examples \
	ingest benchmark bench \
	build publish publish-test \
	build-binary


help: ## Show this help message
	@$(PYTHON) -c "import re; f=open('Makefile').read(); [print('  {:<30s} {}'.format(m.group(1), m.group(2))) for m in re.finditer(r'^([a-z_-]+):.*?## (.+)', f, re.M)]"

pre-check: ## Run pre-checks (Python, pipenv, and any Makefile.user checks)
	@echo "-------------- Running pre-checks --------------"
	@$(PYTHON) --version
	@pipenv --version
	$(user-pre-check)

install-deps: pre-check ## Install all dependencies into pipenv virtualenv
	@echo "-------------- Installing dependencies --------------"
	@pipenv --python $(PYTHON_VERSION)
	@export PIP_INDEX_URL=$${PIP_INDEX_URL:-$$($(PYTHON) -c "import re; m=re.search(r'\[\[source\]\]\s*url = \"([^\"]+)\"', open('Pipfile').read()); print(m.group(1) if m else '')")} && \
	pipenv run pip install -e ".[dev]"
	@pipenv run pre-commit install

install: install-deps ## Install dependencies. Run this first.

clean: ## Remove virtualenv and build artifacts
	@echo "-------------- Cleaning --------------"
	@pipenv --venv >/dev/null 2>&1 && pipenv --rm || echo "No virtualenv to remove."
	@rm -rf dist build *.egg-info .pytest_cache .coverage htmlcov junit_xml_test_report.xml

clean-dist: ## Remove build artifacts only (keeps virtualenv)
	@rm -rf dist build *.egg-info

test: tests

tests: pytest ## Run all tests with coverage

pytest: ## Run pytest with branch coverage
	@echo "-------------- Running pytest --------------"
	@pipenv run pytest \
		--junit-xml=junit_xml_test_report.xml \
		--cov-branch \
		--cov=tinytot \
		--cov-report=term-missing \
		--cov-report=html \
		tinytot/tests

unit-tests: ## Run unit tests only
	@echo "-------------- Running pytest (unit-tests) --------------"
	@pipenv run pytest \
		--junit-xml=junit_xml_test_report.xml \
		--cov-branch \
		--cov=tinytot \
		--cov-report=term-missing \
		tinytot/tests/unit

format: ## Format code with ruff/black
	-@pipenv run ruff format tinytot
	-@pipenv run black .
	@pipenv run pre-commit run --all-files

lint: format ## Run linting and formatting

precommit: ## Run pre-commit checks from .pre-commit-config.yaml
	@pipenv run pre-commit run --all-files

build: clean-dist ## Build wheel distribution
	@echo "-------------- Building tinytot package --------------"
	@pipenv run $(PYTHON) -m build --wheel
	@echo "Build artifacts in dist/"

build-binary: clean-dist ## Build self-contained executable (dist/tinytot or dist/tinytot.exe on Windows)
	@echo "-------------- Building tinytot binary (PyInstaller) --------------"
	@pipenv run python scripts/build_binary.py

publish-test: build ## Upload to Test PyPI (requires ~/.pypirc or TWINE_* env vars)
	@echo "-------------- Publishing to Test PyPI --------------"
	@pipenv run twine upload --repository testpypi dist/*

publish: ## Build wheel and upload to PyPI
	@pipenv run $(PYTHON) -m build --wheel

run: ## Start the TinyToT inference server (PORT=11434)
	@echo "-------------- Starting TinyToT server on port $(PORT) --------------"
	@PORT=$(PORT) pipenv run tinytot

stop: ## Gracefully stop the TinyToT server
	@$(CURL) -sf -X POST http://localhost:$(PORT)/api/quit || echo "Server not running on port $(PORT)."

docs: ## Generate API docs then build HTML with Sphinx
	@echo "-------------- Generating API documentation --------------"
	@pipenv run tinytot-api-docs
	@echo "-------------- Building HTML documentation --------------"
	@pipenv run sphinx-build -b html docs/source docs/build/html
	@echo "Documentation built in docs/build/html"

build-docs: docs ## Alias for docs

docs-serve: docs ## Build and serve documentation
	@pipenv run $(PYTHON) -m http.server --directory docs/build/html

live-docs: ## Serve docs with live reload
	@pipenv run sphinx-autobuild docs/source docs/build/html --open-browser

examples: ## Run example scripts from examples/
	@echo "-------------- Running examples --------------"
	@for f in examples/*.py; do \
		echo "Running $$f ..."; \
		pipenv run $(PYTHON) $$f || true; \
	done

ingest: ## Ingest all trace corpora (OpenTraces, CS chains, GSM8K, Princeton ToT)
	@echo "-------------- Ingesting all trace corpora --------------"
	@pipenv run tinytot-ingest all

benchmark: ingest ## Run full benchmark suite (ingests first)
	@echo "-------------- Running TinyToT benchmarks --------------"
	@pipenv run tinytot-bench all --limit 500

bench: benchmark ## Alias for benchmark
