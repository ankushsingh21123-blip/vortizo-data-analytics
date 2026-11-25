.PHONY: install test run fetch

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements-dev.txt

test:
	.venv/bin/python -m pytest tests/ -q

run:
	.venv/bin/python -m uvicorn app.main:app --reload --port 8000

fetch:
	.venv/bin/python scripts/fetch_dataset.py
