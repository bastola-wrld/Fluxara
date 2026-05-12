# fluxara/api/routes/reports.py
"""
Report endpoints:
  - /reports/manifest         -> list all pre-generated PDFs (instant)
  - /reports/download/facility/{id}  -> instant FileResponse
  - /reports/download/region/{country} -> instant FileResponse
  - /reports/download/company/{org_id} -> instant FileResponse
  - /reports/download/global   -> instant FileResponse
  - /reports/generate          -> admin on-demand generation (stored in DB)
  - /reports/library           -> list DB-stored reports by role
  - /reports/download/{id}     -> download DB-stored report by ID
  - /reports/regenerate        -> admin trigger: re-run auto-generator now
"""
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, date as dt_date, timedelta

from fluxara.database.connection import get_db
from fluxara.database.models import (
    Report, Facility, Inversion, Alert, Organisation, GeneratedReport
)
from fluxara.api.schemas import ReportSchema, GeneratedReportSchema, GenerateReportRequest
from fluxara.api.auth import get_current_user
from fluxara.utils.pdf_generator import (
    generate_facility_pdf, generate_company_pdf,
    generate_summary_pdf, generate_full_pdf, generate_compliance_pdf,
)
from fluxara.reports.auto_generator import (
    get_manifest, get_facility_pdf_path, get_region_pdf_path,
    get_company_pdf_path, get_global_pdf_path,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


# ══════════════════════════════════════════════════════════════════════════════
# PRE-GENERATED PDF DOWNLOADS (FileResponse — instant, zero computation)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/manifest")
async def get_report_manifest(user=Depends(get_current_user)):
    """
    Returns the manifest of all pre-generated PDFs.
    Clients use this to discover available reports.
    """
    manifest = get_manifest()
    if not manifest:
        return {
            "status": "generating",
            "message": "PDFs are being generated. Try again in a few seconds.",
            "facilities": [], "regions": [], "companies": [], "global": None,
        }
    return manifest


@router.get("/download/facility/{facility_id}")
async def download_facility_pdf(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Instant download of a pre-generated facility PDF from disk."""
    # Authorization: company users can only access their own facilities
    if user.role == "company":
        result = await db.execute(select(Facility).where(Facility.id == facility_id))
        facility = result.scalar_one_or_none()
        if not facility or facility.org_id != user.org_id:
            raise HTTPException(status_code=403, detail="Not authorized for this facility")

    path = get_facility_pdf_path(facility_id)
    if not path:
        raise HTTPException(status_code=404, detail="Facility PDF not yet generated. Reports refresh automatically.")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"Fluxara_Facility_{facility_id}.pdf",
    )


@router.get("/download/region/{country}")
async def download_region_pdf(
    country: str,
    user=Depends(get_current_user),
):
    """Instant download of a pre-generated regional summary PDF."""
    path = get_region_pdf_path(country)
    if not path:
        raise HTTPException(status_code=404, detail=f"Region PDF for '{country}' not yet generated.")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"Fluxara_Region_{country}.pdf",
    )


@router.get("/download/company/{org_id}")
async def download_company_pdf(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Instant download of a pre-generated company PDF."""
    # Authorization: company users can only download their own org report
    if user.role == "company" and user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")

    path = get_company_pdf_path(org_id)
    if not path:
        raise HTTPException(status_code=404, detail="Company PDF not yet generated.")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"Fluxara_Company_{org_id}.pdf",
    )


@router.get("/download/global")
async def download_global_pdf(user=Depends(get_current_user)):
    """Instant download of the global intelligence summary PDF."""
    path = get_global_pdf_path()
    if not path:
        raise HTTPException(status_code=404, detail="Global PDF not yet generated.")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename="Fluxara_Global_Summary.pdf",
    )


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN: TRIGGER REGENERATION
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/regenerate")
async def trigger_regeneration(user=Depends(get_current_user)):
    """Admin-only: Trigger an immediate regeneration of all PDFs."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    import asyncio
    from fluxara.reports.auto_generator import generate_all_reports
    asyncio.create_task(generate_all_reports())

    return {"status": "started", "message": "PDF regeneration started in background. Check /health for progress."}


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN: ON-DEMAND CUSTOM PDF GENERATION (stored in DB)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/generate", response_model=GeneratedReportSchema)
async def generate_on_demand_report(
    body: GenerateReportRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Admin-only: Generate a custom PDF report with specific filters.
    Stores the PDF binary in the generated_reports table.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can generate reports")

    if body.report_type not in ("summary", "full", "compliance"):
        raise HTTPException(status_code=400, detail="report_type must be: summary, full, compliance")

    # Build facility query with filters
    q = select(Facility)
    if body.region and body.region != "Global":
        q = q.where(Facility.country == body.region)
    if body.org_id:
        q = q.where(Facility.org_id == body.org_id)
    if body.facility_id:
        q = q.where(Facility.id == body.facility_id)

    result = await db.execute(q.order_by(Facility.name))
    facilities_orm = result.scalars().all()

    if not facilities_orm:
        raise HTTPException(status_code=404, detail="No facilities found for the given filters")

    facilities = [
        {
            "name": f.name, "country": f.country, "sector": f.sector,
            "lat": f.lat, "lon": f.lon, "epa_reported": f.epa_reported,
            "fluxara_latest": f.fluxara_latest, "risk_level": f.risk_level,
        }
        for f in facilities_orm
    ]

    facility_ids = [f.id for f in facilities_orm]

    # Compute statistics
    total_emissions = sum(f.get('fluxara_latest', 0) or 0 for f in facilities)
    total_epa = sum(f.get('epa_reported', 0) or 0 for f in facilities)
    high_risk = sum(1 for f in facilities if (f.get('risk_level') or '').lower() == 'high')
    underreporting = [
        f for f in facilities
        if (f.get('epa_reported') or 0) > 0 and (f.get('fluxara_latest') or 0) > 0
        and ((f['fluxara_latest'] - f['epa_reported']) / f['epa_reported']) > 0.20
    ]
    underreporting_pct = round(len(underreporting) / len(facilities) * 100, 1) if facilities else 0

    stats = {
        "total_facilities": len(facilities),
        "total_emissions": total_emissions,
        "total_epa": total_epa,
        "high_risk": high_risk,
        "underreporting_pct": underreporting_pct,
        "region": body.region or "Global",
        "date_from": str(body.date_from) if body.date_from else "All time",
        "date_to": str(body.date_to) if body.date_to else "Present",
    }

    region_label = body.region or "Global"
    type_label = body.report_type.capitalize()
    date_label = datetime.utcnow().strftime("%B %Y")
    title = f"Fluxara {type_label} Report - {region_label} - {date_label}"

    # Generate PDF based on type
    if body.report_type == "summary":
        pdf_bytes = generate_summary_pdf(title, facilities, stats)
    elif body.report_type == "full":
        inv_q = select(Inversion).where(Inversion.facility_id.in_(facility_ids))
        if body.date_from:
            inv_q = inv_q.where(Inversion.date >= body.date_from)
        if body.date_to:
            inv_q = inv_q.where(Inversion.date <= body.date_to)
        inv_result = await db.execute(inv_q.order_by(Inversion.date.desc()))
        inversions = [
            {"date": i.date, "facility_id": i.facility_id,
             "emission_rate": i.emission_rate, "confidence": i.confidence}
            for i in inv_result.scalars().all()
        ]

        alert_q = select(Alert).where(
            Alert.facility_id.in_(facility_ids), Alert.resolved == False
        ).order_by(Alert.created_at.desc())
        alerts = [
            {"severity": a.severity, "message": a.message,
             "facility_id": a.facility_id, "created_at": a.created_at.isoformat() if a.created_at else ""}
            for a in (await db.execute(alert_q)).scalars().all()
        ]

        pdf_bytes = generate_full_pdf(title, facilities, inversions, alerts)
    elif body.report_type == "compliance":
        pdf_bytes = generate_compliance_pdf(title, facilities, stats)

    # Store in database
    report = GeneratedReport(
        title=title,
        report_type=body.report_type,
        region=body.region,
        org_id=body.org_id,
        facility_id=body.facility_id,
        date_from=body.date_from,
        date_to=body.date_to,
        total_facilities=len(facilities),
        total_emissions=round(total_emissions, 2),
        pdf_data=pdf_bytes,
        file_size=len(pdf_bytes),
        generated_by=user.id if user.id else None,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    return report


# ══════════════════════════════════════════════════════════════════════════════
# REPORT LIBRARY (DB-stored reports, role-filtered)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/library", response_model=List[GeneratedReportSchema])
async def get_report_library(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    List generated reports visible to the current user.
    Admin: all | Company: own org | Government: own country + global
    """
    q = select(GeneratedReport).order_by(GeneratedReport.created_at.desc())

    if user.role == "admin":
        pass
    elif user.role == "company":
        q = q.where(GeneratedReport.org_id == user.org_id)
    elif user.role == "government":
        org_result = await db.execute(
            select(Organisation).where(Organisation.id == user.org_id)
        )
        org = org_result.scalar_one_or_none()
        user_country = org.country if org else None
        q = q.where(
            or_(
                GeneratedReport.region == user_country,
                GeneratedReport.region == "Global",
                GeneratedReport.region.is_(None),
            )
        )
    else:
        q = q.where(GeneratedReport.region == "Global")

    result = await db.execute(q)
    return result.scalars().all()


