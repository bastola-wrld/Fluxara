# scripts/validate_s2_against_emit.py
"""
How good is our Sentinel 2 method? Compare it with NASA.

NASA's EMIT instrument measures methane plumes far more precisely than
Sentinel 2 can. So for plumes NASA has measured, we run our own method on a
Sentinel 2 image of the same place taken close in time, and compare.

    python scripts/validate_s2_against_emit.py --limit 20

Before running it
    python -m fluxara.ingest.run emit --days 1600
    python -m fluxara.ingest.run emit-enrich --limit 500     (gives the NASA rates)

What it writes
    satellite_data/cache/validation_s2_vs_emit.csv   one line per NASA plume tried
    and a summary on screen, which starts with "EMIT plumes tried:"

Read the result with care
    * The two satellites do not pass at the same moment. A leak can change or
      stop within hours, so a miss is not always our method's fault. The CSV
      says how many hours apart the two images were.
    * Sentinel 2 only sees big leaks. A NASA plume below our detection limit
      for that image is counted as "too small to see", not as a miss.
    * Only quote numbers from this script to a customer. Never the old ones.
"""
import argparse
import csv
import logging
import os
import statistics
import sys
from datetime import timedelta
from types import SimpleNamespace

# Lets "python scripts/validate_s2_against_emit.py" find the fluxara package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func

from fluxara.database.models import PlumeDetection
from fluxara.database.sync import session_scope
from fluxara.ingest import sentinel2
from fluxara.ingest.common import make_http_session
from fluxara.retrieval import pipeline
from fluxara.retrieval.bands import BandFetcher, LoginFailed
from fluxara.retrieval.run import explain_missing, missing_logins
from fluxara.retrieval.wind import Era5Wind, FixedWind

log = logging.getLogger("fluxara.validate")

# Written into the cache folder, which docker compose shares with your
# computer, so the file shows up in satellite_data/cache/ next to the code.
OUTPUT = os.path.join(os.getenv("FLUXARA_CACHE_DIR") or "satellite_data/cache",
                      "validation_s2_vs_emit.csv")
COLUMNS = ["emit_id", "emit_time", "lat", "lon", "emit_rate_kg_hr", "emit_uncertainty_kg_hr",
           "s2_image", "hours_apart", "result", "reason", "s2_rate_kg_hr",
           "s2_uncertainty_kg_hr", "s2_detection_limit_kg_hr", "wind_speed_ms",
           "wind_agreement", "s2_divided_by_emit"]


def emit_plumes(session, min_rate, how_many):
    """NASA plumes with a rate of at least min_rate, newest first."""
    rows = (session.query(PlumeDetection.source_id, PlumeDetection.observed_at,
                          func.ST_Y(PlumeDetection.geom), func.ST_X(PlumeDetection.geom),
                          PlumeDetection.emission_rate_kg_hr,
                          PlumeDetection.emission_uncertainty_kg_hr,
                          PlumeDetection.wind_speed_ms)
            .filter(PlumeDetection.source == "nasa_emit")
            .filter(PlumeDetection.emission_rate_kg_hr >= min_rate)
            .order_by(PlumeDetection.observed_at.desc())
            .limit(how_many)
            .all())
    return [SimpleNamespace(id=r[0], time=r[1], lat=r[2], lon=r[3], rate=r[4],
                            uncertainty=r[5], wind_speed=r[6]) for r in rows]


def images_around(http, plume, max_hours):
    """
    Sentinel 2 images over the plume, from 45 days before (for the reference)
    until max_hours after. Returned as simple objects that look like rows of
    satellite_scenes, so the pipeline can use them without saving them.
    """
    window = timedelta(hours=max_hours)
    start = plume.time - window - timedelta(days=pipeline.MAX_REFERENCE_GAP_DAYS)
    box = sentinel2.bbox_around(plume.lat, plume.lon, 1.0)
    scenes = {}
    for item in sentinel2.search_scenes(http, box, start, plume.time + window):
        row = sentinel2.parse_item(item)
        if row:
            scenes[row["source_id"]] = SimpleNamespace(id=None, **row)
    return list(scenes.values())


def closest_image(plume, scenes, max_hours):
    """The usable image nearest in time to the NASA observation, or None."""
    def hours_from_plume(scene):
        return abs((scene.acquired_at - plume.time).total_seconds()) / 3600

    near = [scene for scene in scenes
            if pipeline.supported(scene)
            and hours_from_plume(scene) <= max_hours
            and (scene.cloud_cover_pct is None or scene.cloud_cover_pct <= 30)]
    return min(near, key=hours_from_plume) if near else None


def compare_one(plume, http, fetcher, wind, max_hours):
    """Run our method for one NASA plume. Returns one line for the CSV."""
    line = {"emit_id": plume.id, "emit_time": plume.time.isoformat(),
            "lat": round(plume.lat, 5), "lon": round(plume.lon, 5),
            "emit_rate_kg_hr": round(plume.rate),
            "emit_uncertainty_kg_hr": round(plume.uncertainty) if plume.uncertainty else ""}

    scenes = images_around(http, plume, max_hours)
    target = closest_image(plume, scenes, max_hours)
    if target is None:
        line["result"] = "no_image"
        line["reason"] = f"no clear Sentinel 2A or 2B image within {max_hours} hours"
        return line

    line["s2_image"] = target.source_id
    line["hours_apart"] = round((target.acquired_at - plume.time).total_seconds() / 3600, 1)

    if wind is None:   # --emit-wind: use the wind speed NASA used
        if not plume.wind_speed:
            line["result"], line["reason"] = "failed", "NASA gave no wind speed for this plume"
            return line
        wind = FixedWind(plume.wind_speed, 0.0)

    result = pipeline.check_point(plume.lat, plume.lon, target, scenes, fetcher, wind)
    line["result"] = result["status"]
    line["reason"] = result.get("reason") or ""
    if result.get("detection_limit_kg_hr") is not None:
        line["s2_detection_limit_kg_hr"] = round(result["detection_limit_kg_hr"])
    if result.get("wind_speed_10m_ms") is not None:
        line["wind_speed_ms"] = round(result["wind_speed_10m_ms"], 1)
    if result["status"] == "plume_detected":
        measured = result["plume"]
        line["s2_rate_kg_hr"] = round(measured["rate_kg_hr"])
        line["s2_uncertainty_kg_hr"] = round(measured["uncertainty_kg_hr"])
        line["s2_divided_by_emit"] = round(measured["rate_kg_hr"] / plume.rate, 2)
        if wind.source != "fixed":
            line["wind_agreement"] = result["wind_agreement"]
    return line


