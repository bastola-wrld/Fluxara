# fluxara/api/routes/government.py
"""
Government routes — read-only, full visibility.
No write access. Designed for EPA, EEA, Environment Agency etc.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional

from fluxara.database.connection import get_db
from fluxara.database.models import Facility, Inversion, Alert, Organisation
from fluxara.api.auth import verify_api_key

router = APIRouter(prefix="/government", tags=["Government"])


@router.get("/overview")
async def government_overview(
    country: Optional[str] = Query(None, description="ISO-3 country code filter"),
    sector:  Optional[str] = Query(None, description="Sector name filter"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Full platform stats, filterable by country and sector."""
    q = select(Facility)
    if country:
        q = q.where(Facility.country == country)
    if sector:
        q = q.where(Facility.sector == sector)

    result   = await db.execute(q)
    facilities = result.scalars().all()

    total    = len(facilities)
    high_risk= sum(1 for f in facilities if f.risk_level == "high")

    # Underreporting: satellite (fluxara_latest) > EPA reported by >20%
    underreporting = [
        f for f in facilities
        if f.epa_reported and f.fluxara_latest
        and (f.fluxara_latest - f.epa_reported) / f.epa_reported > 0.20
    ]
    underreport_pct = round(len(underreporting) / total * 100, 1) if total else 0

    total_epa      = sum(f.epa_reported    or 0 for f in facilities)
    total_fluxara  = sum(f.fluxara_latest  or 0 for f in facilities)

    return {
        "total_facilities": total,
        "high_risk": high_risk,
        "underreporting_count": len(underreporting),
        "underreporting_pct": underreport_pct,
        "total_epa_reported_kg_hr": round(total_epa, 2),
        "total_fluxara_kg_hr": round(total_fluxara, 2),
        "discrepancy_kg_hr": round(total_fluxara - total_epa, 2),
        "filter_country": country,
        "filter_sector": sector,
    }


@router.get("/facilities")
async def government_facilities(
    country: Optional[str] = Query(None),
    sector:  Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """All facilities with discrepancy column. Read-only."""
    q = select(Facility)
    if country:
        q = q.where(Facility.country == country)
    if sector:
        q = q.where(Facility.sector == sector)
    q = q.order_by(Facility.name)

    result = await db.execute(q)
    facilities = result.scalars().all()

    return [
        {
            "id": f.id,
            "name": f.name,
            "country": f.country,
            "sector": f.sector,
            "lat": f.lat,
            "lon": f.lon,
            "epa_reported": f.epa_reported,
            "fluxara_latest": f.fluxara_latest,
            "risk_level": f.risk_level,
            "discrepancy_pct": (
                round((f.fluxara_latest - f.epa_reported) / f.epa_reported * 100, 1)
                if f.epa_reported and f.fluxara_latest
                else None
            ),
            "underreporting": (
                f.epa_reported is not None
                and f.fluxara_latest is not None
                and (f.fluxara_latest - f.epa_reported) / f.epa_reported > 0.20
            ),
        }
        for f in facilities
    ]


@router.get("/underreporting")
async def underreporting(
    threshold: float = Query(20.0, description="Underreporting threshold %"),
    country: Optional[str] = Query(None),
    sector:  Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Facilities where satellite > EPA reported by more than `threshold`%."""
    q = select(Facility)
    if country:
        q = q.where(Facility.country == country)
    if sector:
        q = q.where(Facility.sector == sector)

    result = await db.execute(q)
    facilities = result.scalars().all()

    flagged = []
    for f in facilities:
        if f.epa_reported and f.fluxara_latest and f.epa_reported > 0:
            disc = (f.fluxara_latest - f.epa_reported) / f.epa_reported * 100
            if disc > threshold:
                flagged.append({
                    "id": f.id,
                    "name": f.name,
                    "country": f.country,
                    "sector": f.sector,
                    "epa_reported": f.epa_reported,
                    "fluxara_latest": f.fluxara_latest,
                    "discrepancy_pct": round(disc, 1),
                    "risk_level": f.risk_level,
                })

    # Sort by worst discrepancy first
    flagged.sort(key=lambda x: x["discrepancy_pct"], reverse=True)
    return {"threshold_pct": threshold, "count": len(flagged), "facilities": flagged}


@router.get("/ndc-verification")
async def ndc_verification(
    country: str = Query(..., description="ISO-3 country code"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """National totals for Paris Agreement / NDC reporting."""
    result = await db.execute(
        select(Facility).where(Facility.country == country)
    )
    facilities = result.scalars().all()

    sectors: dict = {}
    total_epa = 0.0
    total_fluxara = 0.0

    for f in facilities:
        s = f.sector or "Unknown"
        if s not in sectors:
            sectors[s] = {"epa": 0.0, "fluxara": 0.0, "count": 0}
        sectors[s]["epa"]     += f.epa_reported   or 0
        sectors[s]["fluxara"] += f.fluxara_latest  or 0
        sectors[s]["count"]   += 1
        total_epa     += f.epa_reported   or 0
        total_fluxara += f.fluxara_latest or 0

    return {
        "country": country,
        "total_facilities": len(facilities),
        "total_epa_reported_kg_hr": round(total_epa, 2),
        "total_fluxara_kg_hr": round(total_fluxara, 2),
        "national_discrepancy_kg_hr": round(total_fluxara - total_epa, 2),
        "sector_breakdown": [
            {
                "sector": s,
                "facility_count": v["count"],
                "epa_kg_hr": round(v["epa"], 2),
                "fluxara_kg_hr": round(v["fluxara"], 2),
            }
            for s, v in sorted(sectors.items(), key=lambda x: x[1]["fluxara"], reverse=True)
        ],
    }


@router.get("/sectors")
async def sectors_breakdown(
    country: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Emission breakdown by sector."""
    q = select(Facility)
    if country:
        q = q.where(Facility.country == country)

    result = await db.execute(q)
    facilities = result.scalars().all()

    sectors: dict = {}
    for f in facilities:
        s = f.sector or "Unknown"
        if s not in sectors:
            sectors[s] = {"count": 0, "total_epa": 0.0, "total_fluxara": 0.0, "high_risk": 0}
        sectors[s]["count"]         += 1
        sectors[s]["total_epa"]     += f.epa_reported  or 0
        sectors[s]["total_fluxara"] += f.fluxara_latest or 0
        if f.risk_level == "high":
            sectors[s]["high_risk"] += 1

    return [
        {
            "sector": s,
            "facility_count": v["count"],
            "high_risk": v["high_risk"],
            "total_epa_kg_hr": round(v["total_epa"], 2),
            "total_fluxara_kg_hr": round(v["total_fluxara"], 2),
        }
        for s, v in sorted(sectors.items(), key=lambda x: x[1]["total_fluxara"], reverse=True)
    ]
