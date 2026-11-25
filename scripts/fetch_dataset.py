"""Re-download the source dataset and regenerate data/dataset.csv.

Source: Johns Hopkins COVID-19 time series as republished in the public
`datasets/covid-19` repository (no key needed):
    https://raw.githubusercontent.com/datasets/covid-19/main/data/countries-aggregated.csv

Usage:
    python scripts/fetch_dataset.py            # full file -> data/full.csv, extract -> data/dataset.csv
    python scripts/fetch_dataset.py --full-only

The bundled data/dataset.csv is a five-country extract (India, United
States, Brazil, United Kingdom, Germany). "US" is normalised to
"United States" to match the other country names.
"""

import argparse
import urllib.request
from pathlib import Path

import pandas as pd

SOURCE_URL = (
    "https://raw.githubusercontent.com/datasets/covid-19/main/data/"
    "countries-aggregated.csv"
)
KEEP = ["India", "US", "Brazil", "United Kingdom", "Germany"]
BASE_DIR = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-only", action="store_true")
    args = parser.parse_args()

    full_path = BASE_DIR / "data" / "full.csv"
    print(f"Downloading {SOURCE_URL} ...")
    urllib.request.urlretrieve(SOURCE_URL, full_path)
    df = pd.read_csv(full_path, parse_dates=["Date"])
    print(f"Full file: {len(df):,} rows, {df['Country'].nunique()} countries, "
          f"{df['Date'].min().date()} to {df['Date'].max().date()}")
    if args.full_only:
        return
    sub = df[df["Country"].isin(KEEP)].copy()
    sub["Country"] = sub["Country"].replace({"US": "United States"})
    sub = sub.sort_values(["Country", "Date"])
    out = BASE_DIR / "data" / "dataset.csv"
    sub.to_csv(out, index=False)
    print(f"Extract: {len(sub):,} rows -> {out}")


if __name__ == "__main__":
    main()