def summarise(lines, max_hours):
    """The summary printed at the end. Plain counts, then the comparison."""
    def count(result):
        return sum(1 for line in lines if line["result"] == result)

    seen = [line for line in lines if line["result"] == "plume_detected"]
    missed = [line for line in lines if line["result"] == "no_plume"]
    too_small = [line for line in missed
                 if line.get("s2_detection_limit_kg_hr")
                 and line["emit_rate_kg_hr"] < line["s2_detection_limit_kg_hr"]]

    text = [f"EMIT plumes tried: {len(lines)}",
            f"  no Sentinel 2 image within {max_hours} hours: {count('no_image')}",
            f"  Sentinel 2 image unusable: {count('unusable')}",
            f"  failed (download or wind problem): {count('failed')}",
            f"  Sentinel 2 also saw a plume: {len(seen)}",
            f"  Sentinel 2 saw no plume: {len(missed)}",
            f"    of those, NASA's plume was too small for that image: {len(too_small)}",
            f"    of those, big enough to see but not seen: {len(missed) - len(too_small)}"]

    if seen:
        ratios = sorted(line["s2_divided_by_emit"] for line in seen)
        within_double = sum(1 for ratio in ratios if 0.5 <= ratio <= 2.0)
        agree = 0
        for line in seen:
            gap = abs(line["s2_rate_kg_hr"] - line["emit_rate_kg_hr"])
            allowed = line["s2_uncertainty_kg_hr"] + (line["emit_uncertainty_kg_hr"] or 0)
            agree += gap <= allowed
        text += ["",
                 f"Where both measured a rate ({len(seen)} plumes):",
                 f"  our rate divided by NASA's, middle value: {statistics.median(ratios):.2f}",
                 f"  lowest {ratios[0]:.2f}, highest {ratios[-1]:.2f}",
                 f"  within a factor of 2 of NASA: {within_double} of {len(seen)}",
                 f"  agree within the stated uncertainties: {agree} of {len(seen)}"]
    else:
        text += ["", "No plume was measured by both, so there is no rate comparison yet."]

    if len(seen) < 10:
        text += ["",
                 "This is too few to quote an accuracy. Enrich more NASA plumes",
                 "(emit-enrich --limit 500) and run again with a higher --limit."]
    text += ["", f"Details: {OUTPUT}",
             "The two satellites pass hours apart, and leaks change. Treat this as a",
             "rough check of our method, not as a precise accuracy figure."]
    return "\n".join(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare our Sentinel 2 method with NASA EMIT")
    parser.add_argument("--limit", type=int, default=20, help="how many NASA plumes to try")
    parser.add_argument("--min-rate", type=float, default=1000.0,
                        help="skip NASA plumes smaller than this (kg/h)")
    parser.add_argument("--max-hours", type=int, default=48,
                        help="the Sentinel 2 image must be this close in time")
    parser.add_argument("--emit-wind", action="store_true",
                        help="use NASA's wind speed instead of ERA5 (no Climate Data Store needed)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    missing = missing_logins(need_era5=not args.emit_wind)
    if missing:
        explain_missing(missing)
        return 2

    with session_scope() as session:
        plumes = emit_plumes(session, args.min_rate, args.limit)
    if not plumes:
        print("No NASA plumes with a rate in the database yet. Run first:")
        print("  python -m fluxara.ingest.run emit --days 1600")
        print("  python -m fluxara.ingest.run emit-enrich --limit 500")
        return 1

    http = make_http_session()
    fetcher = BandFetcher()
    wind = None if args.emit_wind else Era5Wind()

    lines = []
    try:
        for number, plume in enumerate(plumes, start=1):
            try:
                line = compare_one(plume, http, fetcher, wind, args.max_hours)
            except LoginFailed as problem:
                print(problem)
                return 2
            except Exception as error:
                line = {"emit_id": plume.id, "emit_time": plume.time.isoformat(),
                        "emit_rate_kg_hr": round(plume.rate),
                        "emit_uncertainty_kg_hr": round(plume.uncertainty) if plume.uncertainty else "",
                        "result": "failed", "reason": f"{type(error).__name__}: {error}"}
            lines.append(line)
            log.info("[%s/%s] %s NASA %s kg/h -> %s %s", number, len(plumes),
                     plume.time.date(), line["emit_rate_kg_hr"], line["result"],
                     line.get("s2_rate_kg_hr") or line.get("reason") or "")
    except KeyboardInterrupt:
        print("\nStopped. Showing what was finished so far.")

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(lines)

    print()
    print(summarise(lines, args.max_hours))
    return 0


if __name__ == "__main__":
    sys.exit(main())
