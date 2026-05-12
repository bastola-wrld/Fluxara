# FIX #3 — fluxara/api/schemas.py
# Problems:
#   a) routes.py (legacy) returns extra fields not in InversionResponse
#   b) Pydantic v2 deprecation: class Config → model_config = ConfigDict(...)
# Apply by replacing fluxara/api/schemas.py with this file.

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, date


# ── Inversion ──────────────────────────────────────────────────────────────

class InversionRequest(BaseModel):
    latitude:  float = Field(..., ge=-90,  le=90)
    longitude: float = Field(..., ge=-180, le=180)
    date:      date                             # Pydantic handles YYYY-MM-DD
    bbox_deg:  float = Field(2.0, gt=0, le=10)


class InversionResponse(BaseModel):
    """
    Core response — matches routes/invert.py exactly.
    All fields are required; no optional surprises.
    """
    top_facility:        str
    emission_rate_kg_hr: float
    uncertainty_1sigma:  float
    confidence:          float
    compute_time_ms:     int


# ── Facility ───────────────────────────────────────────────────────────────

class FacilitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # replaces class Config

    id:              int
    name:            str
    state:           Optional[str]   = None
    country:         Optional[str]   = None
    lat:             float
    lon:             float
    epa_reported:    Optional[float] = None
    fluxara_latest:  Optional[float] = None
    risk_level:      Optional[str]   = None
    sector:          Optional[str]   = None
    ghgrp_id:        Optional[str]   = None


# ── Alert ──────────────────────────────────────────────────────────────────

class AlertSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:               int
    facility_id:      int
    facility_name:    Optional[str]   = None
    alert_type:       str
    severity:         str
    message:          str
    emission_value:   Optional[float] = None
    threshold_value:  Optional[float] = None
    resolved:         bool
    created_at:       datetime


class AlertCountResponse(BaseModel):
    unresolved: int


# ── Report ──────────────────────────────────────────────────────────────────

class ReportSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:               int
    facility_id:      int
    facility_name:    Optional[str]   = None
    report_type:      str
    date_from:        Optional[date]  = None
    date_to:          Optional[date]  = None
    total_emissions:  Optional[float] = None
    status:           str
    pdf_path:         Optional[str]   = None
    created_at:       datetime


class GeneratedReportSchema(BaseModel):
    """Metadata-only schema for listing generated reports (excludes pdf_data binary)."""
    model_config = ConfigDict(from_attributes=True)

    id:               int
    title:            str
    report_type:      str
    region:           Optional[str]   = None
    org_id:           Optional[int]   = None
    facility_id:      Optional[int]   = None
    date_from:        Optional[date]  = None
    date_to:          Optional[date]  = None
    total_facilities: Optional[int]   = None
    total_emissions:  Optional[float] = None
    file_size:        Optional[int]   = None
    generated_by:     Optional[int]   = None
    created_at:       datetime


class GenerateReportRequest(BaseModel):
    """Request body for admin PDF generation."""
    report_type:  str = Field(..., description="summary | full | compliance")
    region:       Optional[str]  = Field(None, description="Country code or 'Global'")
    org_id:       Optional[int]  = Field(None, description="Scope to one organisation")
    facility_id:  Optional[int]  = Field(None, description="Scope to one facility")
    date_from:    Optional[date] = None
    date_to:      Optional[date] = None


# ── User ───────────────────────────────────────────────────────────────────

class UserSchema(BaseModel):
    id:         int
    email:      str
    company:    Optional[str] = None
    role:       str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type:   str