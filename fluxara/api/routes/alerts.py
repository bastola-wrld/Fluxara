# fluxara/api/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from datetime import datetime
from fluxara.database.connection import get_db
from fluxara.database.models import Alert, Facility
from fluxara.api.schemas import AlertSchema, AlertCountResponse
from fluxara.api.auth import verify_api_key

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertSchema])
async def get_alerts(
    resolved: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Join with Facility to get facility_name
    query = select(Alert, Facility.name.label("facility_name")).join(Facility).where(Alert.resolved == resolved)
    result = await db.execute(query)
    
    alerts = []
    for row in result:
        alert = row[0]
        alert.facility_name = row[1]
        alerts.append(alert)
    return alerts

@router.get("/count", response_model=AlertCountResponse)
async def get_alert_count(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(func.count()).select_from(Alert).where(Alert.resolved == False))
    return {"unresolved": result.scalar()}

@router.patch("/{id}/resolve", response_model=AlertSchema)
async def resolve_alert(
    id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Alert).where(Alert.id == id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return alert
