# fluxara/retrieval/show.py
"""
Print what the checks found for a facility, one line per image.

    python -m fluxara.retrieval.show --facility-id 1
"""
import argparse
import sys
from collections import Counter

from fluxara.database.models import Facility, PlumeDetection, SiteObservation
from fluxara.database.sync import session_scope


def describe(observation, plume):
    """One readable line for one check."""
    day = observation.observed_at.strftime("%Y-%m-%d")
    if observation.status == "plume_detected" and plume is not None:
        return (f"{day}  PLUME     {plume.emission_rate_kg_hr:,.0f} "
                f"+/- {plume.emission_uncertainty_kg_hr:,.0f} kg/h, "
                f"wind {observation.wind_speed_10m_ms:.1f} m/s, "
                f"direction {observation.wind_agreement}")
    if observation.status == "no_plume":
        limit = observation.detection_limit_kg_hr
        text = f"{day}  no plume  nothing above {limit:,.0f} kg/h" if limit else f"{day}  no plume"
        return text + (f"  ({observation.reason})" if observation.reason else "")
    return f"{day}  unusable  {observation.reason or ''}"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show methane checks for a facility")
    parser.add_argument("--facility-id", type=int, required=True)
    args = parser.parse_args(argv)

    with session_scope() as session:
        facility = session.get(Facility, args.facility_id)
        if facility is None:
            print(f"No facility with id {args.facility_id}")
            return 1
        rows = (session.query(SiteObservation, PlumeDetection)
                .outerjoin(PlumeDetection, PlumeDetection.id == SiteObservation.plume_detection_id)
                .filter(SiteObservation.facility_id == facility.id)
                .order_by(SiteObservation.observed_at)
                .all())

        print(f"{facility.name} ({facility.lat:.4f}, {facility.lon:.4f})")
        if not rows:
            print("No checks yet. Run:  python -m fluxara.retrieval.run "
                  f"--facility-id {facility.id}")
            return 0
        for observation, plume in rows:
            print(describe(observation, plume))

        counts = Counter(observation.status for observation, _plume in rows)
        print()
        for status in sorted(counts):
            print(f"{status}: {counts[status]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
