"""Test setup: point the app at a throwaway SQLite file seeded with a
tiny fixture CSV, before any app module is imported."""

import os
import sys
import tempfile
from pathlib import Path

FIXTURE_CSV = """Date,Country,Confirmed,Recovered,Deaths
2022-01-01,India,100,90,2
2022-01-02,India,150,120,3
2022-01-03,India,220,180,3
2022-01-04,India,300,250,4
2022-01-05,India,390,300,5
2022-01-06,India,500,400,6
2022-01-01,Brazil,50,40,1
2022-01-02,Brazil,70,55,1
2022-01-03,Brazil,90,70,2
2022-01-04,Brazil,110,85,2
2022-01-05,Brazil,130,100,2
2022-01-06,Brazil,160,120,3
"""

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_TMP = Path(tempfile.mkdtemp(prefix="vortizo-test-"))
_FIXTURE = _TMP / "fixture.csv"
_FIXTURE.write_text(FIXTURE_CSV)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'test.db'}"
os.environ["DATASET_PATH"] = str(_FIXTURE)
