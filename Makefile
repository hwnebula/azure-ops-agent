.PHONY: install lint typecheck test test-integration evals check
install:
	python -m pip install -e ".[dev,api]"
lint:
	ruff check . && ruff format --check .
typecheck:
	mypy src
test:
	pytest
test-integration:
	pytest -m integration
evals:
	python evals/run_evals.py
check: lint typecheck test
