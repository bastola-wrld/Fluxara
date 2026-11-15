# Week 2 changes

Week 1 gave Fluxara real data from NASA. Week 2 gives it its own measurement:
it looks at Sentinel 2 images over a site, finds methane plumes and works out
the leak rate in kg per hour, with an uncertainty.

## What is new

* `fluxara/retrieval/varon.py` The method, as plain maths. It follows Varon et
  al. 2021 (doi:10.5194/amt-14-2771-2021). The top of the file explains every
  step and has a worked example you can check by hand.
* `fluxara/retrieval/bands.py` Downloads band 11 and band 12 from Copernicus
  and cuts out the 10 km square around a site. Files are cached.
* `fluxara/retrieval/wind.py` The wind at the site when the satellite passed,
  from ERA5.
* `fluxara/retrieval/pipeline.py` Puts it together and saves every check.
* `fluxara/retrieval/run.py` and `show.py` Run it and read the results from
  the terminal.
* `scripts/validate_s2_against_emit.py` Compares our numbers with NASA's.
* `GET /v1/observations` Every check of a facility, with counts.
* Database migration `0003`: sun and view angles on images, and the new
  `site_observations` table.

## Every check is saved, also the empty ones

Each image of a site ends as one of three results:

| Result | Meaning |
| --- | --- |
| `plume_detected` | A plume was found. Rate, uncertainty and outline are saved. |
| `no_plume` | The image was good and nothing was above the detection limit, which is saved too. |
| `unusable` | The image could not be used. The reason is saved. |

"We looked on 12 clear days and saw nothing above 3 tonnes per hour" is a
result a customer can use. That is why the empty checks are kept.

## The false alarm check

Bare ground is never cancelled perfectly between two days. What is left is
patchy, and a patch next to a site can look exactly like a plume. So for every
image the code pretends the site is at about 70 other places in the same
square and asks how often it finds a blob as strong as the one at the real
site. The blob at the site only counts as a plume if it beats 95% of them.
The same blobs also raise the detection limit, so a patchy image honestly
says it could only have seen a very large leak.

## What the method cannot do

* It only sees big leaks, about 1 to 3 tonnes per hour and up, over bright and
  even ground such as desert. Not over water, snow, forest or towns.
* Sentinel 2C images are refused. Nobody has published a methane calibration
  for that satellite yet, and we do not guess one.
* The reference image is an earlier image of the same place. If the site was
  leaking the same amount on both days, the leak cancels out and is missed.
* Very large plumes are underestimated, because the step from signal to
  methane uses a straight line.
* The wind is the largest source of error in the rate.
* A plume near a site is not proof that the site caused it.

## Logins you need in `.env`

| Setting | Where to get it | Used for |
| --- | --- | --- |
| `CDSE_USERNAME`, `CDSE_PASSWORD` | dataspace.copernicus.eu | Sentinel 2 images |
| `CDSAPI_KEY` | cds.climate.copernicus.eu, your profile | ERA5 wind |
| `EARTHDATA_TOKEN` | urs.earthdata.nasa.gov | NASA emission rates |

After changing `.env` run `docker compose up -d --force-recreate`. Containers
only read `.env` when they are created.

## Commands

```bash
# Check one facility over the last 60 days, then read the results
docker compose exec api python -m fluxara.retrieval.run --facility-id 1 --days 60
docker compose exec api python -m fluxara.retrieval.show --facility-id 1

# Compare our method with NASA
docker compose exec api python -m fluxara.ingest.run emit-enrich --limit 500
docker compose exec api python scripts/validate_s2_against_emit.py --limit 20 --emit-wind
```

The comparison writes `satellite_data/cache/validation_s2_vs_emit.csv` and
prints a summary that starts with `EMIT plumes tried:`. With `--emit-wind` it
uses the wind speed NASA used, so the comparison is about the methane
measurement alone. Without it, ERA5 wind is used, as in normal runs.

## Smaller fixes

* `emit-enrich` now prints its progress every 25 plumes.
* Ctrl+C during a data job keeps the finished work and marks the run as
  `stopped`, not stuck on `running`.
* The Docker image installs `libexpat1`, which the image reader needs.

## Tests

72 tests, all against a real PostGIS database. The new ones use made up images
with a known plume, so we know the right answer and can check the maths.
