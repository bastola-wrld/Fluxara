# fluxara/retrieval/pipeline.py
"""
Check a place for methane in Sentinel 2 images, and save what we find.

The file has three layers, from the inside out:

    analyse()           two pairs of image crops and a wind  ->  an outcome
                        (pure maths, no downloads, no database)
    check_point()       picks the reference image, downloads the bands, gets
                        the wind, then calls analyse()
    observe() and       do that for a facility in the database and save every
    run_for_facility()  result in site_observations and plume_detections

Every check ends in one of three outcomes:

    plume_detected   a plume was found and measured
    no_plume         the image was good, nothing above the detection limit
    unusable         the image could not be used, with the reason
"""
import logging
import math
from datetime import timedelta

from shapely.geometry import Point
from sqlalchemy import func

from fluxara.database.models import Facility, PlumeDetection, SatelliteScene, SiteObservation
from fluxara.ingest.common import now_utc, save_rows
from fluxara.ingest.sentinel2 import SOURCE as SCENE_SOURCE
from fluxara.retrieval import bands, varon
from fluxara.retrieval.wind import ATTRIBUTION as WIND_ATTRIBUTION

log = logging.getLogger("fluxara.retrieval")

SOURCE = "fluxara_s2"            # our own plumes in plume_detections
LICENCE = "Fluxara analysis of open Copernicus data"

HALF_SIZE_M = 5000               # we look at a 10 km x 10 km square around the site
MAX_DISTANCE_M = 1000            # a plume must start within 1 km of the site
MIN_USABLE_FRACTION = 0.5        # at least half the square must be clear ground
MAX_REFERENCE_GAP_DAYS = 45      # the reference image is at most this much older
MAX_REFERENCE_CLOUD_PCT = 10     # and nearly cloud free


# ── Small helpers ────────────────────────────────────────────────────────────

def outcome(status, reason=None, **details):
    """One result, as a dict. Missing details are simply not there."""
    return {"status": status, "reason": reason, **details}


def sun_zenith_deg(scene, lat, lon):
    """Angle of the sun from straight overhead when the image was taken."""
    if scene.sun_elevation_deg is not None:
        return 90.0 - scene.sun_elevation_deg
    return 90.0 - sun_elevation_from_time(scene.acquired_at, lat, lon)


def sun_elevation_from_time(when, lat, lon):
    """
    Height of the sun above the horizon, worked out from the date, the time
    and the place. Good to about a degree, which is plenty here. Only used
    when the image catalogue does not give the angle.
    """
    day = when.timetuple().tm_yday
    hours = when.hour + when.minute / 60 + when.second / 3600
    year_angle = 2 * math.pi / 365 * (day - 1 + (hours - 12) / 24)
    tilt = (0.006918 - 0.399912 * math.cos(year_angle) + 0.070257 * math.sin(year_angle)
            - 0.006758 * math.cos(2 * year_angle) + 0.000907 * math.sin(2 * year_angle))
    clock_fix_minutes = 229.18 * (0.000075 + 0.001868 * math.cos(year_angle)
                                  - 0.032077 * math.sin(year_angle)
                                  - 0.014615 * math.cos(2 * year_angle)
                                  - 0.040849 * math.sin(2 * year_angle))
    sun_time_minutes = hours * 60 + clock_fix_minutes + 4 * lon
    hour_angle = math.radians(sun_time_minutes / 4 - 180)
    lat_rad = math.radians(lat)
    sine = (math.sin(lat_rad) * math.sin(tilt)
            + math.cos(lat_rad) * math.cos(tilt) * math.cos(hour_angle))
    return math.degrees(math.asin(max(-1.0, min(1.0, sine))))


def supported(scene):
    return (scene.platform or "").lower() in varon.SIGNAL_AT_DOUBLED_COLUMN


