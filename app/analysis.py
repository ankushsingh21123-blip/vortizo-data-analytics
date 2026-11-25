"""Analysis: trends, rankings, anomaly detection, stakeholder reporting.

Every function takes a cleaned DataFrame (columns: Date, Country,
Confirmed, Recovered, Deaths, new_confirmed, new_deaths) and returns
plain data. No model, no LLM, no invented numbers — every figure is
computed from the loaded rows.

Data-quality note (found while validating, not assumed): in the source
file the Recovered column stops being reported for several countries
late in the series (India shows 0 from mid-2021 onward). Analysis and
the dashboard therefore rely on Confirmed and Deaths; Recovered is
shown only as loaded, never used for a conclusion.
"""

import pandas as pd

ANOMALY_MIN_NEW = 500  # ignore tiny absolute spikes in small series
ANOMALY_RATIO = 3.0  # daily new cases vs the prior 14-day median


def load_frame(engine) -> pd.DataFrame:
    df = pd.read_sql_table("observations", engine)
    # Database columns are lowercase; analysis uses Titlecase names.
    df = df.rename(
        columns={
            "date": "Date",
            "country": "Country",
            "confirmed": "Confirmed",
            "recovered": "Recovered",
            "deaths": "Deaths",
        }
    )
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values(["Country", "Date"]).reset_index(drop=True)


def summary(df: pd.DataFrame) -> dict:
    latest = df.sort_values("Date").groupby("Country").tail(1)
    return {
        "rows": int(len(df)),
        "countries": sorted(df["Country"].unique().tolist()),
        "date_min": str(df["Date"].min().date()),
        "date_max": str(df["Date"].max().date()),
        "latest_totals": {
            row.Country: {
                "confirmed": int(row.Confirmed),
                "deaths": int(row.Deaths),
                "date": str(row.Date.date()),
            }
            for row in latest.itertuples(index=False)
        },
    }


def trend(df: pd.DataFrame, country: str, window: int = 7) -> list[dict]:
    sub = df[df["Country"] == country].copy()
    if sub.empty:
        return []
    sub["rolling_avg"] = (
        sub["new_confirmed"].rolling(window, min_periods=1).mean().round(1)
    )
    return [
        {
            "date": str(row.Date.date()),
            "new_confirmed": int(row.new_confirmed),
            "rolling_avg_7d": float(row.rolling_avg),
            "confirmed": int(row.Confirmed),
            "deaths": int(row.Deaths),
        }
        for row in sub.itertuples(index=False)
    ]


def top_countries(df: pd.DataFrame, metric: str = "confirmed", limit: int = 10) -> list[dict]:
    if metric not in ("confirmed", "deaths"):
        raise ValueError("metric must be 'confirmed' or 'deaths'")
    col = "Confirmed" if metric == "confirmed" else "Deaths"
    latest = df.sort_values("Date").groupby("Country").tail(1)
    ranked = latest.sort_values(col, ascending=False).head(limit)
    return [
        {
            "country": row.Country,
            "confirmed": int(row.Confirmed),
            "deaths": int(row.Deaths),
            "date": str(row.Date.date()),
        }
        for row in ranked.itertuples(index=False)
    ]


def anomalies(df: pd.DataFrame, country: str | None = None) -> list[dict]:
    """Days where daily new cases spike above the recent norm.

    A day is an anomaly when new cases exceed 3x the median of the
    prior 14 days and are at least 500 in absolute terms.
    """
    out = []
    frame = df if country is None else df[df["Country"] == country]
    for name, sub in frame.groupby("Country"):
        sub = sub.sort_values("Date").copy()
        sub["median_14d"] = (
            sub["new_confirmed"].shift(1).rolling(14, min_periods=7).median()
        )
        flagged = sub[
            (sub["median_14d"] > 0)
            & (sub["new_confirmed"] >= ANOMALY_MIN_NEW)
            & (sub["new_confirmed"] > ANOMALY_RATIO * sub["median_14d"])
        ]
        for row in flagged.itertuples(index=False):
            out.append(
                {
                    "country": name,
                    "date": str(row.Date.date()),
                    "new_confirmed": int(row.new_confirmed),
                    "median_14d": int(row.median_14d),
                    "ratio": round(float(row.new_confirmed) / float(row.median_14d), 2),
                }
            )
    return sorted(out, key=lambda r: (r["date"], r["country"]))


def stakeholder_report(df: pd.DataFrame, focus_country: str = "India") -> str:
    """Plain-language summary a stakeholder can read without the charts."""
    focus = df[df["Country"] == focus_country]
    lines = []
    date_max = df["Date"].max().date()
    lines.append(
        f"Data covers {len(df):,} daily records across "
        f"{df['Country'].nunique()} countries, "
        f"{df['Date'].min().date()} to {date_max}."
    )
    top = top_countries(df, "confirmed", 1)[0]
    lines.append(
        f"Highest cumulative confirmed cases: {top['country']} "
        f"({top['confirmed']:,} as of {top['date']})."
    )
    if not focus.empty:
        latest = focus.iloc[-1]
        peak = focus.loc[focus["new_confirmed"].idxmax()]
        recent = focus.tail(7)["new_confirmed"].mean()
        month_ago = focus.tail(37).head(7)["new_confirmed"].mean()
        direction = (
            "rising" if recent > month_ago * 1.1
            else "falling" if recent < month_ago * 0.9 else "broadly flat"
        )
        lines.append(
            f"{focus_country}: {int(latest['Confirmed']):,} confirmed cases and "
            f"{int(latest['Deaths']):,} deaths as of {date_max}. "
            f"Peak single day was {int(peak['new_confirmed']):,} new cases on "
            f"{peak['Date'].date()}. The 7-day average of daily new cases is "
            f"{recent:,.0f}, {direction} against a month ago ({month_ago:,.0f})."
        )
    found = anomalies(df)
    lines.append(
        f"Anomaly scan flagged {len(found)} spike days across all countries "
        f"(daily new cases over 3x the prior 14-day median and at least 500)."
    )
    lines.append(
        "Data-quality note: the source stops reporting Recovered for several "
        "countries late in the series, so conclusions here use Confirmed and "
        "Deaths only."
    )
    return "\n".join(lines)
