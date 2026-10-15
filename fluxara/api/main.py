# fluxara/api/main.py
import asyncio
import logging
import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fluxara.api.routes import facilities, alerts, reports, timeseries, plumes
from fluxara.api.routes import admin, company, government, auth
from fluxara.database.connection import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fluxara")

LEGACY_INVERSION = os.getenv("FLUXARA_ENABLE_LEGACY_INVERSION", "false").lower() == "true"
AUTO_PDFS = (os.getenv("FLUXARA_AUTO_GENERATE_PDFS", "false").lower() == "true"
             and os.getenv("FLUXARA_ENABLE_LEGACY_REPORTS", "false").lower() == "true")

app = FastAPI(
    title="Fluxara API",
    description="Methane observations from open satellite data, with sources and uncertainty.",
    version="0.2.0",
)

# CORS: list the exact frontend origins, comma separated. No wildcard, because
# the API accepts credentials.
_origins = [o.strip() for o in os.getenv("FLUXARA_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(facilities.router, prefix="/v1")
app.include_router(alerts.router, prefix="/v1")
app.include_router(reports.router, prefix="/v1")
app.include_router(timeseries.router, prefix="/v1")
app.include_router(plumes.router, prefix="/v1")
app.include_router(admin.router)
app.include_router(company.router)
app.include_router(government.router)
app.include_router(auth.router)

if LEGACY_INVERSION:
    # Needs torch. Experimental research code, off by default.
    from fluxara.api.routes import invert
    app.include_router(invert.router)
    logger.warning("Legacy neural inversion route is ENABLED (experimental, unvalidated)")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal error."})


# The database schema is managed by Alembic:  alembic upgrade head
# The API does not create or alter tables at startup.

async def _run_pdf_generation():
    from fluxara.reports.auto_generator import generate_all_reports
    try:
        await generate_all_reports()
    except Exception as e:
        logger.error("Background PDF generation failed: %s", e, exc_info=True)


async def _nightly_scheduler():
    from datetime import datetime, timedelta, timezone
    while True:
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep((tomorrow - now).total_seconds())
        await _run_pdf_generation()


@app.on_event("startup")
async def startup_generate_pdfs():
    # Off by default: the current report templates are built on
    # facilities.fluxara_latest, which no real pipeline fills yet.
    if AUTO_PDFS:
        asyncio.create_task(_run_pdf_generation())
        asyncio.create_task(_nightly_scheduler())


@app.get("/health", tags=["System"])
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = postgis = False
    plumes_count = None
    last_ingest = None
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
        postgis = (await db.execute(text(
            "SELECT count(*) FROM pg_extension WHERE extname = 'postgis'"))).scalar() == 1
        plumes_count = (await db.execute(text("SELECT count(*) FROM plume_detections"))).scalar()
        last_ingest = (await db.execute(text(
            "SELECT max(finished_at) FROM ingestion_runs WHERE status = 'success'"))).scalar()
    except Exception as e:
        logger.error("Health check DB failure: %s", e)
    return {
        "status": "healthy" if (db_ok and postgis) else "degraded",
        "version": app.version,
        "db_connected": db_ok,
        "postgis": postgis,
        "plume_detections": plumes_count,
        "last_successful_ingest": last_ingest.isoformat() if last_ingest else None,
        "legacy_inversion_enabled": LEGACY_INVERSION,
    }


@app.get("/")
async def root():
    return {"name": "Fluxara API", "docs": "/docs"}
