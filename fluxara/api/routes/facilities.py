# fluxara/api/routes/facilities.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from fluxara.database.connection import get_db
from fluxara.database.models import Facility, Inversion, Alert
from fluxara.api.schemas import FacilitySchema, AlertSchema, InversionResponse
from fluxara.api.auth import verify_api_key

router = APIRouter(prefix="/facilities", tags=["Facilities"])

@router.get("/", response_model=List[FacilitySchema])
async def get_facilities(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Facility))
    return result.scalars().all()

@router.get("/{id}", response_model=FacilitySchema)
async def get_facility(
    id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Facility).where(Facility.id == id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility

@router.get("/{id}/inversions")
async def get_facility_inversions(
    id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Inversion).where(Inversion.facility_id == id))
    return result.scalars().all()

@router.get("/{id}/alerts", response_model=List[AlertSchema])
async def get_facility_alerts(
    id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Alert).where(Alert.facility_id == id))
    return result.scalars().all()
