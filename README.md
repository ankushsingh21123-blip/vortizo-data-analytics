# Data Analytics Desk — Vortizo Data Analytics proof project

An end-to-end data analytics workspace: collect a real public dataset,
clean and validate it, store it in a database, analyse trends and
anomalies, and present the results as a dashboard, an API, and a
plain-language stakeholder report.

Built as the proof project for the **Vortizo AI Data Analytics
Internship** (₹35,000/month, remote, full-time, 6 months, apply by
27 Nov 2026 — Unstop listing
https://unstop.com/internships/data-analytics-internship-vortizo-ai-1809347).

## What the listing actually requires

From the Unstop listing (read 26 Nov 2026) and its skill tags:

- **Responsibilities:** collect, organize, and validate data from
  relevant sources to maintain accurate datasets; explore datasets,
  identify trends and anomalies, and summarize findings for internal
  stakeholders; prepare clear reports, charts, and dashboards that
  communicate analytical results; work with team members to understand
  data questions and translate them into structured analysis.
- **Skills listed:** Data Analysis, Data Visualization, Stakeholder
  Management.
- **Eligibility:** Undergraduate, Postgraduate, Engineering students,
  Management, Arts / Commerce / Sciences, freshers.
- **Duration / mode:** 6 months, work from home, full-time.

This project demonstrates each responsibility directly — nothing in it
claims experience Ankush does not have; the project itself is the
demonstration.

## Skills demonstrated (visible keywords)

Data Analysis, Data Cleaning, Data Validation, Data Visualization,
SQL, PostgreSQL, Python, FastAPI, pandas, Dashboard, Trend Analysis,
Anomaly Detection, Stakeholder Reporting, REST API, ETL / Data Ingest.

## What it does

1. **Collect** — `scripts/fetch_dataset.py` downloads the real public
   dataset: the Johns Hopkins COVID-19 time series as republished in
   the public `datasets/covid-19` repository
   (`data/countries-aggregated.csv`, no key needed). The bundled
   `data/dataset.csv` is a five-country extract of that file — India,
   United States, Brazil, United Kingdom, Germany, 4,080 daily rows,
   22 Jan 2020 to 16 Apr 2022 — so the repo stays small and the demo
   works offline. Run `make fetch` to re-download the full file.
2. **Clean and validate** — `app/ingest.py` enforces the required
   columns, drops unparseable dates, normalises country names,
   coerces numerics, clamps negatives, dedupes (country, date), and
   computes daily new cases/deaths from the cumulative counts. Every
   cleaning action is counted and reported, never silent.
3. **Store** — SQLAlchemy models in `app/db.py`. SQLite locally
   (zero setup); PostgreSQL when `DATABASE_URL` is set — see
   `schema.sql` and `docker-compose.yml`.
4. **Analyse** — `app/analysis.py`: KPI summary, 7-day rolling
   averages, top countries by cumulative cases, and an anomaly scan
   (a day is flagged when new cases exceed 3× the prior 14-day median
   and are at least 500).
5. **Report** — a plain-language stakeholder report generated from
   the numbers (`GET /api/report`), plus the dashboard at `/` with
   KPI cards, a trend chart, top-countries and anomaly tables, and a
   CSV upload form that validates and loads new data with the same
   cleaning rules.

## Data-quality finding (found while validating, not assumed)

In the source file the **Recovered** column stops being reported for
several countries late in the series (India shows 0 from mid-2021
onward). Analysis and the dashboard therefore rely on Confirmed and
Deaths; Recovered is shown only as loaded, never used for a
conclusion. The stakeholder report states this.

## Run it

```bash
./scripts/run_local.sh
# or: make install && make run
```

Open http://localhost:8000 — the dashboard. API docs at
http://localhost:8000/docs.

With PostgreSQL instead of SQLite (Docker):

```bash
docker compose up --build
# DATABASE_URL=postgresql+psycopg://analytics:analytics@localhost:5432/analytics
```

## API

| Endpoint | What it does |
|---|---|
| `GET /health` | Service status |
| `GET /api/summary` | Row/country/date coverage + latest totals |
| `GET /api/trends?country=India` | Daily new cases + 7-day rolling average |
| `GET /api/top?metric=confirmed` | Countries ranked by latest totals |
| `GET /api/anomalies?country=India` | Spike days (3× 14-day median, ≥ 500) |
| `GET /api/report?country=India` | Plain-language stakeholder report |
| `POST /api/upload` | Upload a CSV (Date, Country, Confirmed, Recovered, Deaths); validated, cleaned, upserted |

## Tests

```bash
make test
# or: .venv/bin/python -m pytest tests/ -q
```

Measured 26 Nov 2026: **15 tests, all passing** — ingest cleaning
(valid, missing columns, bad dates, negatives, duplicates),
analysis (summary, top countries, rolling averages, anomaly
detection), and API (health, summary, trends, top, anomalies,
report, dashboard, CSV upload valid/invalid). The suite runs against
a throwaway SQLite file seeded with a 12-row fixture; it needs no
network and no database server.

Live demo check, 26 Nov 2026: server started, seeded 4,080 rows
from `data/dataset.csv`, `/api/summary` returned 5 countries
2020-01-22 to 2022-04-16, India latest 43,042,097 confirmed, and
the dashboard rendered with the trend chart, top-countries table,
anomaly table, and stakeholder report.

## Honest limits

- The PostgreSQL path (docker-compose + `schema.sql`) is
  code-reviewed only, not live-tested: Docker and a Postgres server
  were not available on the build VM. The SQLite path is fully
  tested; the SQL is standard and the model is identical on both.
- The bundled data is a five-country extract of the full 161,568-row
  source file. The full file can be re-downloaded with
  `scripts/fetch_dataset.py`; the analysis code works on either.
- No machine-learning model, no PyTorch/TensorFlow, no NLP: the
  listing asks for data analysis, cleaning, dashboards, and
  stakeholder reporting, and that is what is built.

## Related Vortizo roles (same company, not built for here)

- **AI Internship**, ₹45,000/month, apply by 4 Dec 2026 — separate
  hold; would need an AI-agents proof project.
- **Python Developer** (Unstop 1775204), ₹40,000/month, full-time,
  6 months — second gate (full-time).

## Project structure

```
app/            FastAPI backend: config, SQLAlchemy models, ingest, analysis
frontend/       Dashboard (no build step, no external CDN)
scripts/        fetch_dataset.py (re-download source), run_local.sh
data/           dataset.csv (5-country extract, real JHU data)
tests/          pytest suite (ingest, analysis, API)
schema.sql      PostgreSQL DDL
docker-compose.yml  app + PostgreSQL
```
