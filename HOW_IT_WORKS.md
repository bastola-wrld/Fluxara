# How Fluxara works

A plain walkthrough of the code, in the order data flows through it.

## The big picture

```
NASA EMIT          Copernicus Sentinel 2
    |                      |
    v                      v
fluxara/ingest/emit.py   fluxara/ingest/sentinel2.py     (fetch and save)
    |                      |
    v                      v
        Postgres + PostGIS database
    plume_detections   satellite_scenes   ingestion_runs
                 |
                 v
        fluxara/api  (FastAPI)          /v1/plumes, /v1/timeseries ...
                 |
                 v
        client/  (React dashboard)
```

1. **Ingestion jobs** fetch real satellite data and save it.
2. **The database** stores it, with the source and licence on every row.
3. **The API** answers questions like "which plumes are near this site?".
4. **The dashboard** shows the answers.

## 1. Ingestion: `fluxara/ingest/`

| File | What it does |
|---|---|
| `common.py` | Shared helpers: a web client that retries, a record of each run, and `save_rows` which inserts new rows and updates old ones |
| `emit.py` | NASA EMIT methane plumes, in two steps (see below) |
| `sentinel2.py` | A list of Sentinel 2 images over each facility. No pixels yet |
| `run.py` | The terminal commands that start the jobs |

**EMIT in two steps.**
Step 1 (`ingest_catalogue`) asks NASA's search service for plumes and saves
the outline, time and links. No login needed.
Step 2 (`enrich`) downloads each plume's small metadata file to get the
emission rate. It needs a free Earthdata token.
If NASA did not measure a plume, the rate stays empty. We never fill it with a guess.

**Running it twice is safe.** Every row has a unique pair
(`source`, `source_id`). If a plume is already there, it is updated instead
of added again. The catalogue step only touches catalogue columns, so it
never wipes out an emission rate that step 2 saved.

**Every run is logged** in `ingestion_runs`: when it ran, what it was asked
for, how many rows it fetched, added and updated, which code version ran it,
and the error if it failed. If a run fails, nothing it wrote is kept.

## 2. Database: `fluxara/database/` and `migrations/`

| File | What it does |
|---|---|
| `models.py` | Every table, as Python classes |
| `connection.py` | Database connection for the API (async) |
| `sync.py` | Database connection for terminal jobs (plain) |
| `migrations/versions/` | Step by step changes to the tables, applied with `alembic upgrade head` |

The new tables:

* **plume_detections**: one row per plume. Where (`geom`), when
  (`observed_at`), how big (`emission_rate_kg_hr` with its uncertainty),
  and where the data came from (`source`, `licence`, `attribution`,
  `commercial_use_allowed`).
* **satellite_scenes**: one row per Sentinel 2 image, with links to its bands.
* **ingestion_runs**: the log described above.

**PostGIS** is a Postgres add on for maps. It lets us ask "what is within
5 km of this point?" quickly. Locations are stored in SRID 4326, which just
means ordinary longitude and latitude.

`facilities.geom` is filled in by the database itself from `lat` and `lon`
(a trigger in migration 0002), so you only ever set `lat` and `lon`.

## 3. API: `fluxara/api/`

| Route | What it returns |
|---|---|
| `GET /v1/plumes` | Plumes, newest first. Filter by facility, point and radius, dates, measured only, or sellable only |
| `GET /v1/timeseries` | Month by month detections near a facility. Months with nothing are left out |
| `GET /health` | Is the database up, how many plumes we hold, when the last job succeeded |

Everything else (login, facilities, alerts, admin, company and government
panels) is your original code.

**Turned off for now:** the old neural `/v1/invert` route and PDF report
generation. Both printed numbers that were not observed. Switches for them are
in `.env`.

## 4. Settings: `.env`

| Setting | Why |
|---|---|
| `DATABASE_URL` | Where the database is |
| `FLUXARA_SECRET_KEY` | Signs login tokens. Must be long and random |
| `FLUXARA_ENV` | `development` or `production`. The dev key only works in development |
| `EARTHDATA_TOKEN` | Lets the EMIT enrich step download emission rates |

## 5. Tests: `tests/`

`pytest` runs 35 tests against a real Postgres with PostGIS. The files in
`tests/fixtures/` are real answers recorded from NASA and Copernicus, so the
tests check our code against what those services actually send.

## Common commands

```bash
alembic upgrade head                              # build or update the tables
python scripts/seed_facilities.py                 # load the starter facility list
python scripts/seed_admin.py                      # create your admin login
python -m fluxara.ingest.run emit --days 365      # fetch EMIT plumes
python -m fluxara.ingest.run emit-enrich          # fetch their emission rates
python -m fluxara.ingest.run sentinel2 --days 10  # list Sentinel 2 images
uvicorn fluxara.api.main:app --reload             # start the API
pytest                                            # run the tests
```
