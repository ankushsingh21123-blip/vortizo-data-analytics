"""FastAPI backend + dashboard for the Data Analytics proof project.

Run:  make run        (http://localhost:8000)
API docs: http://localhost:8000/docs

On first start the database is seeded from DATASET_PATH
(data/dataset.csv) if it is empty. No keys, no external calls at runtime.
"""

import io
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import analysis, ingest
from app.config import BASE_DIR, DATASET_PATH
from app.db import SessionLocal, engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    session = SessionLocal()
    try:
        from app.db import Observation

        if session.query(Observation).count() == 0:
            ingest.load_csv(DATASET_PATH, session)
    finally:
        session.close()
    yield


app = FastAPI(title="Data Analytics Desk", version="1.0.0", lifespan=lifespan)


def _frame():
    return analysis.load_frame(engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "data-analytics-desk"}


@app.get("/api/summary")
def api_summary():
    return analysis.summary(_frame())


@app.get("/api/trends")
def api_trends(country: str = "India"):
    series = analysis.trend(_frame(), country)
    if not series:
        raise HTTPException(status_code=404, detail=f"no data for country: {country}")
    return {"country": country, "points": series}


@app.get("/api/top")
def api_top(metric: str = "confirmed", limit: int = 10):
    try:
        return {"metric": metric, "countries": analysis.top_countries(_frame(), metric, limit)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/anomalies")
def api_anomalies(country: str | None = None):
    return {"anomalies": analysis.anomalies(_frame(), country)}


@app.get("/api/report")
def api_report(country: str = "India"):
    return {"country": country, "report": analysis.stakeholder_report(_frame(), country)}


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    """Upload a CSV with columns Date, Country, Confirmed, Recovered,
    Deaths. Rows are validated and cleaned with the same rules as the
    seed ingest, then upserted for their (country, date)."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="only .csv files are accepted")
    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
        _, stats = ingest.clean_frame(df)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session = SessionLocal()
    try:
        stats = ingest.load_csv(io.BytesIO(raw), session, replace=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()
    return JSONResponse({"filename": file.filename, **stats})


# Dashboard (single-page app, no build step, no external CDN).
app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")
