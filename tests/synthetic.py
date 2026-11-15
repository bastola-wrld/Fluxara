"""
Made up Sentinel 2 crops for tests: bright ground, optional patchy texture,
sensor noise, and an optional methane plume blown downwind from the centre.
"""
import math

import numpy as np
from scipy import ndimage

from fluxara.retrieval import varon

SIZE = 500            # 500 pixels of 20 m = the 10 km square the pipeline uses
SITE = SIZE // 2
PLATFORM = "sentinel-2a"
SUN_ZENITH, VIEW_ZENITH = 30.0, 5.0


def ground(seed, texture=0.0, size=SIZE):
    """
    Band 11 and band 12 of bare ground. texture > 0 adds patches a few hundred
    metres wide whose colour differs between the two bands, the way real rock
    and sand do.
    """
    rng = np.random.default_rng(seed)
    b11 = np.full((size, size), 0.35)
    b12 = np.full((size, size), 0.30)
    if texture:
        patches = ndimage.gaussian_filter(rng.normal(size=(size, size)), 8)
        patches /= patches.std()
        b11 = b11 * (1 + 0.5 * texture * patches)
        b12 = b12 * (1 - 0.5 * texture * patches)
    return b11, b12


def with_noise(b11, b12, seed, noise=0.002):
    rng = np.random.default_rng(seed)
    return (b11 * (1 + rng.normal(scale=noise, size=b11.shape)),
            b12 * (1 + rng.normal(scale=noise, size=b12.shape)))


def plume_column(peak_mol_m2, wind_from_deg, length_px=40, width_px=4, size=SIZE):
    """A methane plume in mol/m2, starting at the centre and stretching downwind."""
    to = math.radians((wind_from_deg + 180) % 360)
    east, north = math.sin(to), math.cos(to)
    rows, cols = np.indices((size, size))
    dx, dy = cols - size // 2, (size // 2) - rows        # east, north in pixels
    along = dx * east + dy * north
    across = -dx * north + dy * east
    shape = np.exp(-0.5 * (across / width_px) ** 2) * np.exp(-np.clip(along, 0, None) / length_px)
    shape[along < 0] = 0
    return peak_mol_m2 * shape


def add_plume(b12, column):
    """Darken band 12 the way that much methane would."""
    per_mol = varon.sensitivity(PLATFORM, SUN_ZENITH, VIEW_ZENITH)
    return b12 * (1 + per_mol * column)


def true_rate_kg_hr(column, wind_10m_ms):
    """The leak rate the method should report for this plume."""
    marked = column > 0.05 * column.max()
    mass = column[marked].sum() * varon.PIXEL_AREA_M2 * varon.METHANE_KG_PER_MOL
    length = math.sqrt(marked.sum() * varon.PIXEL_AREA_M2)
    return varon.effective_wind(wind_10m_ms) * mass / length * 3600
