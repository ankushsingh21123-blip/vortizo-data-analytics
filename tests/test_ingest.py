import io

import pandas as pd
import pytest

from app import ingest
from app.db import Base, Observation, make_engine


def _session():
    from sqlalchemy.orm import sessionmaker

    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_clean_valid_frame():
    df, stats = ingest.clean_frame(
        pd.read_csv(io.StringIO(
            "Date,Country,Confirmed,Recovered,Deaths\n"
            "2022-01-01,India,100,90,2\n2022-01-02,India,150,120,3\n"
        ))
    )
    assert stats["rows_loaded"] == 2
    assert stats["countries"] == ["India"]
    assert list(df["new_confirmed"]) == [0, 50]


def test_clean_missing_column_raises():
    with pytest.raises(ValueError, match="missing required columns"):
        ingest.clean_frame(pd.DataFrame({"Date": ["2022-01-01"], "Country": ["India"]}))


def test_clean_drops_bad_dates_negatives_and_duplicates():
    df, stats = ingest.clean_frame(
        pd.read_csv(io.StringIO(
            "Date,Country,Confirmed,Recovered,Deaths\n"
            "not-a-date,India,10,5,0\n"
            "2022-01-01,US,-5,10,1\n"
            "2022-01-01,United States,20,10,1\n"
            "2022-01-02,India,abc,10,1\n"
        ))
    )
    # Bad date dropped, duplicate (US -> United States, same date) deduped.
    assert stats["rows_loaded"] == 2
    assert stats["rows_dropped"] == 2  # 1 bad date + 1 duplicate
    assert stats["values_cleaned"] >= 2  # negative + non-numeric
    assert set(df["Country"]) == {"United States", "India"}


def test_load_csv_counts_rows():
    session = _session()
    import tempfile
    from pathlib import Path

    fixture = Path(tempfile.mktemp(suffix=".csv"))
    fixture.write_text(
        "Date,Country,Confirmed,Recovered,Deaths\n"
        "2022-01-01,India,100,90,2\n2022-01-02,India,150,120,3\n"
    )
    stats = ingest.load_csv(fixture, session)
    assert stats["rows_loaded"] == 2
    assert session.query(Observation).count() == 2
    assert stats["countries"] == ["India"]
    session.close()


def test_load_csv_upsert_replaces_same_dates():
    session = _session()
    import tempfile
    from pathlib import Path

    fixture = Path(tempfile.mktemp(suffix=".csv"))
    fixture.write_text(
        "Date,Country,Confirmed,Recovered,Deaths\n2022-01-01,India,100,90,2\n"
    )
    ingest.load_csv(fixture, session)
    ingest.load_csv(fixture, session, replace=True)
    assert session.query(Observation).count() == 1
    session.close()
