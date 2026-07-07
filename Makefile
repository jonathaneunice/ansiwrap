VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: install dev lint format test test-cov tox update upgrade upgrade-check venv

UV ?= uv

_require-uv:
	@command -v $(UV) >/dev/null 2>&1 || { echo "uv is required for dependency refresh; install from https://docs.astral.sh/uv/"; exit 1; }

install:
	python3 -m pip install -U .

dev: venv
	$(PIP) install -e ".[dev]"

venv:
	python3 -m venv $(VENV)

lint: dev
	$(VENV)/bin/ruff check ansiwrap tests
	$(VENV)/bin/black --check ansiwrap tests
	$(VENV)/bin/validate-pyproject pyproject.toml
	$(VENV)/bin/pyroma -d .
	rm -rf dist
	$(PYTHON) -m build -o dist
	$(VENV)/bin/twine check dist/*

format: dev
	$(VENV)/bin/black ansiwrap tests

test: dev
	$(VENV)/bin/pip install -e ".[test]"
	$(VENV)/bin/pytest

test-cov: dev
	$(VENV)/bin/pip install -e ".[test]"
	$(VENV)/bin/pytest --cov-branch --cov-report=term-missing --cov-report=html --cov=ansiwrap
	-open htmlcov/index.html

tox: dev
	$(VENV)/bin/tox

upgrade-check: _require-uv
	$(UV)x --from uv-update-check uuc -p pyproject.toml

update: dev _require-uv
	$(UV)x --from uv-update-check uuc -u -p pyproject.toml
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -e ".[dev,test]"

upgrade: update
