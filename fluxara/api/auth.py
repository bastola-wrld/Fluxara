# fluxara/api/auth.py
import os
from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.status import HTTP_401_UNAUTHORIZED
from fluxara.database.connection import get_db
from fluxara.database.models import User

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Dev key bypass — set in .env as FLUXARA_DEV_KEY
DEV_KEY = os.getenv("FLUXARA_DEV_KEY", "fluxara-dev-key-2024")


async def verify_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
):
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API Key missing. Use header: X-API-Key: fluxara-dev-key-2024"
        )

    # ── Dev key bypass (no DB required) ──────────────────────────────────────
    if api_key == DEV_KEY:
        return api_key

    # ── Validate against database ─────────────────────────────────────────────
    try:
        result = await db.execute(select(User).where(User.api_key == api_key))
        user = result.scalar_one_or_none()
        if user:
            return api_key
    except Exception:
        pass

    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key"
    )