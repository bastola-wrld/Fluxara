# fluxara/retrieval/varon.py
"""
Turn two Sentinel 2 images into a methane leak rate. Pure maths, no database,
no downloads, so every step can be tested with made up images.

The method is from Varon et al. 2021, "High-frequency monitoring of anomalous
methane point sources with multispectral Sentinel-2 satellite observations",
Atmospheric Measurement Techniques, doi:10.5194/amt-14-2771-2021.

The idea in plain words
    Methane absorbs light in band 12 (2190 nm) and hardly at all in band 11
    (1610 nm). Over a plume, band 12 gets a little darker and band 11 does
    not. So we compare the two bands. The ground also changes the two bands
    (sand, rock, roads), so we do the same on an earlier image of the same
    place with no plume and subtract it. What is left is methane plus noise.

The steps
    1. band_ratio          c, the number that makes c x B12 match B11 on average
    2. fractional_signal   dR = (c x B12 - B11) / B11          ("MBSP")
    3. mbmp                dR on the plume day minus dR on the reference day
    4. column_enhancement  dR  ->  extra methane in mol per square metre
    5. plume_candidates    the brightest 5% of pixels, cleaned up, as blobs
    6. measure_plume       mass in the blob (IME)  ->  kg per hour

A worked example you can check by hand (it is also a test)
    Sentinel 2A, sun 30 degrees from overhead, satellite 5 degrees off straight
    down. Air mass factor = 1/cos(30) + 1/cos(5) = 2.159.
    A pixel with dR = -0.01 holds
        0.01 / 0.029 x 0.65 x (2.305 / 2.159) = 0.239 mol/m2 of extra methane.
    80 such pixels of 20 m x 20 m hold
        80 x 400 m2 x 0.239 mol/m2 x 0.01604 kg/mol = 123 kg       (the IME).
    The plume length is the square root of its area: sqrt(32,000) = 179 m.
    With a 10 m wind of 3 m/s the effective wind is 0.33 x 3 + 0.45 = 1.44 m/s.
        rate = 1.44 x 123 / 179 = 0.99 kg/s = about 3,560 kg per hour.

What this method cannot do
    * It only sees big leaks, roughly 1 to 3 tonnes per hour and up, and only
      over bright, even ground (desert, bare soil). Not over water, snow,
      forest or cities.
    * Step 4 uses a straight line. Real absorption flattens off for very big
      plumes, so very big plumes are underestimated.
    * The wind is the biggest source of error in the rate.
"""
import math

import numpy as np
from scipy import ndimage

METHOD = "varon2021_mbmp"
METHOD_VERSION = "1.0"

PIXEL_SIZE_M = 20.0                 # bands 11 and 12 have 20 m pixels
PIXEL_AREA_M2 = PIXEL_SIZE_M ** 2
METHANE_KG_PER_MOL = 0.01604

# How much dR changes when the methane column doubles (Varon 2021, section 2).
# Measured for the sun 40 degrees from overhead and the satellite looking
# straight down. There is no published number for Sentinel 2C, so we refuse it
# instead of guessing.
DOUBLED_COLUMN_MOL_M2 = 0.65
SIGNAL_AT_DOUBLED_COLUMN = {"sentinel-2a": -0.029, "sentinel-2b": -0.022}
REFERENCE_SUN_ZENITH_DEG = 40.0
REFERENCE_VIEW_ZENITH_DEG = 0.0

# Our own choices, not from the paper.
MIN_REFLECTANCE = 0.05      # darker than this is water or shadow
MAX_REFLECTANCE = 0.60      # brighter than this is cloud or snow
PLUME_PERCENTILE = 95       # a plume pixel is in the top 5% (this one is from the paper)
MIN_PLUME_PIXELS = 10       # smaller blobs are treated as noise
MIN_SNR = 3.0               # the plume must stand this far above the noise
WIND_ERROR_MS = 1.5         # how wrong we assume the 10 m wind can be

# Control spot test: is the blob at the site stronger than blobs elsewhere?
CONTROL_SPACING_M = 1000    # one control spot every 1 km
CONTROL_MIN_DISTANCE_M = 3000   # at least this far from the site
MIN_CONTROL_SPOTS = 20
MAX_FALSE_ALARM_SHARE = 0.05    # the site must beat 95% of the control spots


class CannotRetrieve(Exception):
    """The image cannot be used. The message says why, in plain words."""


# ── Step 0: geometry and calibration ─────────────────────────────────────────

def air_mass_factor(sun_zenith_deg, view_zenith_deg):
    """
    How much longer the light's path through the air is than straight down
    and back up. A low sun means a longer path, so more absorption for the
    same amount of methane.
    """
    down = 1 / math.cos(math.radians(sun_zenith_deg))
    up = 1 / math.cos(math.radians(view_zenith_deg))
    return down + up


