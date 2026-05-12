from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta

from fluxara.database.connection import get_db
from fluxara.database.models import User
from fluxara.api.auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:
        raise HTTPException(status_code=403, detail="Account disabled")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "org_id": user.org_id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "org_id": user.org_id,
        "email": user.email
    }


@router.post("/register")
async def register(
    body: dict,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == body["email"]))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body["email"],
        hashed_password=get_password_hash(body["password"]),
        role=body.get("role", "viewer"),
        company=body.get("company"),
        org_id=body.get("org_id"),
        active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"status": "success", "user_id": user.id}