def choose_reference(target, candidates):
    """
    Pick the earlier image we subtract from the target.

    It must be from a satellite we have a calibration for, the same tile (so
    the pixels line up exactly), earlier than the target but not more than 45
    days, and nearly cloud free. Among those we prefer, in this order: the
    same orbit (same viewing direction, so the ground looks the same), less
    cloud, and closer in time.
    """
    def allowed(scene):
        gap = target.acquired_at - scene.acquired_at
        return (supported(scene)
                and scene.tile_id == target.tile_id
                and timedelta(0) < gap <= timedelta(days=MAX_REFERENCE_GAP_DAYS)
                and scene.cloud_cover_pct is not None
                and scene.cloud_cover_pct <= MAX_REFERENCE_CLOUD_PCT)

    def how_good(scene):
        same_orbit = (scene.relative_orbit is not None
                      and scene.relative_orbit == target.relative_orbit)
        return (same_orbit, -scene.cloud_cover_pct, scene.acquired_at)

    options = [scene for scene in candidates if allowed(scene)]
    return max(options, key=how_good) if options else None


# ── Layer 1: the analysis ────────────────────────────────────────────────────

def analyse(target_b11, target_b12, reference_b11, reference_b12,
            platform, sun_zenith, view_zenith, wind_speed_ms, wind_from_deg,
            site_row, site_col):
    """
    Decide what one image shows at the site. Returns an outcome dict.
    The numbered steps are the whole decision, in order.
    """
    # 1. Is enough of the square clear ground on both days?
    usable = (varon.usable_pixels(target_b11, target_b12)
              & varon.usable_pixels(reference_b11, reference_b12))
    usable_fraction = float(usable.mean())
    if usable_fraction < MIN_USABLE_FRACTION:
        return outcome("unusable", f"only {usable_fraction:.0%} of the area is clear ground",
                       usable_fraction=usable_fraction)

    # 2. Make the methane map and look for a blob near the site.
    try:
        column, usable = varon.image_to_column(
            target_b11, target_b12, reference_b11, reference_b12,
            platform, sun_zenith, view_zenith)
    except varon.CannotRetrieve as problem:
        return outcome("unusable", str(problem), usable_fraction=usable_fraction)
    mask, _strength = varon.find_plume_near(column, usable, site_row, site_col, MAX_DISTANCE_M)

    # 3. How noisy is the map, and what is the smallest leak it could show?
    noise = varon.background_noise(column, usable, mask)
    if not noise > 0:
        return outcome("unusable", "the two images are identical",
                       usable_fraction=usable_fraction)
    control = varon.compare_with_control_spots(column, usable, site_row, site_col, MAX_DISTANCE_M)
    limit = varon.detection_limit_kg_hr(noise, wind_speed_ms, control["control_blobs"])
    common = dict(usable_fraction=usable_fraction, noise_mol_m2=noise,
                  detection_limit_kg_hr=limit, column=column, usable=usable)

    # 4. No blob near the site at all.
    if mask is None:
        return outcome("no_plume", **common)

    # 5. The control spot test: is this blob stronger than blobs elsewhere?
    if control["control_count"] < varon.MIN_CONTROL_SPOTS:
        return outcome("unusable", "not enough clear ground around the site to compare against",
                       usable_fraction=usable_fraction)
    if control["false_alarm_share"] > varon.MAX_FALSE_ALARM_SHARE:
        return outcome("no_plume",
                       f"a blob near the site is no stronger than the ground pattern "
                       f"({control['false_alarm_share']:.0%} of control spots match it)",
                       **common)

    # 6. Is it clearly above the pixel noise?
    plume = varon.measure_plume(column, mask, noise, wind_speed_ms)
    if plume["snr"] < varon.MIN_SNR:
        return outcome("no_plume", f"a blob near the site is too faint (SNR {plume['snr']:.1f})",
                       **common)

    # 7. A plume. Add where it is and whether it points downwind.
    distance_m = float(varon.distance_from(mask.shape, site_row, site_col)[mask].min())
    return outcome("plume_detected", plume=plume, mask=mask,
                   distance_to_plume_m=distance_m,
                   false_alarm_share=control["false_alarm_share"],
                   wind_agreement=varon.wind_agreement(column, mask, site_row, site_col,
                                                       wind_from_deg),
                   **common)


# ── Layer 2: one place, one image ────────────────────────────────────────────

