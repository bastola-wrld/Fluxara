"""The NASA comparison script, with made up images instead of downloads."""
import importlib.util
import pathlib
from datetime import timedelta
from types import SimpleNamespace

import pytest

import synthetic
from fluxara.retrieval.wind import FixedWind
from test_retrieval_pipeline import OFFSET, SCALE, SIZE, WHEN, FilesOnDisk, site_lonlat

path = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "validate_s2_against_emit.py"
spec = importlib.util.spec_from_file_location("validate_script", path)
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


def image(source_id, when, platform="sentinel-2a", cloud=0.0):
    band = {"https": "https://example/band", "scale": SCALE, "offset": OFFSET}
    return SimpleNamespace(id=None, source_id=source_id, platform=platform, acquired_at=when,
                           cloud_cover_pct=cloud, tile_id="32SKA", relative_orbit=65,
                           sun_elevation_deg=90 - synthetic.SUN_ZENITH,
                           view_incidence_deg=synthetic.VIEW_ZENITH,
                           assets={"B11": band, "B12": band})


@pytest.fixture()
def setup(tmp_path, monkeypatch):
    lon, lat = site_lonlat()
    truth = synthetic.plume_column(1.0, 270.0, size=SIZE)
    reference = synthetic.with_noise(*synthetic.ground(0, size=SIZE), 1)
    b11, b12 = synthetic.with_noise(*synthetic.ground(0, size=SIZE), 2)
    images = {"REFERENCE": reference, "TARGET": (b11, synthetic.add_plume(b12, truth))}
    scenes = [image("REFERENCE", WHEN - timedelta(days=10)),
              image("TARGET", WHEN + timedelta(hours=5))]
    monkeypatch.setattr(script, "images_around", lambda http, plume, max_hours: scenes)

    rate = synthetic.true_rate_kg_hr(truth, 3.0)
    plume = SimpleNamespace(id="EMIT_1", time=WHEN, lat=lat, lon=lon, rate=rate,
                            uncertainty=0.3 * rate, wind_speed=3.0)
    return plume, scenes, FilesOnDisk(tmp_path, images)


def test_plume_seen_by_both_is_compared(setup):
    plume, _scenes, fetcher = setup
    line = script.compare_one(plume, None, fetcher, FixedWind(3.0, 270.0), max_hours=48)
    assert line["result"] == "plume_detected" and line["s2_image"] == "TARGET"
    assert line["hours_apart"] == 5.0
    assert 0.75 < line["s2_divided_by_emit"] < 1.25
    assert line["s2_detection_limit_kg_hr"] > 0


def test_nasa_wind_can_be_used_instead_of_era5(setup):
    plume, _scenes, fetcher = setup
    line = script.compare_one(plume, None, fetcher, None, max_hours=48)
    assert line["result"] == "plume_detected" and line["wind_speed_ms"] == 3.0
    assert "wind_agreement" not in line          # NASA gives no wind direction


def test_no_image_close_enough_in_time(setup):
    plume, _scenes, fetcher = setup
    line = script.compare_one(plume, None, fetcher, FixedWind(3.0, 270.0), max_hours=2)
    assert line["result"] == "no_image" and "within 2 hours" in line["reason"]


def test_summary_counts_and_does_not_blame_small_plumes():
    lines = [
        {"result": "plume_detected", "emit_rate_kg_hr": 5000, "emit_uncertainty_kg_hr": 1500,
         "s2_rate_kg_hr": 6000, "s2_uncertainty_kg_hr": 2000, "s2_divided_by_emit": 1.2},
        {"result": "no_plume", "emit_rate_kg_hr": 1200, "s2_detection_limit_kg_hr": 4000},
        {"result": "no_plume", "emit_rate_kg_hr": 9000, "s2_detection_limit_kg_hr": 4000},
        {"result": "no_image"}, {"result": "unusable"}, {"result": "failed"},
    ]
    text = script.summarise(lines, max_hours=48)
    assert text.startswith("EMIT plumes tried: 6")
    assert "Sentinel 2 also saw a plume: 1" in text
    assert "too small for that image: 1" in text
    assert "big enough to see but not seen: 1" in text
    assert "within a factor of 2 of NASA: 1 of 1" in text
    assert "agree within the stated uncertainties: 1 of 1" in text
    assert "too few to quote an accuracy" in text
