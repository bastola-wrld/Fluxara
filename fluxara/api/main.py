# fluxara/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fluxara.api.routes import facilities, alerts, reports, invert, timeseries
from fluxara.api.routes import admin, company, government, auth
from fluxara.database.connection import engine
from fluxara.database.models import Base

app = FastAPI(
    title="Fluxara API v1.0",
    description="Real-time satellite greenhouse gas attribution",
    version="1.0.0",
)

import torch
import os
import asyncio
from fluxara.models.inversion import FluxaraInversionNet
from fluxara.models.bayesian import BayesianEnsemble
import fluxara.api.routes.invert as invert_module


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local development unblocking
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers with /v1 prefix
app.include_router(facilities.router, prefix="/v1")
app.include_router(alerts.router, prefix="/v1")
app.include_router(reports.router, prefix="/v1")
app.include_router(invert.router)
app.include_router(timeseries.router, prefix="/v1")

app.include_router(admin.router)
app.include_router(company.router)
app.include_router(government.router)
app.include_router(auth.router)

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fluxara")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred in the Fluxara Engine.", "type": type(exc).__name__},
    )


# ── PDF Auto-Generation: Background Task + Nightly Scheduler ──────────────

async def _run_pdf_generation():
    """Background task: generate all PDFs from database data."""
    from fluxara.reports.auto_generator import generate_all_reports
    try:
        logger.info("Starting background PDF generation...")
        manifest = await generate_all_reports()
        if manifest:
            total = (
                len(manifest.get("facilities", []))
                + len(manifest.get("regions", []))
                + len(manifest.get("companies", []))
                + (1 if manifest.get("global") else 0)
            )
            logger.info(f"PDF generation complete: {total} reports ready for instant download")
    except Exception as e:
        logger.error(f"Background PDF generation failed: {e}", exc_info=True)


async def _nightly_scheduler():
    """Runs at midnight every night to regenerate all PDFs with fresh data."""
    from datetime import datetime, timedelta
    while True:
        now = datetime.utcnow()
        # Calculate seconds until next midnight UTC
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = (tomorrow - now).total_seconds()
        logger.info(f"Nightly PDF scheduler: next run in {wait_seconds/3600:.1f} hours (midnight UTC)")
        await asyncio.sleep(wait_seconds)

        logger.info("Nightly PDF regeneration starting...")
        await _run_pdf_generation()


@app.on_event("startup")
async def load_model():
    ckpt_path = "checkpoints/fluxara_best.pt"
    if os.path.exists(ckpt_path):
        try:
            model = FluxaraInversionNet()
            ckpt = torch.load(ckpt_path, map_location='cpu')
            model.load_state_dict(ckpt.get("model_state_dict", ckpt))
            model.eval()
            invert_module.ENSEMBLE = BayesianEnsemble(model)
            
            epoch = ckpt.get("epoch", "Unknown") if isinstance(ckpt, dict) else "Unknown"
            mae = ckpt.get("val_mae_pct", "Unknown") if isinstance(ckpt, dict) else "Unknown"
            logger.info(f"Model loaded - epoch {epoch}, MAE {mae}%")
            invert_module.MODEL = model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.warning("Running in mock mode")
    else:
        logger.warning("No checkpoint found - running in mock mode")


@app.on_event("startup")
async def startup_create_tables():
    """Ensure all tables exist (including generated_reports)."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified")
    except Exception as e:
        logger.error(f"DATABASE CONNECTION FAILED: {e}")
        logger.warning("The API is running in DEGRADED mode (no database). Start Docker and the 'db' container.")


@app.on_event("startup")
async def startup_generate_pdfs():
    """Generate all PDFs in background on startup (non-blocking)."""
    # Run PDF generation as a background task so the API starts immediately
    asyncio.create_task(_run_pdf_generation())
    # Start the nightly scheduler
    asyncio.create_task(_nightly_scheduler())
    logger.info("PDF auto-generation scheduled (background)")


@app.get("/health", tags=["System"])
async def health(db: AsyncSession = Depends(get_db)):
    from fluxara.reports.auto_generator import get_manifest
    manifest = get_manifest()
    
    db_ok = False
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB failure: {e}")

    pdf_count = 0
    if manifest:
        pdf_count = (
            len(manifest.get("facilities", []))
            + len(manifest.get("regions", []))
            + len(manifest.get("companies", []))
            + (1 if manifest.get("global") else 0)
        )
    return {
        "status": "healthy",
        "version": "1.0.0",
        "model_loaded": invert_module.ENSEMBLE is not None,
        "db_connected": db_ok,
        "pdfs_ready": pdf_count,
        "pdfs_generated_at": manifest.get("generated_at") if manifest else None,
    }

@app.get("/")
async def root():
    return {
        "name": "Fluxara API",
        "docs": "/docs",
        "endpoints": ["/facilities", "/alerts", "/reports", "/v1/invert"]
    }