@router.get("/download/{report_id}")
async def download_generated_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Download a DB-stored generated report by ID."""
    result = await db.execute(
        select(GeneratedReport).where(GeneratedReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if user.role == "company" and report.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Not authorized for this report")

    safe_title = report.title.replace(" ", "_").replace("—", "-")[:60]
    return Response(
        content=report.pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Fluxara_{safe_title}.pdf"'},
    )


@router.delete("/generated/{report_id}")
async def delete_generated_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Admin-only: Delete a DB-stored generated report."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    result = await db.execute(
        select(GeneratedReport).where(GeneratedReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.delete(report)
    return {"status": "deleted", "id": report_id}


# ══════════════════════════════════════════════════════════════════════════════
# LEGACY LIVE-GENERATION ENDPOINTS (kept for backward compat, now also serves
# pre-generated files when available for instant response)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/facility/{facility_id}/pdf")
async def get_facility_report_pdf(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Download facility PDF — serves pre-generated file if available, else generates live."""
    # Try pre-generated first (instant)
    path = get_facility_pdf_path(facility_id)
    if path:
        # Still check authorization
        if user.role == "company":
            result = await db.execute(select(Facility).where(Facility.id == facility_id))
            facility = result.scalar_one_or_none()
            if not facility or facility.org_id != user.org_id:
                raise HTTPException(status_code=403, detail="Not authorized for this facility")
        return FileResponse(
            path=str(path),
            media_type="application/pdf",
            filename=f"Fluxara_Facility_{facility_id}.pdf",
        )

    # Fallback: generate live
    result = await db.execute(select(Facility).where(Facility.id == facility_id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    if user.role != "admin" and facility.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Not authorized for this facility")

    inv_res = await db.execute(
        select(Inversion).where(Inversion.facility_id == facility_id).order_by(Inversion.date.desc())
    )
    inversions = inv_res.scalars().all()

    alert_res = await db.execute(
        select(Alert).where(Alert.facility_id == facility_id).order_by(Alert.created_at.desc())
    )
    alerts = alert_res.scalars().all()

    f_dict = {
        "name": facility.name, "country": facility.country, "sector": facility.sector,
        "lat": facility.lat, "lon": facility.lon, "fluxara_latest": facility.fluxara_latest,
        "risk_level": facility.risk_level
    }
    inv_list = [{"date": str(i.date), "emission_rate": i.emission_rate, "confidence": i.confidence} for i in inversions]
    alert_list = [{"severity": a.severity, "message": a.message, "created_at": a.created_at.isoformat()} for a in alerts]

    pdf_bytes = generate_facility_pdf(f_dict, inv_list, alert_list)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Fluxara_Facility_{facility_id}.pdf"}
    )


@router.get("/company/{org_id}/pdf")
async def get_company_report_pdf(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Download company PDF — serves pre-generated file if available, else generates live."""
    if user.role != "admin" and user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Try pre-generated first (instant)
    path = get_company_pdf_path(org_id)
    if path:
        return FileResponse(
            path=str(path),
            media_type="application/pdf",
            filename=f"Fluxara_Corporate_{org_id}.pdf",
        )

    # Fallback: generate live
    org_res = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    fac_res = await db.execute(select(Facility).where(Facility.org_id == org_id))
    facilities = fac_res.scalars().all()

    total_emissions = sum(f.fluxara_latest or 0 for f in facilities)

    alert_count_res = await db.execute(
        select(Alert).join(Facility).where(Facility.org_id == org_id, Alert.resolved == False)
    )
    total_alerts = len(alert_count_res.scalars().all())

    org_dict = {"name": org.name}
    fac_list = [{"name": f.name, "fluxara_latest": f.fluxara_latest, "risk_level": f.risk_level, "country": f.country} for f in facilities]

    pdf_bytes = generate_company_pdf(org_dict, fac_list, total_emissions, total_alerts)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Fluxara_Corporate_{org_id}.pdf"}
    )


# ── Legacy list endpoint ──────────────────────────────────────────────────
@router.get("/", response_model=List[ReportSchema])
async def get_reports(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    query = select(Report, Facility.name.label("facility_name")).join(Facility)
    result = await db.execute(query)

    reports = []
    for row in result:
        report = row[0]
        report.facility_name = row[1]
        reports.append(report)
    return reports
