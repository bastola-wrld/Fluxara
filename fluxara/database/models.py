# fluxara/database/models.py
import os
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, Boolean,
                        DateTime, ForeignKey, Text, Date)
from sqlalchemy.orm import relationship
from fluxara.database.connection import Base

# Only import GeoAlchemy2 if PostGIS is available
USE_POSTGIS = os.getenv("USE_POSTGIS", "false").lower() == "true"

if USE_POSTGIS:
    from geoalchemy2 import Geography
    location_col = lambda: Column(Geography(geometry_type='POINT', srid=4326))
else:
    location_col = lambda: None


class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String(255), unique=True, nullable=False, index=True)
    company    = Column(String(255))
    role       = Column(String(20), default="viewer")
    api_key    = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Facility(Base):
    __tablename__ = "facilities"
    id               = Column(Integer, primary_key=True, index=True)
    name             = Column(String(255), nullable=False)
    state            = Column(String(2))
    country          = Column(String(3), default="USA")
    lat              = Column(Float, nullable=False)
    lon              = Column(Float, nullable=False)
    epa_reported     = Column(Float)
    fluxara_latest   = Column(Float)
    risk_level       = Column(String(10))
    sector           = Column(String(50))
    ghgrp_id         = Column(String(50))
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inversions = relationship("Inversion", back_populates="facility")
    alerts     = relationship("Alert", back_populates="facility")
    reports    = relationship("Report", back_populates="facility")


class Inversion(Base):
    __tablename__ = "inversions"
    id              = Column(Integer, primary_key=True, index=True)
    facility_id     = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    latitude        = Column(Float)
    longitude       = Column(Float)
    date            = Column(Date, nullable=False)
    emission_rate   = Column(Float)
    uncertainty     = Column(Float)
    confidence      = Column(Float)
    compute_ms      = Column(Integer)
    tropomi_file    = Column(String(255))
    era5_file       = Column(String(255))
    created_at      = Column(DateTime, default=datetime.utcnow)

    facility = relationship("Facility", back_populates="inversions")


class Alert(Base):
    __tablename__ = "alerts"
    id              = Column(Integer, primary_key=True, index=True)
    facility_id     = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    alert_type      = Column(String(50))
    severity        = Column(String(10))
    message         = Column(Text)
    emission_value  = Column(Float)
    threshold_value = Column(Float)
    resolved        = Column(Boolean, default=False)
    resolved_at     = Column(DateTime)
    created_at      = Column(DateTime, default=datetime.utcnow)

    facility = relationship("Facility", back_populates="alerts")


class Report(Base):
    __tablename__ = "reports"
    id              = Column(Integer, primary_key=True, index=True)
    facility_id     = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    report_type     = Column(String(50))
    date_from       = Column(Date)
    date_to         = Column(Date)
    total_emissions = Column(Float)
    status          = Column(String(20), default="pending")
    pdf_path        = Column(String(255))
    created_at      = Column(DateTime, default=datetime.utcnow)

    facility = relationship("Facility", back_populates="reports")