def check_point(lat, lon, target, candidates, fetcher, wind):
    """
    Check (lat, lon) in the image `target`. `candidates` are other images of
    the same place to pick the reference from. Works on any object that looks
    like a SatelliteScene, so it does not need the database.
    """
    if not supported(target):
        return outcome("unusable", f"no methane calibration for satellite '{target.platform}'")
    reference = choose_reference(target, candidates)
    if reference is None:
        return outcome("unusable", f"no clear earlier image within {MAX_REFERENCE_GAP_DAYS} days")

    crops = {}
    for name, scene in (("target", target), ("reference", reference)):
        for band in ("B11", "B12"):
            crop = bands.scene_crop(fetcher, scene, band, lat, lon, HALF_SIZE_M)
            if crop is None:
                return outcome("unusable", "the site is too close to the edge of the image",
                               reference=reference)
            crops[name, band] = crop

    speed, comes_from = wind.at(lat, lon, target.acquired_at)
    crop = crops["target", "B12"]
    result = analyse(
        crops["target", "B11"].data, crops["target", "B12"].data,
        crops["reference", "B11"].data, crops["reference", "B12"].data,
        target.platform, sun_zenith_deg(target, lat, lon), target.view_incidence_deg or 0.0,
        speed, comes_from, crop.site_row, crop.site_col)

    result.update(reference=reference, crop=crop, wind_speed_10m_ms=speed,
                  wind_from_deg=comes_from, wind_source=wind.source)
    return result


# ── Layer 3: facilities and the database ─────────────────────────────────────

def scenes_over(session, facility, start, end):
    """Sentinel 2 images in our catalogue that cover the facility, oldest first."""
    # Ask the database for the facility's point. It is filled in there by a
    # trigger, so the Python object may not have it yet.
    point = (session.query(Facility.geom).filter(Facility.id == facility.id)
             .scalar_subquery())
    return (session.query(SatelliteScene)
            .filter(SatelliteScene.source == SCENE_SOURCE)
            .filter(SatelliteScene.acquired_at >= start, SatelliteScene.acquired_at <= end)
            .filter(func.ST_Contains(SatelliteScene.footprint, point))
            .order_by(SatelliteScene.acquired_at)
            .all())


def one_image_per_pass(scenes):
    """
    One pass of the satellite is often cut into two overlapping tiles, which
    would count the same moment twice. Keep the least cloudy tile of each pass.
    """
    best = {}
    for scene in scenes:
        key = ((scene.platform or "").lower(), scene.acquired_at.date())
        cloud = scene.cloud_cover_pct if scene.cloud_cover_pct is not None else 100
        if key not in best or cloud < best[key][0]:
            best[key] = (cloud, scene)
    return sorted((scene for _cloud, scene in best.values()), key=lambda s: s.acquired_at)


def save_plume(session, facility, scene, result):
    """Write the plume into plume_detections and return its id."""
    plume, crop = result["plume"], result["crop"]
    lon, lat = bands.pixel_lonlat(crop, plume["peak_row"], plume["peak_col"])
    outline = bands.mask_outline_lonlat(crop, result["mask"])
    source_id = f"{scene.source_id}:facility-{facility.id}"

    row = {
        "source": SOURCE,
        "source_id": source_id,
        "instrument": "MSI",
        "product": varon.METHOD,
        "product_version": varon.METHOD_VERSION,
        "licence": LICENCE,
        "attribution": (f"Fluxara analysis. {scene.attribution}. {WIND_ATTRIBUTION}. "
                        "Method: Varon et al. 2021, doi:10.5194/amt-14-2771-2021"),
        "commercial_use_allowed": True,
        "gas": "CH4",
        "observed_at": scene.acquired_at,
        "geom": f"SRID=4326;{Point(lon, lat).wkt}",
        "geom_kind": "max_enhancement",
        "outline": f"SRID=4326;{outline.wkt}" if outline is not None else None,
        "cloud_cover_pct": scene.cloud_cover_pct,
        "emission_rate_kg_hr": plume["rate_kg_hr"],
        "emission_uncertainty_kg_hr": plume["uncertainty_kg_hr"],
        "wind_speed_ms": result["wind_speed_10m_ms"],
        "wind_speed_std_ms": varon.WIND_ERROR_MS,
        "wind_source": result["wind_source"],
        "fetch_length_m": plume["length_m"],
        "raw_properties": {
            "facility_id": facility.id,
            "scene": scene.source_id,
            "reference_scene": result["reference"].source_id,
            "pixels": plume["pixels"],
            "mass_kg": plume["mass_kg"],
            "snr": plume["snr"],
            "peak_mol_m2": plume["peak_mol_m2"],
            "effective_wind_ms": plume["effective_wind_ms"],
            "false_alarm_share": result["false_alarm_share"],
        },
    }
    save_rows(session, PlumeDetection, [row], update_columns=[c for c in row
                                                              if c not in ("source", "source_id")])
    return (session.query(PlumeDetection.id)
            .filter_by(source=SOURCE, source_id=source_id).scalar())


