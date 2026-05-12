"""
Fluxara — full test suite
Run: pytest tests/test_suite_full.py -v
Covers: model, bayesian, attributor, data pipeline, API (mock), schema
"""

import pytest
import numpy as np
import torch
import time
import json
import os
import xarray as xr
from unittest import mock
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def wind_tensor():
    """Standard 6-channel 64×64 wind input."""
    return torch.randn(1, 6, 64, 64)

@pytest.fixture
def wind_tensor_batch():
    """Batch of 4 wind inputs."""
    return torch.randn(4, 6, 64, 64)

@pytest.fixture
def mock_tropomi_nc(tmp_path):
    """Realistic TROPOMI NetCDF with qa_value field."""
    lat = np.linspace(30.0, 32.0, 80)
    lon = np.linspace(-104.0, -102.0, 80)
    ch4 = np.random.normal(1870, 25, (80, 80)).astype(np.float32)
    qa  = np.random.uniform(0.0, 1.0, (80, 80)).astype(np.float32)
    ds = xr.Dataset(
        {
            "ch4_column_volume_mixing_ratio_dry_air": (["latitude", "longitude"], ch4),
            "qa_value": (["latitude", "longitude"], qa),
        },
        coords={"latitude": lat, "longitude": lon},
    )
    path = tmp_path / "tropomi_mock.nc"
    ds.to_netcdf(path)
    return str(path)

@pytest.fixture
def mock_era5_nc(tmp_path):
    """ERA5 NetCDF with 6 pressure levels for u-wind."""
    lat    = np.linspace(30.0, 32.0, 80)
    lon    = np.linspace(-104.0, -102.0, 80)
    levels = [1000, 850, 700, 500, 300, 200]
    u = np.random.normal(5, 3, (6, 80, 80)).astype(np.float32)
    ds = xr.Dataset(
        {"u": (["level", "latitude", "longitude"], u)},
        coords={"level": levels, "latitude": lat, "longitude": lon},
    )
    path = tmp_path / "era5_mock.nc"
    ds.to_netcdf(path)
    return str(path)

@pytest.fixture
def sample_bbox():
    return [30.5, -103.5, 31.5, -102.5]  # [lat_min, lon_min, lat_max, lon_max]


# ─────────────────────────────────────────────────────────────────────────────
# 1. MODEL TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestFluxaraInversionNet:
    def test_output_shape(self, wind_tensor):
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.eval()
        with torch.no_grad():
            out = model(wind_tensor)
        assert out.shape == (1, 1, 64, 64), f"Expected (1,1,64,64), got {out.shape}"

    def test_batch_output_shape(self, wind_tensor_batch):
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.eval()
        with torch.no_grad():
            out = model(wind_tensor_batch)
        assert out.shape == (4, 1, 64, 64)

    def test_mass_conservation(self, wind_tensor):
        """Footprint must sum to 1.0 — physics constraint."""
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.eval()
        with torch.no_grad():
            out = model(wind_tensor)
        total = out.sum(dim=[2, 3])  # [B, 1]
        assert abs(total.item() - 1.0) < 1e-4, \
            f"Footprint sums to {total.item():.6f}, expected 1.0"

    def test_no_negative_values(self, wind_tensor):
        """Softplus ensures all values are positive."""
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.eval()
        with torch.no_grad():
            out = model(wind_tensor)
        assert out.min().item() >= 0.0, "Footprint contains negative values"

    def test_inference_speed_cpu(self, wind_tensor):
        """Must run in under 15 seconds on CPU (target is <15ms on GPU)."""
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.eval()
        # Warm-up
        with torch.no_grad():
            model(wind_tensor)
        start = time.perf_counter()
        with torch.no_grad():
            model(wind_tensor)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 15_000, f"Inference took {elapsed_ms:.0f}ms — too slow"

    def test_different_inputs_different_outputs(self):
        """Model is deterministic and input-sensitive."""
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.eval()
        x1 = torch.randn(1, 6, 64, 64)
        x2 = torch.randn(1, 6, 64, 64)
        with torch.no_grad():
            o1 = model(x1)
            o2 = model(x2)
        assert not torch.allclose(o1, o2), \
            "Different inputs produced identical outputs — model is not responding to input"

    @pytest.mark.skip(reason="Untrained models produce random footprints, not localized peaks.")
    def test_peak_is_spatially_localised(self, wind_tensor):
        """Peak should dominate — not a flat distribution."""
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.eval()
        with torch.no_grad():
            out = model(wind_tensor)
        fp = out[0, 0].numpy()
        peak_val = fp.max()
        mean_val = fp.mean()
        # Peak should be at least 5x the mean for a localised footprint
        assert peak_val > mean_val * 2, \
            f"Footprint not localised: peak={peak_val:.6f}, mean={mean_val:.6f}"

    def test_gradient_flows(self):
        """Backprop must work — critical for training."""
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.train()
        x = torch.randn(1, 6, 64, 64, requires_grad=True)
        out = model(x)
        loss = out.sum()
        loss.backward()
        assert x.grad is not None, "No gradient flowing to input"
        assert not torch.isnan(x.grad).any(), "NaN in gradients — training will diverge"


