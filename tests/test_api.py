from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok", "service": "data-analytics-desk"}


def test_summary_and_trends():
    with TestClient(app) as client:
        s = client.get("/api/summary").json()
        assert s["rows"] >= 12
        assert "India" in s["countries"] and "Brazil" in s["countries"]
        assert s["latest_totals"]["India"]["confirmed"] == 500

        t = client.get("/api/trends", params={"country": "India"}).json()
        assert len(t["points"]) == 6
        assert [p["new_confirmed"] for p in t["points"]] == [0, 50, 70, 80, 90, 110]
        assert client.get("/api/trends", params={"country": "Nowhere"}).status_code == 404


def test_top_and_anomalies_and_report():
    with TestClient(app) as client:
        top = client.get("/api/top").json()
        assert top["countries"][0]["country"] == "India"
        assert client.get("/api/top", params={"metric": "bogus"}).status_code == 400
        assert isinstance(client.get("/api/anomalies").json()["anomalies"], list)
        report = client.get("/api/report", params={"country": "India"}).json()
        assert "India" in report["report"]


def test_dashboard_serves():
    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert "Data Analytics Desk" in res.text


def test_upload_valid_and_invalid():
    with TestClient(app) as client:
        good = (
            "Date,Country,Confirmed,Recovered,Deaths\n"
            "2022-01-01,France,10,8,0\n2022-01-02,France,25,15,1\n"
        )
        res = client.post(
            "/api/upload", files={"file": ("france.csv", good, "text/csv")}
        )
        assert res.status_code == 200, res.text
        assert res.json()["rows_loaded"] == 2

        bad = "Date,Country,Confirmed\n2022-01-01,France,10\n"
        res = client.post(
            "/api/upload", files={"file": ("bad.csv", bad, "text/csv")}
        )
        assert res.status_code == 400

        res = client.post(
            "/api/upload", files={"file": ("notes.txt", "hello", "text/plain")}
        )
        assert res.status_code == 400
