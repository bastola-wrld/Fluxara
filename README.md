# Fluxara

Methane observations from open satellite data, with the source, licence and
uncertainty attached to every number.

## Status

Early prototype. What works today:

* Ingestion of real NASA EMIT methane plumes and a Sentinel 2 scene catalogue
  into PostGIS, with full provenance. Jobs are safe to rerun.
* An API to query plumes near a site, and an honest monthly time series.
* Login, roles, and the dashboard shell.

What does not exist yet:

* Our own Sentinel 2 methane retrieval (next step).
* PDF reports on real data. The old templates are switched off.
* Any validated accuracy figure. Do not quote one.

The neural "inversion" model in `fluxara/models` is experimental research
code trained on synthetic data. It is off by default and is not the product.

## Quick start

Needs Docker, or Python 3.11 plus Postgres 15+ with PostGIS.

```bash
cp .env.example .env          # then fill in FLUXARA_SECRET_KEY and the passwords
docker compose up --build -d  # db, api (runs migrations), fetcher, frontend
docker compose exec api python scripts/seed_facilities.py
docker compose exec api python scripts/seed_admin.py
```

API docs: http://localhost:8000/docs. Dashboard: http://localhost:3000.

Without Docker:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements_dev.txt
alembic upgrade head
python scripts/seed_facilities.py
python scripts/seed_admin.py
uvicorn fluxara.api.main:app --reload
```

## Getting real data in

```bash
python -m fluxara.ingest.run emit --days 60            # NASA EMIT plumes, no login needed
python -m fluxara.ingest.run emit-enrich               # emission rates, needs EARTHDATA_TOKEN
python -m fluxara.ingest.run sentinel2 --days 10       # scenes over your facilities
python -m fluxara.ingest.run daily                     # all of the above, for a scheduler
```

`EARTHDATA_TOKEN` is free: create an account at https://urs.earthdata.nasa.gov
and choose Generate Token.

Each run is recorded in `ingestion_runs` with its parameters, row counts, code
version and any error.

## Checking a site for methane

```bash
docker compose exec api python -m fluxara.retrieval.run --facility-id 1 --days 60
docker compose exec api python -m fluxara.retrieval.show --facility-id 1
```

This needs the Copernicus logins in `.env`. See `CHANGES_WEEK2.md` for what the
method does, what it cannot do, and how to compare it with NASA.

## Database changes

The schema is managed by Alembic. The API never creates tables itself.

```bash
alembic upgrade head                           # apply
alembic revision --autogenerate -m "message"   # after editing models.py
```

If you have an old database made before migrations existed:
`alembic stamp 0001 && alembic upgrade head`.

## Tests

```bash
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/fluxara_test pytest
```

The tests need a real Postgres with PostGIS and rebuild that database, so its
name must contain `test`.

## Layout

| Path | What |
|---|---|
| `fluxara/ingest/` | One module per data source, plus `run.py` |
| `fluxara/retrieval/` | Our own methane measurement from Sentinel 2 images |
| `fluxara/database/` | Models, async engine (API), sync engine (jobs) |
| `fluxara/api/` | FastAPI app and routes |
| `migrations/` | Alembic migrations |
| `client/` | React dashboard |
| `scripts/` | Seeding and the daily job |
| `tests/` | Test suite and recorded API responses |
| `legacy/`, `docs/archive/` | Old research code and documents. Read their README first. |

See `HOW_IT_WORKS.md` for a plain walkthrough of the code, and `DATA_SOURCES.md` for licences and for what each satellite can and cannot see.

## Licence

Proprietary. See `LICENSE`.
