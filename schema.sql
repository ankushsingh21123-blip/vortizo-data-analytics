-- PostgreSQL schema for the analytics store.
-- Mirrors the SQLAlchemy model in app/db.py. Applied automatically
-- by docker-compose on first database start.
CREATE TABLE IF NOT EXISTS observations (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    country VARCHAR(100) NOT NULL,
    confirmed BIGINT NOT NULL DEFAULT 0,
    recovered BIGINT NOT NULL DEFAULT 0,
    deaths BIGINT NOT NULL DEFAULT 0,
    new_confirmed BIGINT NOT NULL DEFAULT 0,
    new_deaths BIGINT NOT NULL DEFAULT 0,
    UNIQUE (country, date)
);
CREATE INDEX IF NOT EXISTS idx_observations_country_date
    ON observations (country, date);
CREATE INDEX IF NOT EXISTS idx_observations_date
    ON observations (date);
