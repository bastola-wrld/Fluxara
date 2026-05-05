# fluxara/api/auth_system.py
# New file — replaces simple API key auth

import jwt
import bcrypt
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

SECRET_KEY = "fluxara-secret-2024-change-in-production"
ALGORITHM  = "HS256"
TOKEN_EXPIRE_HOURS = 24

USERS_FILE = Path("../satellite_data/users.json")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ── User models ────────────────────────────────────────
class User(BaseModel):
    username    : str
    email       : str
    role        : str   # "admin" | "customer" | "demo"
    company     : str   = ""
    plan        : str   = "demo"  # "demo"|"starter"|"pro"|"enterprise"
    created_at  : str   = ""
    active      : bool  = True
    api_calls   : int   = 0
    max_calls   : int   = 100

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type  : str
    role        : str
    username    : str
    plan        : str

# ── User database (JSON file — replace with PostgreSQL later) ──
def load_users() -> dict:
    if not USERS_FILE.exists():
        # Create default users
        default_users = {
            "admin": {
                "username"       : "admin",
                "email"          : "admin@fluxara.io",
                "role"           : "admin",
                "company"        : "Fluxara",
                "plan"           : "enterprise",
                "created_at"     : datetime.now().isoformat(),
                "active"         : True,
                "api_calls"      : 0,
                "max_calls"      : 999999,
                "hashed_password": bcrypt.hashpw(
                    b"fluxara-admin-2024",
                    bcrypt.gensalt()
                ).decode(),
            },
            "demo": {
                "username"       : "demo",
                "email"          : "demo@fluxara.io",
                "role"           : "customer",
                "company"        : "Demo Company",
                "plan"           : "demo",
                "created_at"     : datetime.now().isoformat(),
                "active"         : True,
                "api_calls"      : 0,
                "max_calls"      : 100,
                "hashed_password": bcrypt.hashpw(
                    b"demo1234",
                    bcrypt.gensalt()
                ).decode(),
            },
        }
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f, indent=2)
        return default_users

    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(username: str) -> Optional[UserInDB]:
    users = load_users()
    if username in users:
        return UserInDB(**users[username])
    return None

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401,
                                detail="Invalid token")
        user = get_user(username)
        if not user:
            raise HTTPException(status_code=401,
                                detail="User not found")
        if not user.active:
            raise HTTPException(status_code=403,
                                detail="Account disabled")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401,
                            detail="Token expired — please login again")
    except Exception:
        raise HTTPException(status_code=401,
                            detail="Invalid credentials")

def require_admin(user: UserInDB = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403,
                            detail="Admin access required")
    return user

def track_api_call(username: str):
    users = load_users()
    if username in users:
        users[username]["api_calls"] += 1
        save_users(users)