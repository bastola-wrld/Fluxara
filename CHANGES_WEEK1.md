# Week 1 changes

## Removed because it was invented
* `timeseries.py` random chart data and the hardcoded "15% underreporting".
* The `847.3 kg/hr` mock response in `/v1/invert`. The route is now off by default.
* Random number fallbacks in the data loaders and the mock downloaders.
* The daily pipeline that ran an untrained network on random arrays, saved the
  result as an emission rate and raised alerts from it.
* Seeding that padded the database to 847 sites with random coordinates and
  created sample "40% above baseline" alerts.
* The random `fluxara` column in the facility seed files.
* `validation_report.md`, the benchmark script and `epa_ghgrp.csv`, which was
  an HTML error page, not EPA data.
* PDF generation is switched off: the templates print "0.0 kg/hr" and "LOW"
  risk for sites with no data.

## Fixed because it did not run
* `fluxara/api/main.py` used names it never imported, so the API could not start.
* `fpdf2` was missing from the requirements.
* The Dockerfile copied folders that do not exist.
* `App.jsx` imported `invertpanel` with the wrong case, which breaks on Linux.
* Month buckets shifted by one when the database was not in UTC.

## Security
* The frontend no longer ships a shared admin API key.
* No default secret key, passwords or database URL in the code. The dev key
  only works when `FLUXARA_ENV=development`.
* CORS no longer allows every origin with credentials.
* If this repository was ever public, treat the old defaults as leaked:
  `fluxara-dev-key-2024`, `fluxaraadmin123`, `fluxara123`, `fluxara-super-secret-2024`.

## Added
* PostGIS geometry on facilities with a GiST index and a sync trigger.
* `plume_detections`, `satellite_scenes`, `ingestion_runs` with provenance and licence per row.
* Alembic migrations.
* Ingesters for NASA EMIT plumes and the Sentinel 2 scene catalogue, safe to rerun.
* `GET /v1/plumes` and a real `GET /v1/timeseries`.
* 35 tests against real PostGIS, and a CI workflow.

## Not done, on purpose
* The facility seed list is still hand typed and unverified. Its reported
  totals are no longer loaded.
* `fluxara_latest` and `risk_level` are empty until there is a real method to fill them.
* The dashboard's Invert panel still calls the disabled route.
* Government and company panels still compute "underreporting" from
  `fluxara_latest`. With no data they show nothing, but the logic needs rebuilding.
