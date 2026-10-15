# fluxara/ingest/run.py
"""
Run the data jobs from the terminal.

    python -m fluxara.ingest.run emit --days 30             plumes seen in the last 30 days
    python -m fluxara.ingest.run emit --updated-days 3      plumes NASA added or changed recently
    python -m fluxara.ingest.run emit-enrich --limit 200    emission rates (needs EARTHDATA_TOKEN)
    python -m fluxara.ingest.run sentinel2 --days 10        images over your facilities
    python -m fluxara.ingest.run daily                      all of the above, for a scheduler
"""
import argparse
import logging
import os
import sys
from datetime import timedelta

from fluxara.database.sync import session_scope
from fluxara.ingest import emit, sentinel2
from fluxara.ingest.common import now_utc

log = logging.getLogger("fluxara.ingest.run")


def days_ago(days):
    return now_utc() - timedelta(days=days)


def run_daily():
    """
    Run every job once. If one job fails the others still run.
    Returns how many jobs failed (0 means all good).
    """
    jobs = []
    jobs.append(("EMIT catalogue",
                 lambda s: emit.ingest_catalogue(s, updated_since=days_ago(3))))
    if os.getenv("EARTHDATA_TOKEN"):
        jobs.append(("EMIT enrich", lambda s: emit.enrich(s)))
    else:
        log.warning("EARTHDATA_TOKEN not set, so EMIT emission rates are skipped")
    jobs.append(("Sentinel 2 catalogue",
                 lambda s: sentinel2.ingest_for_facilities(s, start=days_ago(7), end=now_utc())))

    failures = 0
    for name, job in jobs:
        try:
            with session_scope() as session:
                log.info("%s: %s", name, job(session))
        except Exception:
            failures += 1
            log.exception("%s failed", name)
    return failures


def build_parser():
    parser = argparse.ArgumentParser(description="Fluxara data jobs")
    commands = parser.add_subparsers(dest="command", required=True)

    emit_cmd = commands.add_parser("emit", help="NASA EMIT plume catalogue")
    emit_cmd.add_argument("--days", type=int, help="plumes observed in the last N days")
    emit_cmd.add_argument("--updated-days", type=int, help="plumes NASA published or changed in the last N days")
    emit_cmd.add_argument("--bbox", type=float, nargs=4, metavar=("WEST", "SOUTH", "EAST", "NORTH"))

    enrich_cmd = commands.add_parser("emit-enrich", help="EMIT emission rates (needs EARTHDATA_TOKEN)")
    enrich_cmd.add_argument("--limit", type=int, default=500)

    s2_cmd = commands.add_parser("sentinel2", help="Sentinel 2 images over facilities")
    s2_cmd.add_argument("--days", type=int, default=10)
    s2_cmd.add_argument("--radius-km", type=float, default=10.0)
    s2_cmd.add_argument("--max-cloud", type=float, default=30.0)
    s2_cmd.add_argument("--facility-id", type=int, action="append")

    commands.add_parser("daily", help="run every job")
    return parser


def main(argv=None):
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "daily":
        return 1 if run_daily() else 0

    with session_scope() as session:
        if args.command == "emit":
            if not args.days and not args.updated_days:
                parser.error("give --days or --updated-days")
            new, updated = emit.ingest_catalogue(
                session,
                since=days_ago(args.days) if args.days else None,
                updated_since=days_ago(args.updated_days) if args.updated_days else None,
                bbox=tuple(args.bbox) if args.bbox else None,
            )
            print(f"EMIT plumes: {new} new, {updated} updated")

        elif args.command == "emit-enrich":
            count = emit.enrich(session, limit=args.limit)
            print(f"EMIT plumes enriched: {count}")

        elif args.command == "sentinel2":
            new, updated = sentinel2.ingest_for_facilities(
                session, start=days_ago(args.days), end=now_utc(),
                radius_km=args.radius_km, max_cloud_pct=args.max_cloud,
                facility_ids=args.facility_id,
            )
            print(f"Sentinel 2 images: {new} new, {updated} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