def sensitivity(platform, sun_zenith_deg, view_zenith_deg):
    """
    How much dR changes for each extra mol of methane per square metre.
    A negative number, because methane makes band 12 darker.
    """
    platform = (platform or "").lower()
    if platform not in SIGNAL_AT_DOUBLED_COLUMN:
        raise CannotRetrieve(f"no methane calibration for satellite '{platform or 'unknown'}'")
    if not 0 <= sun_zenith_deg < 80:
        raise CannotRetrieve(f"sun too low (zenith angle {sun_zenith_deg:.0f} degrees)")

    per_mol_at_reference = SIGNAL_AT_DOUBLED_COLUMN[platform] / DOUBLED_COLUMN_MOL_M2
    reference_path = air_mass_factor(REFERENCE_SUN_ZENITH_DEG, REFERENCE_VIEW_ZENITH_DEG)
    this_path = air_mass_factor(sun_zenith_deg, view_zenith_deg)
    return per_mol_at_reference * this_path / reference_path


# ── Steps 1 to 4: images -> methane map ──────────────────────────────────────

def usable_pixels(b11, b12):
    """True where both bands have a sensible value: no cloud, water, shadow or gap."""
    with np.errstate(invalid="ignore"):
        return (np.isfinite(b11) & np.isfinite(b12)
                & (b11 >= MIN_REFLECTANCE) & (b11 <= MAX_REFLECTANCE)
                & (b12 > 0))


def band_ratio(b11, b12, usable):
    """
    c, the number that makes c x B12 fit B11 best over the whole crop
    (least squares). It removes the overall brightness difference between
    the two bands.
    """
    top = np.sum(b11[usable] * b12[usable])
    bottom = np.sum(b12[usable] ** 2)
    if bottom == 0:
        raise CannotRetrieve("band 12 is empty")
    return top / bottom


def fractional_signal(b11, b12, usable):
    """dR = (c x B12 - B11) / B11. Negative where band 12 is darker than expected."""
    c = band_ratio(b11, b12, usable)
    signal = np.full(b11.shape, np.nan)
    signal[usable] = (c * b12[usable] - b11[usable]) / b11[usable]
    return signal


def mbmp(target_b11, target_b12, reference_b11, reference_b12):
    """
    dR on the day we are checking minus dR on the reference day.
    Returns (signal, usable). The ground cancels out, methane stays.
    """
    if target_b11.shape != reference_b11.shape:
        raise CannotRetrieve("the two images do not line up")
    usable = (usable_pixels(target_b11, target_b12)
              & usable_pixels(reference_b11, reference_b12))
    if not usable.any():
        raise CannotRetrieve("no usable pixels")
    signal = (fractional_signal(target_b11, target_b12, usable)
              - fractional_signal(reference_b11, reference_b12, usable))
    return signal, usable


def column_enhancement(signal, usable, platform, sun_zenith_deg, view_zenith_deg):
    """
    dR -> extra methane in mol per square metre. The typical (median) pixel is
    set to zero, so the map shows methane above the local background.
    """
    column = signal / sensitivity(platform, sun_zenith_deg, view_zenith_deg)
    return column - np.nanmedian(column[usable])


def image_to_column(target_b11, target_b12, reference_b11, reference_b12,
                    platform, sun_zenith_deg, view_zenith_deg):
    """Steps 1 to 4 in one call. Returns (methane map, usable pixels)."""
    signal, usable = mbmp(target_b11, target_b12, reference_b11, reference_b12)
    column = column_enhancement(signal, usable, platform, sun_zenith_deg, view_zenith_deg)
    return column, usable


# ── Step 5: find blobs ───────────────────────────────────────────────────────

def plume_candidates(column, usable):
    """
    Mark the top 5% of pixels, smooth the marks with a 3 x 3 median filter to
    drop single stray pixels, then number each connected group ("blob").
    Pixels that touch at a corner count as connected.
    Returns (labels, count). labels is 0 outside blobs and 1..count inside.
    """
    threshold = np.percentile(column[usable], PLUME_PERCENTILE)
    with np.errstate(invalid="ignore"):
        marked = usable & (column > threshold)
    marked = ndimage.median_filter(marked.astype(np.uint8), size=3).astype(bool) & usable
    return ndimage.label(marked, structure=np.ones((3, 3)))


