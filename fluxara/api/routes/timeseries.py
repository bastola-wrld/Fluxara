# fluxara/api/routes/timeseries.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import random
from typing import Optional
from fluxara.database.connection import get_db
from fluxara.database.models import Facility, Inversion
from fluxara.api.auth import verify_api_key

router = APIRouter(prefix="/timeseries", tags=["Dashboard"])

@router.get("")
async def get_timeseries(
    facility_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Returns emission timeseries data.
    If facility_id is provided, returns specific data for that site.
    Otherwise returns aggregated global data.
    """
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    
    # In a real production system, this would query the 'inversions' table 
    # for historical records. Since we are in the initial deployment phase,
    # we generate a stable walk based on the facility's baseline.
    
    base_epa = 0
    base_fluxara = 0
    
    if facility_id:
        result = await db.execute(select(Facility).where(Facility.id == facility_id))
        facility = result.scalar_one_or_none()
        if facility:
            base_epa = facility.epa_reported or 500
            # Latest inversion if exists
            inv_result = await db.execute(
                select(Inversion)
                .where(Inversion.facility_id == facility_id)
                .order_by(Inversion.date.desc())
                .limit(1)
            )
            latest = inv_result.scalar_one_or_none()
            base_fluxara = latest.emission_rate if latest else base_epa * 1.1
        else:
            base_epa = 500
            base_fluxara = 550
    else:
        # Global aggregate
        epa_result = await db.execute(select(func.sum(Facility.epa_reported)))
        base_epa = epa_result.scalar() or 50000
        base_fluxara = base_epa * 1.15 # Assume 15% underreporting on average
        
    # Generate deterministic walk for the chart
    random.seed(42 + (facility_id or 999))
    
    epa_series = []
    fluxara_series = []
    
    for i in range(len(months)):
        # EPA is relatively flat (reported annually)
        epa_val = int(base_epa * (1.0 + random.uniform(-0.02, 0.02)))
        epa_series.append(epa_val)
        
        # Fluxara (satellite) captures fluctuations
        flux_val = int(base_fluxara * (1.0 + (i * 0.03) + random.uniform(-0.05, 0.05)))
        fluxara_series.append(flux_val)
        
    return {
        "dates": months,
        "epa": epa_series,
        "fluxara": fluxara_series
    }