def save_observation(session, facility, scene, result):
    """
    Save the check, replacing an earlier check of the same image. If the
    earlier check had a plume and this one does not, the old plume is removed.
    """
    observation = (session.query(SiteObservation)
                   .filter_by(facility_id=facility.id, scene_id=scene.id, method=varon.METHOD)
                   .one_or_none())
    old_plume_id = observation.plume_detection_id if observation else None

    plume_id = None
    if result["status"] == "plume_detected":
        plume_id = save_plume(session, facility, scene, result)

    if observation is None:
        observation = SiteObservation(facility_id=facility.id, scene_id=scene.id,
                                      method=varon.METHOD)

    reference = result.get("reference")
    observation.method_version = varon.METHOD_VERSION
    observation.status = result["status"]
    observation.reason = result.get("reason")
    observation.observed_at = scene.acquired_at
    observation.reference_scene_id = getattr(reference, "id", None)
    observation.usable_fraction = result.get("usable_fraction")
    observation.noise_mol_m2 = result.get("noise_mol_m2")
    observation.detection_limit_kg_hr = result.get("detection_limit_kg_hr")
    observation.wind_speed_10m_ms = result.get("wind_speed_10m_ms")
    observation.wind_from_deg = result.get("wind_from_deg")
    observation.wind_source = result.get("wind_source")
    observation.plume_detection_id = plume_id
    observation.distance_to_plume_m = result.get("distance_to_plume_m")
    observation.wind_agreement = result.get("wind_agreement")
    observation.updated_at = now_utc()
    session.add(observation)
    session.flush()

    if old_plume_id and old_plume_id != plume_id:
        session.query(PlumeDetection).filter_by(id=old_plume_id, source=SOURCE).delete()
    return observation


def observe(session, facility, scene, candidates, fetcher, wind):
    """Check one facility in one image and save the result. Returns the outcome."""
    result = check_point(facility.lat, facility.lon, scene, candidates, fetcher, wind)
    save_observation(session, facility, scene, result)
    return result


def run_for_facility(session, facility_id, start, end, fetcher, wind, max_cloud_pct=30.0):
    """
    Check every image of a facility between start and end.
    Each image is saved as soon as it is done, so stopping half way loses
    nothing. Returns a count of each outcome, plus "failed" for images that
    hit an error (a download that broke, wind not published yet).
    """
    facility = session.get(Facility, facility_id)
    if facility is None:
        raise ValueError(f"No facility with id {facility_id}")

    earliest_reference = start - timedelta(days=MAX_REFERENCE_GAP_DAYS)
    candidates = scenes_over(session, facility, earliest_reference, end)
    targets = one_image_per_pass(
        scene for scene in candidates
        if scene.acquired_at >= start
        and (scene.cloud_cover_pct is None or scene.cloud_cover_pct <= max_cloud_pct))

    counts = {"plume_detected": 0, "no_plume": 0, "unusable": 0, "failed": 0}
    for number, scene in enumerate(targets, start=1):
        try:
            result = observe(session, facility, scene, candidates, fetcher, wind)
            session.commit()
        except bands.LoginFailed:
            raise    # the login is wrong for every image, so stop now
        except Exception as error:
            session.rollback()
            counts["failed"] += 1
            log.warning("[%s/%s] %s failed: %s: %s", number, len(targets),
                        scene.acquired_at.date(), type(error).__name__, error)
            continue

        counts[result["status"]] += 1
        log.info("[%s/%s] %s %s%s", number, len(targets), scene.acquired_at.date(),
                 result["status"], f" ({result['reason']})" if result.get("reason") else "")
    return counts
