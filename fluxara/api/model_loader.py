# fluxara/api/model_loader.py
import torch
import os
import logging
from fluxara.models.inversion import FluxaraInversionNet
from fluxara.models.bayesian import BayesianEnsemble

logger = logging.getLogger("fluxara.model_loader")

_MODEL = None
_ENSEMBLE = None

def get_ensemble():
    global _MODEL, _ENSEMBLE
    if _ENSEMBLE is not None:
        return _ENSEMBLE

    ckpt_path = "checkpoints/fluxara_best.pt"
    _MODEL = FluxaraInversionNet()
    
    if os.path.exists(ckpt_path):
        try:
            ckpt = torch.load(ckpt_path, map_location='cpu')
            # Handle potential dictionary vs raw state_dict
            _MODEL.load_state_dict(ckpt.get("model_state_dict", ckpt))
            _MODEL.eval()
            _ENSEMBLE = BayesianEnsemble(_MODEL)
            
            epoch = ckpt.get("epoch", "Unknown") if isinstance(ckpt, dict) else "Unknown"
            logger.info(f"✅ Model loaded successfully (Epoch {epoch})")
        except Exception as e:
            logger.error(f"❌ Failed to load model weights: {e}")
            _ENSEMBLE = BayesianEnsemble(_MODEL) # Mock mode (random weights)
    else:
        logger.warning("⚠️ No model checkpoint found. Running in mock mode.")
        _ENSEMBLE = BayesianEnsemble(_MODEL)

    return _ENSEMBLE