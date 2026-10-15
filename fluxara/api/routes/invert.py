"""
fluxara/api/routes/invert.py

LEGACY, EXPERIMENTAL. Not part of the product.

The U-Net behind this route was trained on synthetic data and has not been
validated against real emissions. The route is only mounted when
FLUXARA_ENABLE_LEGACY_INVERSION=true, and it returns 503 when no trained
model is present. It never returns placeholder numbers.
"""

import time
import os
import torch
import numpy as np
import logging
import pandas as pd

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fluxara.api.schemas import InversionRequest, InversionResponse
from fluxara.api.auth import verify_api_key
from fluxara.database.connection import get_db
from fluxara.database.models import Inversion, Facility

from fluxara.data.downloader import CDSDownloader
from fluxara.data.loader import load_tropomi, load_era5, normalize_wind_field
from fluxara.data.facilities import spatial_query
from fluxara.models.inversion import FluxaraInversionNet
from fluxara.models.bayesian import BayesianEnsemble
from fluxara.models.attributor import attribute

router = APIRouter(tags=["Inversion"])
log    = logging.getLogger("fluxara.api.invert")

MODEL    = None
ENSEMBLE = None
CKPT_BEST = "checkpoints/fluxara_best.pt"


def _load_model():
    """Load model from checkpoint. Returns (model, ensemble) or (None, None)."""
    if not os.path.exists(CKPT_BEST):
        log.warning("No checkpoint at %s: legacy inversion unavailable", CKPT_BEST)
        return None, None
    try:
        ckpt = torch.load(CKPT_BEST, map_location="cpu")
        m = FluxaraInversionNet()
        m.load_state_dict(ckpt["model_state_dict"])
        m.eval()
        e = BayesianEnsemble(m)
        log.info("Model loaded — epoch %s, val_MAE=%.2f%%",
                 ckpt.get("epoch", "?"), ckpt.get("val_mae_pct", 0))
        return m, e
    except Exception as ex:
        log.error("Failed to load model: %s", ex)
        return None, None


@router.post("/v1/invert", response_model=InversionResponse)
async def invert(
    req: InversionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    start = time.perf_counter()
    global MODEL, ENSEMBLE

    # ── Load model once ───────────────────────────────────────────────────────
    if ENSEMBLE is None:
        MODEL, ENSEMBLE = _load_model()

    date_str = req.date.strftime("%Y-%m-%d")
    bbox = [
        req.latitude  - req.bbox_deg / 2,
        req.longitude - req.bbox_deg / 2,
        req.latitude  + req.bbox_deg / 2,
        req.longitude + req.bbox_deg / 2,
    ]

    # ── No trained model: refuse, never invent a number ──────────────────────
    if ENSEMBLE is None:
        raise HTTPException(
            status_code=503,
            detail="The legacy neural inversion has no trained model and is disabled. "
                   "Use /v1/plumes for satellite observations.",
        )

    # ── Download satellite data ───────────────────────────────────────────────
    try:
        downloader    = CDSDownloader()
        tropomi_path  = downloader.download_tropomi(date_str, bbox)
        era5_path     = downloader.download_era5(date_str, bbox)
    except Exception as ex:
        log.error("Download failed: %s", ex)
        raise HTTPException(
            status_code=422,
            detail=f"Satellite data unavailable for {date_str} over {bbox}. "
                   f"Reason: {ex}"
        )

    if not tropomi_path or not era5_path:
        raise HTTPException(
            status_code=422,
            detail=f"No data found for {date_str}. "
                   "TROPOMI has ~20% cloud coverage gaps — try adjacent date."
        )

    # ── Load + preprocess — FAIL LOUDLY if data is bad ───────────────────────
    # We do NOT silently substitute random tensors. If data loading fails,
    # the client must know so they can investigate the source files.
    try:
        tropomi_ch4 = load_tropomi(tropomi_path, bbox)
        era5_wind   = load_era5(era5_path, bbox)
    except Exception as ex:
        log.error("Data loading failed: %s", ex)
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse satellite data: {ex}. "
                   "Verify CDS API returned valid NetCDF files."
        )

    try:
        norm_wind   = normalize_wind_field(era5_wind)
        model_input = torch.from_numpy(norm_wind).unsqueeze(0).float()  # [1,6,64,64]
    except Exception as ex:
        log.error("Preprocessing failed: %s", ex)
        raise HTTPException(status_code=500,
                            detail="Wind field normalisation failed.")

    # ── Neural inference ──────────────────────────────────────────────────────
    try:
        with torch.no_grad():
            mean_fp, std_fp, confidence = ENSEMBLE.forward(model_input)
        mean_fp_np = mean_fp.squeeze().numpy()   # [64, 64]
        std_fp_np  = std_fp.squeeze().numpy()    # [64, 64]
    except Exception as ex:
        log.error("Model inference error: %s", ex)
        raise HTTPException(status_code=500, detail="Neural inference failed.")

    # ── Attribution ───────────────────────────────────────────────────────────
    try:
        result = await db.execute(select(Facility))
        all_facilities = result.scalars().all()
        facilities_df  = pd.DataFrame([{
            "id": f.id, "name": f.name, "lat": f.lat, "lon": f.lon,
        } for f in all_facilities])

        attr = attribute(mean_fp.numpy()[0], tropomi_ch4, facilities_df)

        emission_rate = attr["emission_rate_kg_hr"]
        conf          = float(confidence) if not isinstance(confidence, float) \
                        else confidence

        # Resolve facility name from peak coordinates
        top_facility_name = "Unknown Source"
        facility_id       = None

        if not facilities_df.empty and "peak_index" in attr:
            peak_idx  = attr["peak_index"]
            peak_lat  = bbox[0] + (peak_idx[0] / 64) * req.bbox_deg
            peak_lon  = bbox[1] + (peak_idx[1] / 64) * req.bbox_deg
            nearest   = spatial_query(peak_lat, peak_lon, facilities_df)
            if nearest is not None:
                top_facility_name = nearest["name"]
                facility_id       = int(nearest["id"])

        if conf < 0.1:
            top_facility_name = "Unknown Source"
            log.warning("Low confidence (%.2f) — attribution unreliable", conf)

    except Exception as ex:
        log.error("Attribution error: %s", ex)
        raise HTTPException(status_code=500, detail="Facility attribution failed.")

    compute_ms = int((time.perf_counter() - start) * 1000)

    # ── Persist to database ───────────────────────────────────────────────────
    try:
        new_inv = Inversion(
            facility_id  = facility_id,
            latitude     = req.latitude,
            longitude    = req.longitude,
            date         = req.date,
            emission_rate= emission_rate,
            uncertainty  = float(std_fp_np.mean()),
            confidence   = conf,
            compute_ms   = compute_ms,
            tropomi_file = os.path.basename(tropomi_path),
            era5_file    = os.path.basename(era5_path),
        )
        db.add(new_inv)
        await db.commit()
    except Exception as ex:
        await db.rollback()
        log.error("DB write failed (result still returned): %s", ex)

    log.info(
        "Inversion complete | facility=%s | rate=%.1f kg/hr | "
        "conf=%.2f | compute_ms=%d",
        top_facility_name, emission_rate, conf, compute_ms
    )

    return InversionResponse(
        top_facility        = top_facility_name,
        emission_rate_kg_hr = emission_rate,
        uncertainty_1sigma  = float(std_fp_np.mean()),
        confidence          = conf,
        compute_time_ms     = compute_ms,
    )