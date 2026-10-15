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
    """
    Load the legacy research model. Raises if there are no trained weights.
    It never falls back to a randomly initialised network.
    """
    global _MODEL, _ENSEMBLE
    if _ENSEMBLE is not None:
        return _ENSEMBLE

    ckpt_path = "checkpoints/fluxara_best.pt"
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(
            f"No model checkpoint at {ckpt_path}. The legacy inversion cannot run.")
    model = FluxaraInversionNet()
    ckpt = torch.load(ckpt_path, map_location="cpu")
    model.load_state_dict(ckpt.get("model_state_dict", ckpt))
    model.eval()
    _MODEL, _ENSEMBLE = model, BayesianEnsemble(model)
    return _ENSEMBLE
