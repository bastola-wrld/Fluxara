# tests/test_model.py
import pytest
import torch
import time
from fluxara.models.inversion import FluxaraInversionNet
from fluxara.models.bayesian import BayesianEnsemble

def test_output_shape_correct():
    model = FluxaraInversionNet()
    model.eval()
    x = torch.randn(1, 6, 64, 64)
    with torch.no_grad():
        output = model(x)
    assert output.shape == (1, 1, 64, 64)

def test_physics_constraint():
    model = FluxaraInversionNet()
    model.eval()
    x = torch.randn(1, 6, 64, 64)
    with torch.no_grad():
        output = model(x)
    assert abs(output.sum().item() - 1.0) < 0.01

def test_no_negative_values():
    model = FluxaraInversionNet()
    model.eval()
    x = torch.randn(1, 6, 64, 64)
    with torch.no_grad():
        output = model(x)
    assert output.min().item() >= 0.0

def test_inference_speed():
    model = FluxaraInversionNet()
    model.eval()
    x = torch.randn(1, 6, 64, 64)
    
    start = time.perf_counter()
    with torch.no_grad():
        _ = model(x)
    compute_ms = (time.perf_counter() - start) * 1000
    assert compute_ms < 15000

def test_bayesian_uncertainty_positive():
    model = FluxaraInversionNet()
    ensemble = BayesianEnsemble(model, num_samples=3)
    x = torch.randn(1, 6, 64, 64)
    mean, std, conf = ensemble.forward(x)
    assert std.min() >= 0.0
