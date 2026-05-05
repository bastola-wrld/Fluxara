# fluxara/api/routes/reports.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from fluxara.database.connection import get_db
from fluxara.database.models import Report, Facility
from fluxara.api.schemas import ReportSchema
from fluxara.api.auth import verify_api_key

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/", response_model=List[ReportSchema])
async def get_reports(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = select(Report, Facility.name.label("facility_name")).join(Facility)
    result = await db.execute(query)
    
    reports = []
    for row in result:
        report = row[0]
        report.facility_name = row[1]
        reports.append(report)
    return reports

@router.get("/{id}", response_model=ReportSchema)
async def get_report(
    id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = select(Report, Facility.name.label("facility_name")).join(Facility).where(Report.id == id)
    result = await db.execute(query)
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = row[0]
    report.facility_name = row[1]
    return report

@router.get("/{id}/download")
async def download_report(
    id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Stub for PDF download
    return {"message": "Download stub for report", "id": id, "pdf_url": f"/static/reports/report_{id}.pdf"}