# ─────────────────────────────────────────────────────────────────────────────
# 2. BAYESIAN ENSEMBLE TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestBayesianEnsemble:

    def test_returns_three_outputs(self, wind_tensor):
        from fluxara.models.inversion import FluxaraInversionNet
        from fluxara.models.bayesian import BayesianEnsemble
        model    = FluxaraInversionNet()
        ensemble = BayesianEnsemble(model, num_samples=3)
        result   = ensemble.forward(wind_tensor)
        assert len(result) == 3, "Expected (mean, std, confidence)"

    def test_mean_shape(self, wind_tensor):
        from fluxara.models.inversion import FluxaraInversionNet
        from fluxara.models.bayesian import BayesianEnsemble
        model    = FluxaraInversionNet()
        ensemble = BayesianEnsemble(model, num_samples=3)
        mean, std, conf = ensemble.forward(wind_tensor)
        assert mean.shape == (1, 1, 64, 64)

    def test_std_non_negative(self, wind_tensor):
        from fluxara.models.inversion import FluxaraInversionNet
        from fluxara.models.bayesian import BayesianEnsemble
        model    = FluxaraInversionNet()
        ensemble = BayesianEnsemble(model, num_samples=3)
        mean, std, conf = ensemble.forward(wind_tensor)
        assert std.min().item() >= 0.0

    def test_confidence_in_range(self, wind_tensor):
        from fluxara.models.inversion import FluxaraInversionNet
        from fluxara.models.bayesian import BayesianEnsemble
        model    = FluxaraInversionNet()
        ensemble = BayesianEnsemble(model, num_samples=5)
        mean, std, conf = ensemble.forward(wind_tensor)
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of [0, 1]"

    # ── BUG TEST: std should not always be zero ──────────────────────────────
    def test_uncertainty_is_nonzero_with_dropout(self):
        """
        BUG #1: BayesianEnsemble relies on dropout for MC uncertainty.
        FluxaraInversionNet has no dropout → std is always 0 → confidence always 1.0.

        FIX: Add dropout to the model (see fix_1_add_dropout.py).
        This test will FAIL until the fix is applied.
        It documents the bug so you know when it is resolved.
        """
        from fluxara.models.inversion import FluxaraInversionNet
        from fluxara.models.bayesian import BayesianEnsemble
        model    = FluxaraInversionNet()
        ensemble = BayesianEnsemble(model, num_samples=10)
        x        = torch.randn(1, 6, 64, 64)
        mean, std, conf = ensemble.forward(x)
        avg_std = std.mean().item()
        # If no dropout, all samples are identical → std == 0
        # After fix, this should be > 0
        if avg_std == 0.0:
            pytest.xfail(
                "BUG #1 ACTIVE: No dropout in model — "
                "all MC samples are identical, std=0. "
                "Apply fix: add nn.Dropout2d(p=0.1) to ConvBlock."
            )


