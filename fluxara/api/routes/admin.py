# fluxara/api/routes/admin.py
"""
Admin routes — full platform access.
All endpoints require role=admin via API key lookup.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date

from fluxara.database.connection import get_db
from fluxara.database.models import Organisation, User, Facility, Inversion, Alert
from fluxara.api.auth import verify_api_key

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/overview")
async def admin_overview(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Total counts across the entire platform."""
    orgs      = (await db.execute(select(func.count()).select_from(Organisation))).scalar()
    users     = (await db.execute(select(func.count()).select_from(User))).scalar()
    facilities= (await db.execute(select(func.count()).select_from(Facility))).scalar()
    inversions= (await db.execute(select(func.count()).select_from(Inversion))).scalar()
    alerts    = (await db.execute(select(func.count()).select_from(Alert).where(Alert.resolved == False))).scalar()
    return {
        "organisations": orgs,
        "users": users,
        "facilities": facilities,
        "inversions": inversions,
        "unresolved_alerts": alerts,
        "api_calls_today": 0,  # stub — wire to audit log later
    }


@router.get("/organisations")
async def list_organisations(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Organisation).order_by(Organisation.created_at.desc()))
    orgs = result.scalars().all()
    return [
        {
            "id": o.id,
            "name": o.name,
            "org_type": o.org_type,
            "plan": o.plan,
            "active": o.active,
            "country": o.country,
            "created_at": o.created_at,
        }
        for o in orgs
    ]


@router.post("/organisations")
async def create_organisation(
    body: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    org = Organisation(
        name=body["name"],
        org_type=body.get("org_type", "company"),
        plan=body.get("plan", "free"),
        country=body.get("country"),
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return {"id": org.id, "name": org.name, "org_type": org.org_type, "country": org.country}


@router.delete("/organisations/{org_id}")
async def disable_organisation(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    org.active = False
    await db.commit()
    return {"status": "disabled", "id": org_id}


@router.delete("/organisations/{org_id}/hard")
async def hard_delete_organisation(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    await db.delete(org)
    await db.commit()
    return {"status": "deleted", "id": org_id}


@router.post("/users")
async def create_user(
    body: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    user = User(
        email=body["email"],
        role=body.get("role", "viewer"),
        org_id=body.get("org_id"),
        company=body.get("company"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role, "org_id": user.org_id}


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "org_id": u.org_id,
            "active": getattr(u, "active", True),
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/role/{role}")
async def change_user_role(
    user_id: int,
    role: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    allowed = {"admin", "company", "government", "viewer"}
    if role not in allowed:
        raise HTTPException(status_code=400, detail=f"Role must be one of {allowed}")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    await db.commit()
    return {"status": "success", "id": user_id, "new_role": role}


@router.delete("/users/{user_id}")
async def disable_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.active = False
    await db.commit()
    return {"status": "disabled", "id": user_id}


@router.delete("/users/{user_id}/hard")
async def hard_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"status": "deleted", "id": user_id}


@router.get("/inversions")
async def admin_inversions(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(
        select(Inversion).order_by(Inversion.created_at.desc()).limit(limit)
    )
    invs = result.scalars().all()
    return [
        {
            "id": i.id,
            "facility_id": i.facility_id,
            "date": i.date,
            "emission_rate": i.emission_rate,
            "confidence": i.confidence,
            "compute_ms": i.compute_ms,
        }
        for i in invs
    ]


@router.get("/alerts")
async def admin_alerts(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(
        select(Alert).where(Alert.resolved == False).order_by(Alert.created_at.desc())
    )
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "facility_id": a.facility_id,
            "severity": a.severity,
            "message": a.message,
            "created_at": a.created_at,
        }
        for a in alerts
    ]


@router.post("/inversions")
async def create_inversion(
    body: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    inv = Inversion(
        facility_id=body["facility_id"],
        emission_rate=body["emission_rate"],
        confidence=body["confidence"],
        date=date.fromisoformat(body.get("date", date.today().isoformat())),
        compute_ms=body.get("compute_ms", 0)
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return inv


@router.delete("/inversions/{inv_id}")
async def delete_inversion(
    inv_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Inversion).where(Inversion.id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Inversion not found")
    await db.delete(inv)
    await db.commit()
    return {"status": "deleted", "id": inv_id}


@router.post("/alerts")
async def create_alert(
    body: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    alert = Alert(
        facility_id=body["facility_id"],
        severity=body["severity"],
        message=body["message"],
        alert_type=body.get("alert_type", "manual"),
        resolved=False
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
    return {"status": "deleted", "id": alert_id}
