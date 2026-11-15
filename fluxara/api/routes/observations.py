# fluxara/api/routes/observations.py
"""
GET /v1/observations  returns every Sentinel 2 check of a facility.

A check that found nothing is as much a result as one that found a plume:
"12 clear images, nothing above 3 t/h" is what a report says for a clean site.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fluxara.api.auth import verify_api_key
from fluxara.database.connection import get_db
from fluxara.database.models import Facility, PlumeDetection, SiteObservation

router = APIRouter(prefix="/observations", tags=["Observations"])

Check = SiteObservation
STATUSES = ["plume_detected", "no_plume", "unusable"]

FIELDS = [
    Check.id, Check.facility_id, Check.observed_at, Check.status, Check.reason,
    Check.method, Check.method_version, Check.usable_fraction,
    Check.detection_limit_kg_hr, Check.wind_speed_10m_ms, Check.wind_from_deg,
    Check.wind_source, Check.distance_to_plume_m, Check.wind_agreement,
    Check.plume_detection_id,
    PlumeDetection.emission_rate_kg_hr, PlumeDetection.emission_uncertainty_kg_hr,
]


@router.get("")
async def list_observations(
    facility_id: int = Query(..., description="The facility to list checks for"),
    status: Optional[str] = Query(None, description="plume_detected, no_plume or unusable"),
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(verify_api_key),
):
    """Checks of one facility, newest first, with a count of each outcome."""
    if status is not None and status not in STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {STATUSES}")
    found = (await db.execute(select(Facility.id).where(Facility.id == facility_id))).first()
    if not found:
        raise HTTPException(status_code=404, detail="Facility not found")

    conditions = [Check.facility_id == facility_id]
    if since:
        conditions.append(Check.observed_at >= since)
    if until:
        conditions.append(Check.observed_at <= until)

    # Count each outcome over the whole period, before the status filter.
    counted = await db.execute(
        select(Check.status, func.count()).where(*conditions).group_by(Check.status))
    counts = {name: 0 for name in STATUSES}
    counts.update({name: number for name, number in counted.all()})

    if status:
        conditions.append(Check.status == status)
    query = (select(*FIELDS)
             .outerjoin(PlumeDetection, PlumeDetection.id == Check.plume_detection_id)
             .where(*conditions))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    page = query.order_by(Check.observed_at.desc(), Check.id.desc()).limit(limit).offset(offset)
    rows = (await db.execute(page)).mappings().all()

    return {"total": total, "limit": limit, "offset": offset,
            "counts": counts, "items": [dict(row) for row in rows]}