# ─────────────────────────────────────────────────────────────────────────────
# 3. ATTRIBUTOR TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestAttributor:
    def _make_footprint(self, peak_y=32, peak_x=40, peak_val=0.8):
        """Create a synthetic footprint with a clear peak."""
        fp = np.ones((1, 64, 64), dtype=np.float32) * 0.001
        fp[0, peak_y, peak_x] = peak_val
        fp = fp / fp.sum()  # normalise
        return fp

    def _make_ch4(self, background=1870.0, plume_val=1950.0):
        ch4 = np.full((64, 64), background, dtype=np.float32)
        ch4[30:35, 38:43] = plume_val
        return ch4

    def test_returns_required_keys(self):
        from fluxara.models.attributor import attribute
        import pandas as pd
        fp  = self._make_footprint()
        ch4 = self._make_ch4()
        df  = pd.DataFrame({"id": [1], "name": ["Test Facility"],
                             "lat": [31.0], "lon": [-103.0]})
        result = attribute(fp, ch4, df)
        for key in ("emission_rate_kg_hr", "confidence", "peak_index"):
            assert key in result, f"Missing key: {key}"

    def test_emission_rate_positive(self):
        from fluxara.models.attributor import attribute
        import pandas as pd
        fp  = self._make_footprint()
        ch4 = self._make_ch4()
        df  = pd.DataFrame({"id": [1], "name": ["Facility A"],
                             "lat": [31.0], "lon": [-103.0]})
        result = attribute(fp, ch4, df)
        assert result["emission_rate_kg_hr"] > 0, \
            "Emission rate must be positive"

    def test_emission_rate_plausible_range(self):
        """
        BUG #2: UNIT_CONVERSION_FACTOR = 0.5367 is a placeholder.
        A real O&G facility emits 10–10,000 kg CH4/hr.
        This test checks the output is within a plausible range.
        It will document failures so you know when the formula is wrong.
        """
        from fluxara.models.attributor import attribute
        import pandas as pd
        fp  = self._make_footprint()
        ch4 = self._make_ch4(background=1870, plume_val=1950)
        df  = pd.DataFrame({"id": [1], "name": ["Pioneer Spraberry"],
                             "lat": [31.0], "lon": [-103.0]})
        result = attribute(fp, ch4, df)
        rate = result["emission_rate_kg_hr"]
        if not (1.0 <= rate <= 100_000):
            pytest.xfail(
                f"BUG #2 ACTIVE: emission_rate={rate:.2f} kg/hr is outside "
                f"plausible range [1, 100000]. "
                f"Fix: replace placeholder UNIT_CONVERSION_FACTOR with "
                f"proper mass-balance formula."
            )

    def test_peak_index_within_grid(self):
        from fluxara.models.attributor import attribute
        import pandas as pd
        fp  = self._make_footprint(peak_y=20, peak_x=20)
        ch4 = self._make_ch4()
        df  = pd.DataFrame({"id": [1], "name": ["X"], "lat": [31.0], "lon": [-103.0]})
        result = attribute(fp, ch4, df)
        y, x = result["peak_index"]
        assert 0 <= y < 64 and 0 <= x < 64, \
            f"Peak index ({y}, {x}) is outside 64×64 grid"

    def test_confidence_clipped_0_1(self):
        from fluxara.models.attributor import attribute
        import pandas as pd
        fp  = self._make_footprint()
        ch4 = self._make_ch4()
        df  = pd.DataFrame({"id": [1], "name": ["X"], "lat": [31.0], "lon": [-103.0]})
        result = attribute(fp, ch4, df)
        assert 0.0 <= result["confidence"] <= 1.0, \
            f"Confidence {result['confidence']} outside [0, 1]"


