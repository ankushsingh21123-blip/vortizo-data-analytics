"""Configuration. SQLite is the default; set DATABASE_URL for PostgreSQL.

No secrets are read from anywhere except the environment. There are no
API keys in this project at all.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'analytics.db'}"
)
DATASET_PATH = os.environ.get(
    "DATASET_PATH", str(BASE_DIR / "data" / "dataset.csv")
)
