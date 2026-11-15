"""The maths of the Sentinel 2 methane method, on made up images."""
import math

import numpy as np
import pytest

import synthetic
from fluxara.retrieval import pipeline, varon
from synthetic import PLATFORM, SITE, SUN_ZENITH, VIEW_ZENITH

WIND_SPEED, WIND_FROM = 3.0, 270.0     # 3 m/s from the west, so plumes go east


def analyse(target, reference):
    return pipeline.analyse(*target, *reference, PLATFORM, SUN_ZENITH, VIEW_ZENITH,
                            WIND_SPEED, WIND_FROM, SITE, SITE)


def two_days(seed, change=0.0):
    """A reference day and a later day of the same ground. change > 0 means the
    ground changed in patches between the two days."""
    reference = synthetic.with_noise(*synthetic.ground(seed), seed + 1)
    target = synthetic.with_noise(*synthetic.ground(seed + 5, change), seed + 2)
    return target, reference


def test_worked_example_from_the_docstring():
    assert varon.air_mass_factor(30, 5) == pytest.approx(2.159, abs=0.001)
    per_mol = varon.sensitivity("sentinel-2a", 30, 5)
    assert -0.01 / per_mol == pytest.approx(0.239, abs=0.001)

    column = np.zeros((50, 50))
    mask = np.zeros((50, 50), dtype=bool)
    mask[10:18, 10:20] = True                      # 80 pixels
    column[mask] = -0.01 / per_mol
    plume = varon.measure_plume(column, mask, noise_mol_m2=0.05, wind_10m_ms=3.0)
    assert plume["pixels"] == 80
    assert plume["mass_kg"] == pytest.approx(123, abs=1)
    assert plume["length_m"] == pytest.approx(179, abs=1)
    assert plume["effective_wind_ms"] == pytest.approx(1.44)
    assert plume["rate_kg_hr"] == pytest.approx(3560, abs=20)


def test_sensitivity_depends_on_satellite_and_sun():
    assert varon.sensitivity("sentinel-2a", 40, 0) == pytest.approx(-0.029 / 0.65)
    assert varon.sensitivity("Sentinel-2B", 40, 0) == pytest.approx(-0.022 / 0.65)
    # A lower sun means a longer path, so a stronger signal per mol.
    assert abs(varon.sensitivity("sentinel-2a", 60, 0)) > abs(varon.sensitivity("sentinel-2a", 20, 0))
    with pytest.raises(varon.CannotRetrieve, match="sentinel-2c"):
        varon.sensitivity("sentinel-2c", 40, 0)
    with pytest.raises(varon.CannotRetrieve, match="sun too low"):
        varon.sensitivity("sentinel-2a", 85, 0)


def test_cloud_water_and_gaps_are_not_usable():
    b11 = np.array([[0.30, 0.02, 0.80, np.nan]])
    b12 = np.array([[0.25, 0.02, 0.70, 0.25]])
    assert varon.usable_pixels(b11, b12).tolist() == [[True, False, False, False]]


def test_same_ground_on_both_days_gives_no_plume():
    result = analyse(*two_days(seed=0))
    assert result["status"] == "no_plume" and result["reason"] is None
    # With clean ground the smallest visible leak is between 1 and 3 t/h.
    assert 1000 < result["detection_limit_kg_hr"] < 3000


@pytest.mark.parametrize("peak", [0.5, 1.0, 2.0])
def test_a_real_plume_is_found_and_measured(peak):
    target, reference = two_days(seed=0)
    truth = synthetic.plume_column(peak, WIND_FROM)
    target = (target[0], synthetic.add_plume(target[1], truth))

    result = analyse(target, reference)
    assert result["status"] == "plume_detected"
    plume = result["plume"]
    expected = synthetic.true_rate_kg_hr(truth, WIND_SPEED)
    assert plume["rate_kg_hr"] == pytest.approx(expected, rel=0.25)
    assert abs(plume["rate_kg_hr"] - expected) < plume["uncertainty_kg_hr"]
    assert result["wind_agreement"] == "consistent"
    assert result["distance_to_plume_m"] < 100
    assert result["false_alarm_share"] == 0.0
    # The peak is at the source, in the middle of the crop.
    assert abs(plume["peak_row"] - SITE) <= 3 and abs(plume["peak_col"] - SITE) <= 3


def test_plume_against_the_wind_is_flagged():
    target, reference = two_days(seed=0)
    truth = synthetic.plume_column(1.0, wind_from_deg=90)        # drawn going west
    target = (target[0], synthetic.add_plume(target[1], truth))
    result = analyse(target, reference)                          # but the wind goes east
    assert result["status"] == "plume_detected"
    assert result["wind_agreement"] == "inconsistent"


def test_patchy_ground_does_not_become_a_plume():
    """
    The bug this guards against: when the ground changes in patches between
    the two days, a patch near the site looks like a plume with a high signal
    to noise ratio. The control spot test must reject nearly all of them.
    """
    outcomes = [analyse(*two_days(seed, change=0.02))["status"] for seed in range(0, 200, 10)]
    assert outcomes.count("plume_detected") <= 3          # 20 tries, about 1 expected
    assert outcomes.count("no_plume") >= 17


def test_patchy_ground_raises_the_detection_limit():
    clean = analyse(*two_days(seed=0))["detection_limit_kg_hr"]
    patchy = analyse(*two_days(seed=0, change=0.02))["detection_limit_kg_hr"]
    assert patchy > 5 * clean


def test_mostly_cloud_is_unusable():
    target, reference = two_days(seed=0)
    cloudy = target[0].copy()
    cloudy[:, : int(cloudy.shape[1] * 0.7)] = 0.9
    result = analyse((cloudy, target[1]), reference)
    assert result["status"] == "unusable" and "clear ground" in result["reason"]


def test_identical_images_are_unusable():
    ground = synthetic.ground(0)
    result = analyse(ground, ground)
    assert result["status"] == "unusable" and "identical" in result["reason"]


def test_unknown_satellite_is_unusable():
    target, reference = two_days(seed=0)
    result = pipeline.analyse(*target, *reference, "sentinel-2c", SUN_ZENITH, VIEW_ZENITH,
                              WIND_SPEED, WIND_FROM, SITE, SITE)
    assert result["status"] == "unusable" and "calibration" in result["reason"]


def test_control_spots_stay_away_from_the_site():
    spots = varon.control_spots((500, 500), 250, 250)
    assert len(spots) >= 60
    assert all(math.hypot(r - 250, c - 250) * 20 >= 3000 for r, c in spots)


def test_detection_limit_grows_with_noise_and_wind():
    base = varon.detection_limit_kg_hr(0.1, 3.0)
    assert varon.detection_limit_kg_hr(0.2, 3.0) == pytest.approx(2 * base)
    assert varon.detection_limit_kg_hr(0.1, 6.0) > base