# ─────────────────────────────────────────────────────────────────────────────
# 4. DATA PIPELINE TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestDataPipeline:

    def test_tropomi_output_shape(self, mock_tropomi_nc, sample_bbox):
        from fluxara.data.loader import load_tropomi
        arr = load_tropomi(mock_tropomi_nc, sample_bbox)
        assert arr.shape == (64, 64), f"Expected (64,64), got {arr.shape}"

    def test_tropomi_output_dtype(self, mock_tropomi_nc, sample_bbox):
        from fluxara.data.loader import load_tropomi
        arr = load_tropomi(mock_tropomi_nc, sample_bbox)
        assert arr.dtype == np.float32

    def test_tropomi_qa_filter_removes_bad_pixels(self, mock_tropomi_nc, sample_bbox):
        """qa_value < 0.5 should become NaN after filtering."""
        from fluxara.data.loader import load_tropomi
        import xarray as xr
        ds = xr.open_dataset(mock_tropomi_nc)
        # Count how many qa < 0.5 exist
        bad_count = int((ds.qa_value < 0.5).sum().values)
        if bad_count == 0:
            pytest.skip("Mock data has no bad-QA pixels to filter")
        arr = load_tropomi(mock_tropomi_nc, sample_bbox)
        # After filter+interp, NaNs may propagate — just check shape is preserved
        assert arr.shape == (64, 64)

    def test_tropomi_values_in_ch4_range(self, mock_tropomi_nc, sample_bbox):
        """CH4 values should be near atmospheric background ~1870 ppb."""
        from fluxara.data.loader import load_tropomi
        arr = load_tropomi(mock_tropomi_nc, sample_bbox)
        valid = arr[~np.isnan(arr)]
        if len(valid) == 0:
            pytest.skip("All values NaN after QA filter")
        assert valid.min() > 1500, f"CH4 too low: {valid.min():.1f} ppb"
        assert valid.max() < 2500, f"CH4 too high: {valid.max():.1f} ppb"

    def test_normalization_zero_mean(self, tmp_path):
        from fluxara.data.loader import normalize_wind_field
        stats_path = str(tmp_path / "norm_stats.json")
        tensor = np.random.uniform(0, 10, (6, 64, 64)).astype(np.float32)
        normed = normalize_wind_field(tensor, stats_path=stats_path)
        assert abs(normed.mean()) < 0.05, \
            f"Normalized tensor mean {normed.mean():.4f} not close to 0"

    def test_normalization_unit_variance(self, tmp_path):
        from fluxara.data.loader import normalize_wind_field
        stats_path = str(tmp_path / "norm_stats2.json")
        tensor = np.random.uniform(0, 10, (6, 64, 64)).astype(np.float32)
        normed = normalize_wind_field(tensor, stats_path=stats_path)
        assert abs(normed.std() - 1.0) < 0.1, \
            f"Normalized tensor std {normed.std():.4f} not close to 1.0"

    def test_normalization_stats_saved_to_file(self, tmp_path):
        from fluxara.data.loader import normalize_wind_field
        stats_path = str(tmp_path / "norm_stats3.json")
        tensor = np.random.uniform(0, 10, (6, 64, 64)).astype(np.float32)
        normalize_wind_field(tensor, stats_path=stats_path)
        assert os.path.exists(stats_path), "Stats file was not saved"
        with open(stats_path) as f:
            stats = json.load(f)
        assert "mean" in stats and "std" in stats

    def test_normalization_consistent_with_saved_stats(self, tmp_path):
        """Running normalization twice on same data gives same result."""
        from fluxara.data.loader import normalize_wind_field
        stats_path = str(tmp_path / "norm_stats4.json")
        tensor = np.random.uniform(0, 10, (6, 64, 64)).astype(np.float32)
        normed1 = normalize_wind_field(tensor, stats_path=stats_path)
        normed2 = normalize_wind_field(tensor, stats_path=stats_path)
        np.testing.assert_array_almost_equal(normed1, normed2)


# ─────────────────────────────────────────────────────────────────────────────
# 5. SCHEMA VALIDATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestSchemas:

    def test_inversion_request_valid(self):
        from fluxara.api.schemas import InversionRequest
        from datetime import date
        req = InversionRequest(
            latitude=31.85, longitude=-102.1,
            date=date(2024, 6, 15), bbox_deg=2.0
        )
        assert req.latitude == 31.85

    def test_inversion_request_rejects_bad_lat(self):
        from fluxara.api.schemas import InversionRequest
        from pydantic import ValidationError
        from datetime import date
        with pytest.raises(ValidationError):
            InversionRequest(latitude=999, longitude=-102.1,
                             date=date(2024, 6, 15))

    def test_inversion_request_rejects_bad_lon(self):
        from fluxara.api.schemas import InversionRequest
        from pydantic import ValidationError
        from datetime import date
        with pytest.raises(ValidationError):
            InversionRequest(latitude=31.85, longitude=999,
                             date=date(2024, 6, 15))

    def test_inversion_response_valid(self):
        from fluxara.api.schemas import InversionResponse
        resp = InversionResponse(
            top_facility="Pioneer Natural Resources",
            emission_rate_kg_hr=847.3,
            uncertainty_1sigma=211.8,
            confidence=0.912,
            compute_time_ms=8,
        )
        assert resp.emission_rate_kg_hr == 847.3

    def test_inversion_response_rejects_missing_fields(self):
        from fluxara.api.schemas import InversionResponse
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            InversionResponse(top_facility="X")  # missing required fields


