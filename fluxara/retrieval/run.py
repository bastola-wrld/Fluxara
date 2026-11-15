# fluxara/retrieval/run.py
"""
Check facilities for methane plumes from the terminal.

    python -m fluxara.retrieval.run --facility-id 1 --days 60
    python -m fluxara.retrieval.run --facility-id 1 --facility-id 2 --days 30

What it does, in order
    1. Checks that the logins it needs are in .env, and stops early if not.
    2. Updates the list of Sentinel 2 images over each facility.
    3. Checks every image and saves the result (see pipeline.py).

Look at the results with:  python -m fluxara.retrieval.show --facility-id 1
"""
import argparse
import logging
import os
import sys
from datetime import timedelta

from fluxara.database.sync import session_scope
from fluxara.ingest import sentinel2
from fluxara.ingest.common import now_utc
from fluxara.retrieval import pipeline
from fluxara.retrieval.bands import BandFetcher, LoginFailed
from fluxara.retrieval.wind import Era5Wind, FixedWind

log = logging.getLogger("fluxara.retrieval.run")


def missing_logins(need_era5=True):
    """The names of the .env settings that are still empty."""
    needed = ["CDSE_USERNAME", "CDSE_PASSWORD"]
    if need_era5:
        needed.append("CDSAPI_KEY")
    return [name for name in needed if not os.getenv(name)]


def explain_missing(names):
    print("These settings are missing in .env: " + ", ".join(names))
    print("  CDSE_USERNAME, CDSE_PASSWORD  free account at https://dataspace.copernicus.eu")
    print("  CDSAPI_KEY                    free account at https://cds.climate.copernicus.eu")
    print("After editing .env run:  docker compose up -d --force-recreate")


def build_parser():
    parser = argparse.ArgumentParser(description="Check facilities for methane plumes")
    parser.add_argument("--facility-id", type=int, action="append", required=True)
    parser.add_argument("--days", type=int, default=60, help="look this many days back")
    parser.add_argument("--max-cloud", type=float, default=30.0)
    parser.add_argument("--wind-speed", type=float,
                        help="use this 10 m wind (m/s) instead of ERA5, for trying things out")
    parser.add_argument("--wind-from", type=float, default=0.0,
                        help="direction the wind comes from, in degrees, with --wind-speed")
    return parser


def main(argv=None):
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    # 1. Logins
    use_era5 = args.wind_speed is None
    missing = missing_logins(need_era5=use_era5)
    if missing:
        explain_missing(missing)
        return 2
    wind = Era5Wind() if use_era5 else FixedWind(args.wind_speed, args.wind_from)
    fetcher = BandFetcher()

    end = now_utc()
    start = end - timedelta(days=args.days)
    catalogue_start = start - timedelta(days=pipeline.MAX_REFERENCE_GAP_DAYS)

    # 2. Image list. A 1 km radius is enough: we only want images over the site.
    with session_scope() as session:
        new, updated = sentinel2.ingest_for_facilities(
            session, start=catalogue_start, end=end, radius_km=1.0,
            max_cloud_pct=100.0, facility_ids=args.facility_id)
        print(f"Sentinel 2 images: {new} new, {updated} updated")

    # 3. Check every image
    exit_code = 0
    for facility_id in args.facility_id:
        with session_scope() as session:
            try:
                counts = pipeline.run_for_facility(session, facility_id, start, end,
                                                   fetcher, wind, args.max_cloud)
            except LoginFailed as problem:
                print(problem)
                return 2
            except ValueError as problem:
                print(problem)
                exit_code = 1
                continue
        checked = sum(counts.values())
        print(f"Facility {facility_id}: {checked} images checked, "
              f"{counts['plume_detected']} with a plume, {counts['no_plume']} clear, "
              f"{counts['unusable']} unusable, {counts['failed']} failed")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
