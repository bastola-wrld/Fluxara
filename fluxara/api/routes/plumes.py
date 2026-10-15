# fluxara/api/routes/plumes.py
"""
GET /v1/plumes  returns real satellite plume detections.

Every plume comes with its source, licence and credit line, so a report can
always say where a number came from and whether we may sell it.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fluxara.api.auth import verify_api_key
from fluxara.database.connection import get_db
from fluxara.database.models import Facility, PlumeDetection

router = APIRouter(prefix="/plumes", tags=["Plumes"])

Plume = PlumeDetection

# The fields we send back for each plume.
PLUME_FIELDS = [
    Plume.id, Plume.source, Plume.source_id, Plume.instrument, Plume.product,
    Plume.product_version, Plume.gas, Plume.observed_at,
    func.ST_Y(Plume.geom).label("lat"),   # ST_Y is latitude
    func.ST_X(Plume.geom).label("lon"),   # ST_X is longitude
    Plume.geom_kind,
    Plume.emission_rate_kg_hr, Plume.emission_uncertainty_kg_hr, Plume.max_enhancement_ppm_m,
    Plume.wind_speed_ms, Plume.wind_source, Plume.cloud_cover_pct,
    Plume.licence, Plume.attribution, Plume.commercial_use_allowed, Plume.source_url,
]


def near(point, radius_km):
    """
    True for plumes within radius_km of point.
    Casting to Geography makes PostGIS measure real metres on the Earth's
    surface instead of degrees.
    """
    return func.ST_DWithin(cast(Plume.geom, Geography), cast(point, Geography), radius_km * 1000)


def distance_km(point):
    return func.ST_Distance(cast(Plume.geom, Geography), cast(point, Geography)) / 1000


async def facility_location(db, facility_id):
    """The facility's point as a small SQL query, or an HTTP error if there is none."""
    facility = (await db.execute(
        select(Facility.id, Facility.geom).where(Facility.id == facility_id))).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    if facility.geom is None:
        raise HTTPException(status_code=422, detail="Facility has no valid location")
    return select(Facility.geom).where(Facility.id == facility_id).scalar_subquery()


@router.get("")
async def list_plumes(
    facility_id: Optional[int] = Query(None, description="Only plumes near this facility"),
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lon: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: float = Query(5.0, gt=0, le=200),
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    quantified_only: bool = Query(False, description="Only plumes with an emission rate"),
    commercial_only: bool = Query(False, description="Only data we are allowed to sell"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(verify_api_key),
):
    """
    Plumes, newest first. Give facility_id, or lat and lon, to search around
    a point. A plume being near a facility does not prove the facility caused
    it: distance_km is a fact, deciding the source is a judgement.
    """
    # 1. Work out the centre point, if one was asked for.
    point = None
    if facility_id is not None:
        point = await facility_location(db, facility_id)
    elif lat is not None and lon is not None:
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    elif lat is not None or lon is not None:
        raise HTTPException(status_code=422, detail="Give both lat and lon")

    # 2. Build the query step by step.
    if point is None:
        query = select(*PLUME_FIELDS)
    else:
        query = select(*PLUME_FIELDS, distance_km(point).label("distance_km"))
        query = query.where(near(point, radius_km))
    if since:
        query = query.where(Plume.observed_at >= since)
    if until:
        query = query.where(Plume.observed_at <= until)
    if quantified_only:
        query = query.where(Plume.emission_rate_kg_hr.isnot(None))
    if commercial_only:
        query = query.where(Plume.commercial_use_allowed.is_(True))

    # 3. Count everything that matches, then fetch one page of it.
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    page = query.order_by(Plume.observed_at.desc(), Plume.id.desc()).limit(limit).offset(offset)
    rows = (await db.execute(page)).mappings().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(row) for row in rows],
    }