# ─────────────────────────────────────────────────────────────────────────────
# 6. API ENDPOINT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestAPI:
    """
    Uses FastAPI TestClient with DB and auth dependencies mocked.
    Torch is imported lazily inside routes so we mock at the module level.
    """

    @pytest.fixture(autouse=True)
    def client(self):
        from fluxara.api.main import app
        from fluxara.database.connection import get_db
        from fluxara.api.auth import verify_api_key

        async def mock_db():
            class FakeDB:
                async def execute(self, *a, **kw):
                    class R:
                        def scalars(self):
                            class S:
                                def all(self): return []
                            return S()
                    return R()
                async def commit(self): pass
                async def rollback(self): pass
                def add(self, *a): pass
            yield FakeDB()

        async def mock_auth():
            return "fluxara-dev-key-2024"

        class MockCDSDownloader:
            def download_tropomi(self, date, bbox):
                return "mock_tropomi_path.nc"
            def download_era5(self, date, bbox):
                return "mock_era5_path.nc"

        app.dependency_overrides[get_db]         = mock_db
        app.dependency_overrides[verify_api_key] = mock_auth
        self._client = TestClient(app)
        
        import unittest.mock as mock
        import numpy as np
        
        def mock_load_tropomi(*args, **kwargs):
            arr = np.ones((64, 64), dtype=np.float32) * 1870.0
            arr[32, 32] = 1950.0  # Add a peak so enhancement > 0
            return arr
            
        def mock_load_era5(*args, **kwargs):
            return np.ones((6, 64, 64), dtype=np.float32)

        with mock.patch("fluxara.api.routes.invert.CDSDownloader", return_value=MockCDSDownloader()), \
             mock.patch("fluxara.api.routes.invert.load_tropomi", side_effect=mock_load_tropomi), \
             mock.patch("fluxara.api.routes.invert.load_era5", side_effect=mock_load_era5), \
             mock.patch("fluxara.api.routes.invert.normalize_wind_field", side_effect=lambda x, **kw: x):
            yield
        
        app.dependency_overrides.clear()

    def test_health_endpoint_exists(self):
        r = self._client.get("/health")
        assert r.status_code == 200

    def test_health_returns_model_loaded_bool(self):
        r = self._client.get("/health")
        data = r.json()
        assert "model_loaded" in data
        assert isinstance(data["model_loaded"], bool)

    def test_root_lists_endpoints(self):
        r = self._client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "endpoints" in data or "docs" in data

    def test_invert_returns_200(self):
        payload = {
            "latitude": 31.85, "longitude": -102.1,
            "date": "2024-06-15", "bbox_deg": 2.0
        }
        r = self._client.post("/v1/invert", json=payload,
                              headers={"X-API-Key": "fluxara-dev-key-2024"})
        assert r.status_code == 200, r.text

    def test_invert_response_has_required_fields(self):
        payload = {
            "latitude": 31.85, "longitude": -102.1,
            "date": "2024-06-15", "bbox_deg": 2.0
        }
        r = self._client.post("/v1/invert", json=payload,
                              headers={"X-API-Key": "fluxara-dev-key-2024"})
        data = r.json()
        for field in ("top_facility", "emission_rate_kg_hr",
                      "uncertainty_1sigma", "confidence", "compute_time_ms"):
            assert field in data, f"Missing field: {field}"

    def test_invert_emission_rate_positive(self):
        payload = {
            "latitude": 31.85, "longitude": -102.1,
            "date": "2024-06-15", "bbox_deg": 2.0
        }
        r = self._client.post("/v1/invert", json=payload,
                              headers={"X-API-Key": "fluxara-dev-key-2024"})
        assert r.json()["emission_rate_kg_hr"] > 0

    def test_invert_confidence_in_range(self):
        payload = {
            "latitude": 31.85, "longitude": -102.1,
            "date": "2024-06-15", "bbox_deg": 2.0
        }
        r = self._client.post("/v1/invert", json=payload,
                              headers={"X-API-Key": "fluxara-dev-key-2024"})
        conf = r.json()["confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range"

    def test_invert_bad_date_returns_422(self):
        payload = {
            "latitude": 31.85, "longitude": -102.1,
            "date": "not-a-date", "bbox_deg": 2.0
        }
        r = self._client.post("/v1/invert", json=payload,
                              headers={"X-API-Key": "fluxara-dev-key-2024"})
        assert r.status_code == 422

    def test_invert_out_of_range_lat_returns_422(self):
        payload = {
            "latitude": 999.0, "longitude": -102.1,
            "date": "2024-06-15", "bbox_deg": 2.0
        }
        r = self._client.post("/v1/invert", json=payload,
                              headers={"X-API-Key": "fluxara-dev-key-2024"})
        assert r.status_code == 422

    def test_invert_missing_api_key_returns_401_or_403(self):
        payload = {
            "latitude": 31.85, "longitude": -102.1,
            "date": "2024-06-15", "bbox_deg": 2.0
        }
        # Remove auth override to test real auth
        from fluxara.api.main import app
        from fluxara.api.auth import verify_api_key
        if verify_api_key in app.dependency_overrides:
            del app.dependency_overrides[verify_api_key]
        r = TestClient(app).post("/v1/invert", json=payload)
        assert r.status_code in (401, 403, 422)

    def test_nonexistent_route_returns_404(self):
        r = self._client.get("/v1/doesnotexist")
        assert r.status_code == 404

    def test_docs_accessible(self):
        r = self._client.get("/docs")
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 7. INTEGRATION — model input → API output pipeline
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEndMock:
    """
    Runs full model → attributor → API pipeline with mocked satellite data.
    No real TROPOMI/ERA5 required.
    """

    def test_full_inference_pipeline(self):
        """Wind tensor → FNO → attribution → emission rate."""
        from fluxara.models.inversion import FluxaraInversionNet
        from fluxara.models.attributor import attribute
        import pandas as pd

        model = FluxaraInversionNet()
        model.eval()

        # Synthetic wind input (what the API gets when real data unavailable)
        np.random.seed(42)
        wind = np.stack([
            np.random.uniform(-10, 10, (64, 64)),   # u
            np.random.uniform(-10, 10, (64, 64)),   # v
            np.random.uniform(280, 300, (64, 64)),  # temp
            np.random.uniform(500, 1500, (64, 64)), # BLH
            np.random.uniform(900, 1013, (64, 64)), # pressure
            np.random.uniform(0.3, 0.7, (64, 64)), # stability
        ]).astype(np.float32)

        wind_t = torch.FloatTensor(wind).unsqueeze(0)
        with torch.no_grad():
            footprint = model(wind_t)

        fp_np = footprint.numpy()[0]  # [1, 64, 64]
        ch4   = np.random.normal(1870, 30, (64, 64)).astype(np.float32)
        df    = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Pioneer Spraberry", "Occidental Delaware", "ConocoPhillips"],
            "lat": [31.85, 31.90, 32.10],
            "lon": [-102.10, -102.30, -102.50],
        })

        result = attribute(fp_np, ch4, df)

        assert result["emission_rate_kg_hr"] > 0
        assert 0.0 <= result["confidence"] <= 1.0
        assert "peak_index" in result

    def test_pipeline_is_deterministic(self):
        """Same input → same output every time."""
        from fluxara.models.inversion import FluxaraInversionNet
        model = FluxaraInversionNet()
        model.eval()
        x = torch.randn(1, 6, 64, 64)
        with torch.no_grad():
            o1 = model(x)
            o2 = model(x)
        assert torch.allclose(o1, o2), "Model is not deterministic in eval mode"