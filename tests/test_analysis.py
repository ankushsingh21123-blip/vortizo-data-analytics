import pandas as pd

from app import analysis


def _frame(rows):
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def test_summary_and_top():
    df = _frame([
        {"Date": "2022-01-01", "Country": "India", "Confirmed": 100, "Recovered": 90, "Deaths": 2, "new_confirmed": 0, "new_deaths": 0},
        {"Date": "2022-01-02", "Country": "India", "Confirmed": 150, "Recovered": 120, "Deaths": 3, "new_confirmed": 50, "new_deaths": 1},
        {"Date": "2022-01-01", "Country": "Brazil", "Confirmed": 50, "Recovered": 40, "Deaths": 1, "new_confirmed": 0, "new_deaths": 0},
    ])
    s = analysis.summary(df)
    assert s["rows"] == 3
    assert s["countries"] == ["Brazil", "India"]
    assert s["latest_totals"]["India"]["confirmed"] == 150
    assert analysis.top_countries(df)[0]["country"] == "India"


def test_trend_rolling_average():
    df = _frame([
        {"Date": "2022-01-01", "Country": "India", "Confirmed": 100, "Recovered": 90, "Deaths": 2, "new_confirmed": 0, "new_deaths": 0},
        {"Date": "2022-01-02", "Country": "India", "Confirmed": 150, "Recovered": 120, "Deaths": 3, "new_confirmed": 50, "new_deaths": 1},
        {"Date": "2022-01-03", "Country": "India", "Confirmed": 220, "Recovered": 180, "Deaths": 3, "new_confirmed": 70, "new_deaths": 0},
    ])
    series = analysis.trend(df, "India")
    assert [p["new_confirmed"] for p in series] == [0, 50, 70]
    assert series[1]["rolling_avg_7d"] == 25.0  # (0 + 50) / 2
    assert analysis.trend(df, "Nowhere") == []


def test_top_rejects_bad_metric():
    df = _frame([{"Date": "2022-01-01", "Country": "India", "Confirmed": 1, "Recovered": 0, "Deaths": 0, "new_confirmed": 0, "new_deaths": 0}])
    try:
        analysis.top_countries(df, "bogus")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for bad metric")


def test_anomalies_flag_spike_but_not_small_bump():
    rows = []
    for day in range(1, 21):
        rows.append({"Date": f"2022-01-{day:02d}", "Country": "India",
                     "Confirmed": day * 100, "Recovered": 0, "Deaths": 0,
                     "new_confirmed": 100, "new_deaths": 0})
    rows[19]["new_confirmed"] = 5000  # day 20: 50x the median
    rows[19]["Confirmed"] = 6900
    df = _frame(rows)
    flagged = analysis.anomalies(df, "India")
    assert len(flagged) == 1
    assert flagged[0]["date"] == "2022-01-20"
    assert flagged[0]["ratio"] == 50.0

    rows[19]["new_confirmed"] = 200  # below the 500 minimum
    df = _frame(rows)
    assert analysis.anomalies(df, "India") == []


def test_stakeholder_report_is_plain_and_numeric():
    df = _frame([
        {"Date": "2022-01-01", "Country": "India", "Confirmed": 100, "Recovered": 90, "Deaths": 2, "new_confirmed": 0, "new_deaths": 0},
        {"Date": "2022-01-02", "Country": "India", "Confirmed": 150, "Recovered": 120, "Deaths": 3, "new_confirmed": 50, "new_deaths": 1},
        {"Date": "2022-01-01", "Country": "Brazil", "Confirmed": 50, "Recovered": 40, "Deaths": 1, "new_confirmed": 0, "new_deaths": 0},
    ])
    report = analysis.stakeholder_report(df, "India")
    assert "India" in report
    assert "150" in report
    assert "Anomaly scan" in report
