PYTHON ?= python
PACKAGE ?= email_harvester

.PHONY: install lint test cov typecheck build audit run-example

install:
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -e .[dev]

lint:
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ruff format --check src tests

test:
	$(PYTHON) -m pytest

cov:
	$(PYTHON) -m pytest --cov=src/$(PACKAGE) --cov-report=term-missing

typecheck:
	$(PYTHON) -m mypy src/$(PACKAGE)

build:
	$(PYTHON) -m build

audit:
	$(PYTHON) -m pip_audit

run-example:
	$(PYTHON) email_harvester_ultimate.py --categories-file categories.txt --output results.csv

