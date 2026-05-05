# fluxara/models/inference.py
import torch
import numpy as np


def run_inference(model, wind_tensor: torch.Tensor, device) -> np.ndarray:
    """
    Run the FNO model on a wind field tensor.
    Returns the footprint as a numpy array.
    """
    model.eval()
    with torch.no_grad():
        output = model(wind_tensor.to(device))
    return output[0, 0].cpu().numpy()
