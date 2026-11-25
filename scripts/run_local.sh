#!/bin/bash
# Local run: creates the venv on first use, installs deps, starts the app.
set -e
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements-dev.txt
fi
exec .venv/bin/python -m uvicorn app.main:app --reload --port 8000
