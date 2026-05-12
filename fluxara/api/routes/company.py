# fluxara/api/routes/company.py
"""
Company routes — scoped to a single org_id.
All data is filtered so one company cannot see another's data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, date as dt_date

from fluxara.database.connection import get_db
from fluxara.database.models import Organisation, Facility, Inversion, Alert, Report
from fluxara.api.auth import verify_api_key

router = APIRouter(prefix="/company", tags=["Company"])


@router.get("/overview/{org_id}")
async def company_overview(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Stats scoped to a single organisation."""
    facilities = (
        await db.execute(
            select(func.count()).select_from(Facility).where(Facility.org_id == org_id)
        )
    ).scalar()

    high_risk = (
        await db.execute(
            select(func.count()).select_from(Facility)
            .where(Facility.org_id == org_id, Facility.risk_level == "high")
        )
    ).scalar()

    unresolved_alerts = (
        await db.execute(
            select(func.count()).select_from(Alert)
            .join(Facility, Alert.facility_id == Facility.id)
            .where(Facility.org_id == org_id, Alert.resolved == False)
        )
    ).scalar()

    inversions = (
        await db.execute(
            select(func.count()).select_from(Inversion)
            .join(Facility, Inversion.facility_id == Facility.id)
            .where(Facility.org_id == org_id)
        )
    ).scalar()

    return {
        "org_id": org_id,
        "facilities": facilities,
        "high_risk": high_risk,
        "unresolved_alerts": unresolved_alerts,
        "inversions": inversions,
    }


@router.get("/facilities/{org_id}")
async def company_facilities(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(
        select(Facility).where(Facility.org_id == org_id).order_by(Facility.name)
    )
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
            "discrepancy_pct": (
                round(
                    abs((f.fluxara_latest - f.epa_reported) / f.epa_reported) * 100, 1
                )
                if f.epa_reported and f.fluxara_latest
                else None
            ),
            "risk_level": f.risk_level,
        }
        for f in facilities
    ]


@router.post("/facilities/{org_id}")
async def add_facility(
    org_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Verify org exists
    org = (await db.execute(select(Organisation).where(Organisation.id == org_id))).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    facility = Facility(
        name=body["name"],
        lat=body["lat"],
        lon=body["lon"],
        country=body.get("country", "USA"),
        sector=body.get("sector"),
        epa_reported=body.get("epa_reported"),
        org_id=org_id,
        risk_level="medium",
    )
    db.add(facility)
    await db.commit()
    await db.refresh(facility)
    return {"id": facility.id, "name": facility.name}


@router.delete("/facilities/{facility_id}")
async def remove_facility(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Facility).where(Facility.id == facility_id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    await db.delete(facility)
    await db.commit()
    return {"status": "deleted", "id": facility_id}


@router.get("/inversions/{org_id}")
async def company_inversions(
    org_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(
        select(Inversion)
        .join(Facility, Inversion.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
        .order_by(Inversion.created_at.desc())
        .limit(limit)
    )
    invs = result.scalars().all()
    return [
        {
            "id": i.id,
            "facility_id": i.facility_id,
            "date": i.date,
            "emission_rate": i.emission_rate,
            "confidence": i.confidence,
            "uncertainty": i.uncertainty,
            "compute_ms": i.compute_ms,
        }
        for i in invs
    ]


@router.get("/alerts/{org_id}")
async def company_alerts(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(
        select(Alert)
        .join(Facility, Alert.facility_id == Facility.id)
        .where(Facility.org_id == org_id, Alert.resolved == False)
        .order_by(Alert.created_at.desc())
    )
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "facility_id": a.facility_id,
            "severity": a.severity,
            "alert_type": a.alert_type,
            "message": a.message,
            "emission_value": a.emission_value,
            "threshold_value": a.threshold_value,
            "created_at": a.created_at,
        }
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    await db.commit()
    return {"status": "resolved", "id": alert_id}


@router.get("/reports/{org_id}")
async def company_reports(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(
        select(Report)
        .join(Facility, Report.facility_id == Facility.id)
        .where(Facility.org_id == org_id)
        .order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return [
        {
            "id": r.id,
            "facility_id": r.facility_id,
            "report_type": r.report_type,
            "status": r.status,
            "total_emissions": r.total_emissions,
            "pdf_path": r.pdf_path,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.post("/reports/{org_id}/generate")
async def generate_report(
    org_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Trigger MRV report generation for an org's facility."""
    facility_id = body.get("facility_id")
    if not facility_id:
        raise HTTPException(status_code=400, detail="facility_id required")

    report = Report(
        facility_id=facility_id,
        report_type=body.get("report_type", "MRV"),
        date_from=body.get("date_from"),
        date_to=body.get("date_to"),
        status="pending",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return {"id": report.id, "status": "pending", "message": "Report generation queued."}
