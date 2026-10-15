# fluxara/api/routes/timeseries.py
"""
GET /v1/timeseries  a month by month summary of real plume detections.

Nothing is filled in or smoothed. A month with no detection is left out,
because "no detection" does not mean "no emissions": satellites only see big
leaks, clouds get in the way, and they only pass over now and then.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fluxara.api.auth import verify_api_key
from fluxara.api.routes.plumes import near
from fluxara.database.connection import get_db
from fluxara.database.models import Facility, PlumeDetection as Plume

router = APIRouter(prefix="/timeseries", tags=["Dashboard"])


def one_decimal(value):
    return round(float(value), 1) if value is not None else None


@router.get("")
async def get_timeseries(
    facility_id: Optional[int] = Query(None),
    radius_km: float = Query(5.0, gt=0, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(verify_api_key),
):
    """
    Monthly summary for the area around one facility, or for everything.

    "fluxara" is the average of the plume rates measured that month, each one
    a snapshot (kg/hr) at the moment the satellite passed. It is not the
    site's average emission rate for the month.
    """
    # Group by calendar month in UTC, so the result does not depend on the
    # database's time zone setting.
    month = func.date_trunc("month", func.timezone("UTC", Plume.observed_at)).label("month")
    query = (
        select(
            month,
            func.count().label("detections"),
            func.count(Plume.emission_rate_kg_hr).label("quantified"),  # counts non empty rates
            func.avg(Plume.emission_rate_kg_hr).label("mean_rate"),
            func.max(Plume.emission_rate_kg_hr).label("max_rate"),
        )
        .group_by(month)
        .order_by(month)
    )

    reported = None  # the operator's own figure, if we have one
    if facility_id is None:
        rows = (await db.execute(query)).all()
    else:
        facility = (await db.execute(
            select(Facility).where(Facility.id == facility_id))).scalar_one_or_none()
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        reported = facility.epa_reported
        if facility.geom is None:
            rows = []
        else:
            point = select(Facility.geom).where(Facility.id == facility_id).scalar_subquery()
            rows = (await db.execute(query.where(near(point, radius_km)))).all()

    return {
        # These three keep the shape the dashboard chart already expects.
        "dates": [row.month.strftime("%Y-%m") for row in rows],
        "fluxara": [one_decimal(row.mean_rate) for row in rows],
        "epa": [reported for _ in rows],  # repeated only so the chart can draw a line
        # Extra detail.
        "detections": [row.detections for row in rows],
        "quantified": [row.quantified for row in rows],
        "max_rate_kg_hr": [one_decimal(row.max_rate) for row in rows],
        "radius_km": radius_km if facility_id is not None else None,
        "has_data": len(rows) > 0,
        "note": ("Each value is the average of plume rates seen at satellite overpasses "
                 "that month. Months without a detection are left out and do not mean zero emissions."),
    }