def blob_sizes_and_strengths(column, labels, count):
    """
    For every blob: how many pixels, and its strength (the methane summed over
    its pixels, mol/m2). Blobs under MIN_PLUME_PIXELS get strength 0.
    Both arrays are indexed by blob number, entry 0 is unused.
    """
    numbers = np.arange(count + 1)
    sizes = ndimage.sum(np.ones_like(labels), labels, numbers)
    strengths = ndimage.sum(np.nan_to_num(column), labels, numbers)
    strengths[sizes < MIN_PLUME_PIXELS] = 0
    strengths[0] = 0
    return sizes, strengths


def distance_from(shape, row, col):
    """Distance in metres of every pixel from the pixel (row, col)."""
    rows, cols = np.indices(shape)
    return np.hypot(rows - row, cols - col) * PIXEL_SIZE_M


def strongest_blob_near(labels, strengths, row, col, max_distance_m):
    """
    The strongest blob with at least one pixel within max_distance_m of
    (row, col). Returns (blob number, strength), or (0, 0.0) if there is none.
    """
    close = distance_from(labels.shape, row, col) <= max_distance_m
    nearby = np.unique(labels[close])
    nearby = nearby[nearby > 0]
    if nearby.size == 0:
        return 0, 0.0
    best = nearby[np.argmax(strengths[nearby])]
    if strengths[best] <= 0:
        return 0, 0.0
    return int(best), float(strengths[best])


def find_plume_near(column, usable, row, col, max_distance_m):
    """
    Look for a plume near the site at (row, col).
    Returns (mask, strength). mask is None when nothing was found.
    """
    labels, count = plume_candidates(column, usable)
    _sizes, strengths = blob_sizes_and_strengths(column, labels, count)
    blob, strength = strongest_blob_near(labels, strengths, row, col, max_distance_m)
    if blob == 0:
        return None, 0.0
    return labels == blob, strength


# ── The control spot test ────────────────────────────────────────────────────

def control_spots(shape, row, col):
    """
    Places in the crop to compare the site against: a grid with one spot every
    1 km, keeping only spots at least 3 km from the site and not hugging the edge.
    """
    step = int(CONTROL_SPACING_M / PIXEL_SIZE_M)
    edge = step // 2
    spots = []
    for r in range(edge, shape[0] - edge + 1, step):
        for c in range(edge, shape[1] - edge + 1, step):
            if math.hypot(r - row, c - col) * PIXEL_SIZE_M >= CONTROL_MIN_DISTANCE_M:
                spots.append((r, c))
    return spots


def compare_with_control_spots(column, usable, row, col, max_distance_m):
    """
    Why this test exists
        The ground is never perfectly cancelled. What is left over is patchy,
        and a patch can look exactly like a plume, with a high signal to noise
        ratio. So we ask a simple question: if we pretend the site is
        somewhere else in the same image, how often do we find a blob as
        strong as the one at the real site? If the answer is "often", the blob
        at the site is just ground.

    Returns a dict:
        site_strength       strength of the strongest blob near the site
        control_count       how many control spots could be used
        control_blobs       (strength, pixels) of the strongest blob at each spot
        false_alarm_share   share of control spots with a blob at least as strong
    """
    labels, count = plume_candidates(column, usable)
    sizes, strengths = blob_sizes_and_strengths(column, labels, count)
    _blob, site_strength = strongest_blob_near(labels, strengths, row, col, max_distance_m)

    control_blobs = []   # (strength, pixels) of the strongest blob at each control spot
    for spot_row, spot_col in control_spots(column.shape, row, col):
        close = distance_from(column.shape, spot_row, spot_col) <= max_distance_m
        if usable[close].mean() < 0.5:
            continue   # mostly cloud or water here, not a fair comparison
        blob, strength = strongest_blob_near(labels, strengths, spot_row, spot_col, max_distance_m)
        control_blobs.append((strength, int(sizes[blob]) if blob else 0))

    as_strong = sum(1 for strength, _pixels in control_blobs if strength >= site_strength)
    share = as_strong / len(control_blobs) if control_blobs else None
    return {"site_strength": site_strength,
            "control_count": len(control_blobs),
            "control_blobs": control_blobs,
            "false_alarm_share": share}


# ── Step 6: noise, rate, uncertainty ─────────────────────────────────────────

def background_noise(column, usable, plume_mask=None):
    """
    How bumpy the methane map is where there is no plume, in mol/m2.
    Uses the median absolute deviation, which a few extreme pixels cannot fool.
    """
    background = usable if plume_mask is None else usable & ~plume_mask
    values = column[background]
    if values.size == 0:
        return float("nan")
    spread = np.median(np.abs(values - np.median(values)))
    return float(1.4826 * spread)


