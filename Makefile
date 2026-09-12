# Makefile for Hiver Assessment
.PHONY: help install explore prepare baseline evaluate demo test lint format clean

PYTHON := python
PIP := pip
PYTEST := pytest

help:
	@echo "Available commands:"
	@echo "  make ui        : Launch the modern interactive Web UI Dashboard"
	@echo "  make install   : Install project dependencies"
	@echo "  make explore   : Run data exploration and distribution checks"
	@echo "  make prepare   : Run data preprocessing and create deterministic splits"
	@echo "  make baseline  : Train the baseline model"
	@echo "  make evaluate  : Run evaluation suite against test data"
	@echo "  make demo      : Run interactive or sample inference demo"
	@echo "  make test      : Run unit tests and zero-leakage checks"
	@echo "  make lint      : Run code linter"
	@echo "  make format    : Format code using black"
	@echo "  make clean     : Clean up build artifacts and temporary files"

ui:
	$(PYTHON) app.py

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

explore:
	$(PYTHON) scripts/explore.py

prepare:
	$(PYTHON) scripts/prepare_data.py

baseline:
	$(PYTHON) scripts/train_baseline.py

evaluate:
	$(PYTHON) scripts/evaluate.py

demo:
	$(PYTHON) scripts/demo.py

test:
	$(PYTEST) tests/

lint:
	flake8 src/ scripts/ tests/

format:
	black src/ scripts/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
