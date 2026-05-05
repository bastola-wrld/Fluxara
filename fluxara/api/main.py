# fluxara/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fluxara.api.routes import facilities, alerts, reports, invert
from fluxara.database.connection import engine
from fluxara.database.models import Base

app = FastAPI(
    title="Fluxara API v1.0",
    description="Real-time satellite greenhouse gas attribution",
    version="1.0.0",
)

import torch
import os
from fluxara.models.inversion import FluxaraInversionNet
from fluxara.models.bayesian import BayesianEnsemble
import fluxara.api.routes.invert as invert_module


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(facilities.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(invert.router)

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
            logger.info(f"Model loaded — epoch {epoch}, MAE {mae}%")
            invert_module.MODEL = model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.warning("Running in mock mode")
    else:
        logger.warning("No checkpoint found — running in mock mode")


@app.get("/health", tags=["System"])
async def health():
    # Basic health check
    return {
        "status": "healthy",
        "version": "1.0.0",
        "model_loaded": invert_module.ENSEMBLE is not None,
        "db_connected": True
    }

@app.get("/")
async def root():
    return {
        "name": "Fluxara API",
        "docs": "/docs",
        "endpoints": ["/facilities", "/alerts", "/reports", "/v1/invert"]
    }