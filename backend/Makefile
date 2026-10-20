PY ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: venv install dev test lint fmt seed run

venv:
	python3 -m venv .venv

install: venv
	$(PIP) install -U pip
	$(PIP) install -e ".[dev]"

run:
	$(PY) -m uvicorn app.main:app --reload --port 8000

seed:
	$(PY) -m app.seed

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check .

fmt:
	$(PY) -m ruff format .
