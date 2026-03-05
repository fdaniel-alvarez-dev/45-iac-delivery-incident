.PHONY: setup demo test lint clean

PYTHON ?= python3
PYTHONPATH := src

setup:
	$(PYTHON) -m venv .venv
	@mkdir -p artifacts
	@echo "Created .venv and artifacts/ (no dependencies to install)."

demo:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m portfolio_proof report --examples examples --out artifacts/report.md

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

lint:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compileall -q src tests
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/lint.py

clean:
	rm -rf artifacts __pycache__ .pytest_cache .venv
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