def effective_wind(wind_10m_ms):
    """The speed that carries the plume, from the 10 m wind (Varon 2021, eq. 12)."""
    return 0.33 * wind_10m_ms + 0.45


def rate_kg_hr(strength_mol_m2, pixels, wind_10m_ms):
    """Leak rate of a blob from its strength (methane summed over its pixels)."""
    mass_kg = strength_mol_m2 * PIXEL_AREA_M2 * METHANE_KG_PER_MOL
    length_m = math.sqrt(pixels * PIXEL_AREA_M2)
    return effective_wind(wind_10m_ms) * mass_kg / length_m * 3600


def measure_plume(column, mask, noise_mol_m2, wind_10m_ms):
    """
    From a plume mask to a leak rate.

        mass (IME)  = sum of methane over the plume pixels x pixel area x 0.01604 kg/mol
        length      = square root of the plume's area
        rate        = effective wind x mass / length

    The uncertainty combines two things: the wind may be wrong by
    WIND_ERROR_MS, and every pixel carries noise.
    """
    pixels = int(mask.sum())
    area_m2 = pixels * PIXEL_AREA_M2
    mass_kg = float(np.nansum(column[mask])) * PIXEL_AREA_M2 * METHANE_KG_PER_MOL
    length_m = math.sqrt(area_m2)
    wind = effective_wind(wind_10m_ms)
    rate_kg_hr = wind * mass_kg / length_m * 3600

    mass_noise_kg = noise_mol_m2 * math.sqrt(pixels) * PIXEL_AREA_M2 * METHANE_KG_PER_MOL
    share_from_noise = mass_noise_kg / mass_kg if mass_kg > 0 else float("inf")
    share_from_wind = 0.33 * WIND_ERROR_MS / wind
    uncertainty_kg_hr = rate_kg_hr * math.hypot(share_from_noise, share_from_wind)

    peak = np.nanmax(np.where(mask, column, -np.inf))
    peak_row, peak_col = np.argwhere(np.where(mask, column, -np.inf) == peak)[0]

    return {
        "pixels": pixels,
        "mass_kg": mass_kg,
        "length_m": length_m,
        "effective_wind_ms": wind,
        "rate_kg_hr": rate_kg_hr,
        "uncertainty_kg_hr": uncertainty_kg_hr,
        "snr": mass_kg / mass_noise_kg if mass_noise_kg > 0 else float("inf"),
        "peak_mol_m2": float(peak),
        "peak_row": int(peak_row),
        "peak_col": int(peak_col),
    }


def detection_limit_kg_hr(noise_mol_m2, wind_10m_ms, control_blobs=()):
    """
    The smallest leak this image could have shown. The larger of two numbers:

    1. From pixel noise: the smallest blob we accept (MIN_PLUME_PIXELS pixels)
       with every pixel MIN_SNR times above the noise.
    2. From the ground: the leak rate that the false blobs at the control
       spots would have been reported as. A real leak has to beat 95% of them.
    """
    strength = MIN_SNR * noise_mol_m2 * MIN_PLUME_PIXELS
    limit = rate_kg_hr(strength, MIN_PLUME_PIXELS, wind_10m_ms)

    false_rates = [rate_kg_hr(strength, pixels, wind_10m_ms) if pixels else 0.0
                   for strength, pixels in control_blobs]
    if false_rates:
        limit = max(limit, float(np.percentile(false_rates, 100 * (1 - MAX_FALSE_ALARM_SHARE))))
    return limit


# ── Does the plume point downwind? ───────────────────────────────────────────

def wind_agreement(column, mask, row, col, wind_from_deg):
    """
    A real plume is blown away from its source, so it should stretch downwind.
    Compares the direction from the site to the plume's centre of mass with
    the direction the wind blows towards.

    Returns "consistent", "unclear" or "inconsistent".
    """
    weights = np.where(mask, np.nan_to_num(column), 0.0)
    weights = np.clip(weights, 0, None)
    if weights.sum() == 0:
        return "unclear"
    rows, cols = np.indices(mask.shape)
    centre_row = (rows * weights).sum() / weights.sum()
    centre_col = (cols * weights).sum() / weights.sum()

    # Image rows grow southwards, columns grow eastwards.
    east = centre_col - col
    north = row - centre_row
    if math.hypot(east, north) < 2:   # the plume sits on top of the site
        return "unclear"

    blowing_to = math.radians((wind_from_deg + 180) % 360)
    wind_east, wind_north = math.sin(blowing_to), math.cos(blowing_to)
    cosine = (east * wind_east + north * wind_north) / math.hypot(east, north)
    if cosine > 0.5:
        return "consistent"
    if cosine < 0:
        return "inconsistent"
    return "unclear"
