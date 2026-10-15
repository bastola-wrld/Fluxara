# fluxara/database/models.py
"""
ORM models.

Schema changes go through Alembic (see migrations/). Do not rely on
Base.metadata.create_all() outside of tests.

Spatial columns use PostGIS geometry in SRID 4326 (WGS84 lon/lat).
PostGIS is required.
"""
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (Column, Integer, BigInteger, String, Float, Boolean,
                        DateTime, ForeignKey, Text, Date, LargeBinary, Index,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from fluxara.database.connection import Base

SRID = 4326


def utcnow():
    return datetime.now(timezone.utc)


class Organisation(Base):
    __tablename__ = "organisations"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False, unique=True)
    org_type   = Column(String(20), nullable=False)   # "company" | "government" | "admin"
    plan       = Column(String(20), default="free")   # "free" | "pro" | "enterprise"
    country    = Column(String(50), nullable=True)
    active     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users      = relationship("User", back_populates="organisation")
    facilities = relationship("Facility", back_populates="organisation")


class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String(255), unique=True, nullable=False, index=True)
    company    = Column(String(255))
    role       = Column(String(20), default="viewer")  # "admin" | "company" | "government" | "viewer"
    api_key    = Column(String(64), unique=True, index=True)
    hashed_password = Column(String(255))
    org_id     = Column(Integer, ForeignKey("organisations.id"), nullable=True)
    active     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organisation = relationship("Organisation", back_populates="users")


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
    # Kept in sync with lat/lon by the facilities_set_geom database trigger.
    geom             = Column(Geometry("POINT", srid=SRID, spatial_index=False))
    # Where this record came from, e.g. "manual_unverified", "epa_ghgrp_2023".
    data_source      = Column(String(50), nullable=False, server_default="manual_unverified")
    org_id           = Column(Integer, ForeignKey("organisations.id"), nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inversions   = relationship("Inversion", back_populates="facility")
    alerts       = relationship("Alert", back_populates="facility")
    reports      = relationship("Report", back_populates="facility")
    organisation = relationship("Organisation", back_populates="facilities")

    __table_args__ = (
        Index("ix_facilities_geom", "geom", postgresql_using="gist"),
    )


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


class GeneratedReport(Base):
    """Admin-generated PDF reports stored with binary content for instant client download."""
    __tablename__ = "generated_reports"
    id               = Column(Integer, primary_key=True, index=True)
    title            = Column(String(255), nullable=False)
    report_type      = Column(String(50), nullable=False)   # summary / full / compliance
    region           = Column(String(100))                   # country code or "Global"
    org_id           = Column(Integer, ForeignKey("organisations.id"), nullable=True)
    facility_id      = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    date_from        = Column(Date)
    date_to          = Column(Date)
    total_facilities = Column(Integer)
    total_emissions  = Column(Float)
    pdf_data         = Column(LargeBinary, nullable=False)
    file_size        = Column(Integer)                       # bytes
    generated_by     = Column(Integer, ForeignKey("users.id"))
    created_at       = Column(DateTime, default=datetime.utcnow)

    organisation = relationship("Organisation")
    facility     = relationship("Facility")
    generator    = relationship("User")


# ── Satellite data (real observations only) ──────────────────────────────────

class IngestionRun(Base):
    """One execution of an ingestion job. Every ingested row points back here."""
    __tablename__ = "ingestion_runs"
    id           = Column(Integer, primary_key=True)
    source       = Column(String(50), nullable=False, index=True)
    status       = Column(String(20), nullable=False, default="running")  # running | success | failed
    params       = Column(JSONB, nullable=False, default=dict)
    code_version = Column(String(64))
    n_fetched    = Column(Integer, nullable=False, default=0)
    n_inserted   = Column(Integer, nullable=False, default=0)
    n_updated    = Column(Integer, nullable=False, default=0)
    error        = Column(Text)
    started_at   = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at  = Column(DateTime(timezone=True))


class PlumeDetection(Base):
    """
    A methane plume observed by a satellite instrument.

    One row per (source, source_id). Re-ingesting the same plume updates the
    row in place, so jobs are safe to rerun.

    emission_rate_kg_hr is NULL when the provider did not quantify the plume.
    It is never filled with an estimate of our own in this table.
    """
    __tablename__ = "plume_detections"
    id          = Column(BigInteger, primary_key=True)

    # Identity and provenance
    source            = Column(String(50), nullable=False)    # e.g. "nasa_emit"
    source_id         = Column(String(255), nullable=False)   # provider's granule or plume id
    instrument        = Column(String(50), nullable=False)    # e.g. "EMIT"
    product           = Column(String(100))                   # e.g. "EMITL2BCH4PLM"
    product_version   = Column(String(20))
    processing_version = Column(String(50))                   # provider software build
    source_url        = Column(Text)
    source_revised_at = Column(DateTime(timezone=True))
    ingestion_run_id  = Column(Integer, ForeignKey("ingestion_runs.id"))
    raw_properties    = Column(JSONB, nullable=False, default=dict)

    # Licence, so paid reports only use data we are allowed to sell
    licence                = Column(String(100), nullable=False)
    attribution            = Column(Text, nullable=False)
    commercial_use_allowed = Column(Boolean, nullable=False)

    # Observation
    gas          = Column(String(10), nullable=False, default="CH4")
    observed_at  = Column(DateTime(timezone=True), nullable=False, index=True)
    geom         = Column(Geometry("POINT", srid=SRID, spatial_index=False), nullable=False)
    geom_kind    = Column(String(30), nullable=False)   # "max_enhancement" | "outline_centroid"
    outline      = Column(Geometry("GEOMETRY", srid=SRID, spatial_index=False))
    cloud_cover_pct = Column(Float)

    # Quantification, exactly as reported by the provider
    emission_rate_kg_hr        = Column(Float)
    emission_uncertainty_kg_hr = Column(Float)
    max_enhancement_ppm_m      = Column(Float)
    wind_speed_ms              = Column(Float)
    wind_speed_std_ms          = Column(Float)
    wind_source                = Column(String(50))
    fetch_length_m             = Column(Float)

    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at    = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_plume_source_id"),
        Index("ix_plume_detections_geom", "geom", postgresql_using="gist"),
    )


class SatelliteScene(Base):
    """
    Catalogue entry for a satellite image that covers a watched site.
    Holds metadata and asset links only. Pixels are fetched on demand.
    """
    __tablename__ = "satellite_scenes"
    id          = Column(BigInteger, primary_key=True)
    source      = Column(String(50), nullable=False)    # e.g. "sentinel-2-l1c"
    source_id   = Column(String(255), nullable=False)   # STAC item id
    platform    = Column(String(50))
    acquired_at = Column(DateTime(timezone=True), nullable=False, index=True)
    cloud_cover_pct = Column(Float)
    tile_id     = Column(String(20), index=True)
    footprint   = Column(Geometry("GEOMETRY", srid=SRID, spatial_index=False), nullable=False)
    assets      = Column(JSONB, nullable=False, default=dict)   # band -> {href, https, scale, offset, gsd_m}
    licence     = Column(String(100), nullable=False)
    attribution = Column(Text, nullable=False)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"))
    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at    = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_scene_source_id"),
        Index("ix_satellite_scenes_footprint", "footprint", postgresql_using="gist"),
    )
