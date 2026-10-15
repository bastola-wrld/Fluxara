#!/usr/bin/env python3
"""
Load the starter facility list into the database.

Run after migrations:
    alembic upgrade head
    python scripts/seed_facilities.py

Every row is loaded with data_source = "manual_unverified": the locations are
approximate and the reported totals were typed in by hand without a cited
source. They are placeholders for development, not reference data. Replace
them with records from a named registry before showing them to a customer.

Safe to rerun: a facility already present (same name and country) is skipped.
No sites are invented and no alerts are created.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fluxara.database.models import Facility          # noqa: E402
from fluxara.database.sync import session_scope       # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "satellite_data", "facilities", "global_facilities.json")

COUNTRY = {"USA": "USA", "UK": "GBR", "Germany": "DEU", "Netherlands": "NLD", "Brazil": "BRA",
           "Kazakhstan": "KAZ", "Mexico": "MEX", "Algeria": "DZA", "Qatar": "QAT",
           "Indonesia": "IDN", "South Africa": "ZAF", "Canada": "CAN", "Norway": "NOR",
           "Saudi Arabia": "SAU", "Russia": "RUS", "China": "CHN", "India": "IND",
           "Australia": "AUS", "Nigeria": "NGA", "UAE": "ARE", "Iraq": "IRQ", "Iran": "IRN"}


def main():
    with open(DATA) as f:
        records = json.load(f)
    added = skipped = 0
    with session_scope() as db:
        existing = {(n, c) for n, c in db.query(Facility.name, Facility.country)}
        for r in records:
            country = COUNTRY.get(r.get("country", ""), (r.get("country") or "")[:3].upper())
            if (r["name"], country) in existing:
                skipped += 1
                continue
            state = r.get("state") or None
            db.add(Facility(
                name=r["name"], country=country,
                state=state if state and len(state) <= 2 else None,
                lat=float(r["lat"]), lon=float(r["lon"]),
                sector=r.get("type"),
                # epa_reported and fluxara_latest are left empty on purpose:
                # the file's totals are unsourced CO2 equivalent figures, not
                # methane rates, so they must not be shown as kg/hr of methane.
                data_source="manual_unverified",
            ))
            added += 1
    print(f"Facilities added: {added}, already present: {skipped}")


if __name__ == "__main__":
    main()
