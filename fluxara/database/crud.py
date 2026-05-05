# fluxara/database/crud.py
from datetime import datetime
from sqlalchemy.orm import Session
from fluxara.database.models import User, ApiKey, Facility, InversionResult

# ── Users ─────────────────────────────────────────────────────────────────────
def create_user(db: Session, name: str, email: str, org: str = None):
    user = User(name=name, email=email, org=org)
    db.add(user); db.commit(); db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_all_users(db: Session):
    return db.query(User).all()

# ── API Keys ──────────────────────────────────────────────────────────────────
def create_api_key(db: Session, key: str, name: str, user_id: int, permissions: str = "read"):
    api_key = ApiKey(key=key, name=name, user_id=user_id, permissions=permissions)
    db.add(api_key); db.commit(); db.refresh(api_key)
    return api_key

def get_api_key(db: Session, key: str):
    return db.query(ApiKey).filter(ApiKey.key == key, ApiKey.is_active == True).first()

def update_api_key_last_used(db: Session, key: str):
    api_key = get_api_key(db, key)
    if api_key:
        api_key.last_used = datetime.utcnow()
        db.commit()

# ── Facilities ────────────────────────────────────────────────────────────────
def create_facility(db: Session, name: str, lat: float, lon: float,
                    operator: str = None, state: str = None,
                    epa_reported_kgh: float = None, risk_level: str = "unknown"):
    f = Facility(name=name, lat=lat, lon=lon, operator=operator,
                 state=state, epa_reported_kgh=epa_reported_kgh, risk_level=risk_level)
    db.add(f); db.commit(); db.refresh(f)
    return f

def get_all_facilities(db: Session):
    return db.query(Facility).all()

def get_facility_by_name(db: Session, name: str):
    return db.query(Facility).filter(Facility.name.ilike(f"%{name}%")).first()

# ── Inversion Results ─────────────────────────────────────────────────────────
def save_inversion(db: Session, data: dict, user_id: int = None, facility_id: int = None):
    result = InversionResult(
        user_id             = user_id,
        facility_id         = facility_id,
        latitude            = data["latitude"],
        longitude           = data["longitude"],
        date                = data["date"],
        bbox_deg            = data.get("bbox_deg", 2.0),
        emission_rate_kg_hr = data.get("emission_rate_kg_hr"),
        emission_rate_t_yr  = data.get("emission_rate_t_yr"),
        anomaly_ppb         = data.get("anomaly_ppb"),
        uncertainty_1sigma  = data.get("uncertainty_1sigma"),
        confidence          = data.get("confidence"),
        compute_time_ms     = data.get("compute_time_ms"),
        top_facility        = data.get("top_facility"),
    )
    db.add(result); db.commit(); db.refresh(result)
    return result

def get_recent_inversions(db: Session, limit: int = 50):
    return db.query(InversionResult).order_by(
        InversionResult.created_at.desc()).limit(limit).all()

def get_inversions_by_facility(db: Session, facility_id: int):
    return db.query(InversionResult).filter(
        InversionResult.facility_id == facility_id).all()