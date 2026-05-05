# fluxara/api/schemas.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, date

# ── Inversion ──────────────────────────────────────────
class InversionRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    date: date  # Pydantic handles YYYY-MM-DD strings automatically
    bbox_deg: float = 2.0

class InversionResponse(BaseModel):
    top_facility: str
    emission_rate_kg_hr: float
    uncertainty_1sigma: float
    confidence: float
    compute_time_ms: int

# ── Facility ──────────────────────────────────────────
class FacilitySchema(BaseModel):
    id: int
    name: str
    state: Optional[str]
    country: Optional[str]
    lat: float
    lon: float
    epa_reported: Optional[float]
    fluxara_latest: Optional[float]
    risk_level: Optional[str]
    sector: Optional[str]
    ghgrp_id: Optional[str]

    class Config:
        from_attributes = True

# ── Alert ──────────────────────────────────────────
class AlertSchema(BaseModel):
    id: int
    facility_id: int
    facility_name: Optional[str] = None
    alert_type: str
    severity: str
    message: str
    emission_value: Optional[float]
    threshold_value: Optional[float]
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlertCountResponse(BaseModel):
    unresolved: int

# ── Report ──────────────────────────────────────────
class ReportSchema(BaseModel):
    id: int
    facility_id: int
    facility_name: Optional[str] = None
    report_type: str
    date_from: Optional[date]
    date_to: Optional[date]
    total_emissions: Optional[float]
    status: str
    pdf_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ── User ──────────────────────────────────────────
class UserSchema(BaseModel):
    id: int
    email: EmailStr
    company: Optional[str]
    role: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
