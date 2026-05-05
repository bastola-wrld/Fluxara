# fluxara/models/bayesian.py
import torch
import torch.nn as nn
import numpy as np

class BayesianEnsemble:
    """
    Ensemble of FluxaraInversionNet instances with MC Dropout.
    Provides uncertainty quantification (1-sigma).
    """
    def __init__(self, base_model, num_samples=5):
        self.model = base_model
        self.num_samples = num_samples

    def forward(self, x):
        """
        Run multiple forward passes with dropout enabled.
        """
        # Ensure dropout is active even in eval mode
        self.model.train() # Force dropout on
        
        outputs = []
        for _ in range(self.num_samples):
            with torch.no_grad():
                outputs.append(self.model(x))
        
        outputs = torch.stack(outputs) # [num_samples, batch, 1, 64, 64]
        
        mean = outputs.mean(dim=0)
        std = outputs.std(dim=0)
        
        # Calculate confidence score (0-1)
        # Low std relative to mean = high confidence
        avg_mean = mean.mean().item()
        avg_std = std.mean().item()
        confidence = 1.0 - (avg_std / (avg_mean + 1e-9))
        confidence = np.clip(confidence, 0.0, 1.0)
        
        return mean, std, float(confidence)
