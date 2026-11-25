"""Data collection, cleaning and loading.

Source: the Johns Hopkins COVID-19 time series as republished in the
public `datasets/covid-19` repository
(https://github.com/datasets/covid-19, file data/countries-aggregated.csv).
`data/dataset.csv` is a five-country extract of that file
(India, United States, Brazil, United Kingdom, Germany); see
scripts/fetch_dataset.py to re-download the full file and regenerate it.

Cleaning rules (all counted and reported, never silent):
- required columns: Date, Country, Confirmed, Recovered, Deaths
- unparseable dates are dropped
- country names are stripped; "US" is normalised to "United States"
- numeric fields are coerced to integers; non-numeric values become 0
  and are counted as cleaned, negative values are clamped to 0
- duplicate (country, date) rows keep the last occurrence
- daily new cases/deaths are computed as the day-on-day difference of
  the cumulative counts, floored at 0 (the source occasionally revises
  cumulative counts downwards)
"""

from pathlib import Path

import pandas as pd

from app.db import Observation

REQUIRED_COLUMNS = ["Date", "Country", "Confirmed", "Recovered", "Deaths"]
NUMERIC_COLUMNS = ["Confirmed", "Recovered", "Deaths"]


def clean_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Validate and clean a raw frame. Returns (clean frame, stats)."""
    stats = {"rows_read": len(df), "rows_dropped": 0, "values_cleaned": 0}
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    df = df[REQUIRED_COLUMNS].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    bad_dates = df["Date"].isna()
    stats["rows_dropped"] += int(bad_dates.sum())
    df = df[~bad_dates]

    df["Country"] = df["Country"].astype(str).str.strip()
    df.loc[df["Country"] == "US", "Country"] = "United States"
    empty_country = df["Country"].isin(["", "nan", "None"])
    stats["rows_dropped"] += int(empty_country.sum())
    df = df[~empty_country]

    for col in NUMERIC_COLUMNS:
        numeric = pd.to_numeric(df[col], errors="coerce")
        stats["values_cleaned"] += int(numeric.isna().sum())
        numeric = numeric.fillna(0)
        negative = numeric < 0
        stats["values_cleaned"] += int(negative.sum())
        df[col] = numeric.clip(lower=0).astype("int64")

    before = len(df)
    df = df.drop_duplicates(subset=["Country", "Date"], keep="last")
    stats["rows_dropped"] += before - len(df)
    df = df.sort_values(["Country", "Date"]).reset_index(drop=True)

    # Daily deltas from the cumulative counts, floored at 0.
    df["new_confirmed"] = (
        df.groupby("Country")["Confirmed"].diff().fillna(0).clip(lower=0).astype("int64")
    )
    df["new_deaths"] = (
        df.groupby("Country")["Deaths"].diff().fillna(0).clip(lower=0).astype("int64")
    )
    stats["rows_loaded"] = len(df)
    stats["countries"] = sorted(df["Country"].unique().tolist())
    return df, stats


def load_csv(path: str | Path, session, replace: bool = False) -> dict:
    """Clean a CSV file and upsert it into the observations table."""
    df, stats = clean_frame(pd.read_csv(path))
    if replace:
        countries = df["Country"].unique().tolist()
        session.query(Observation).filter(
            Observation.country.in_(countries)
        ).delete(synchronize_session=False)
    rows = [
        Observation(
            date=row.Date.date() if hasattr(row.Date, "date") else row.Date,
            country=row.Country,
            confirmed=int(row.Confirmed),
            recovered=int(row.Recovered),
            deaths=int(row.Deaths),
            new_confirmed=int(row.new_confirmed),
            new_deaths=int(row.new_deaths),
        )
        for row in df.itertuples(index=False)
    ]
    session.bulk_save_objects(rows)
    session.commit()
    stats["date_min"] = str(df["Date"].min().date())
    stats["date_max"] = str(df["Date"].max().date())
    return stats
