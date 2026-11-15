# fluxara/ingest/sentinel2.py
"""
A list of Sentinel 2 images that cover each facility.

What Sentinel 2 is
    Two European satellites that photograph the whole Earth every few days at
    20 m resolution. Two of its bands, B11 and B12, are in the shortwave
    infrared. Methane absorbs light in B12 but hardly at all in B11, which is
    how we will spot plumes (that is the week 2 job).

What this file does
    It only records which images exist: when they were taken, how cloudy they
    were, the area they cover, and the links to the B11 and B12 files.
    It does not download any pixels.

Searching is free and needs no account. Downloading the band files later
needs a free Copernicus Data Space account.
"""
import logging
import math
from datetime import datetime, timezone

from shapely.geometry import shape

from fluxara.database.models import Facility, SatelliteScene
from fluxara.ingest.common import HTTP_TIMEOUT, ingestion_run, make_http_session, save_rows

log = logging.getLogger("fluxara.ingest.sentinel2")

SOURCE = "sentinel-2-l1c"  # L1C = the raw "top of atmosphere" images methane work uses
SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"
LICENCE = "Copernicus Sentinel data licence (free, full and open)"
BANDS_TO_KEEP = ["B11", "B12", "B8A", "B04", "B03", "B02", "TCI",
                 "granule_metadata", "product_metadata"]
MAX_PAGES = 50  # safety stop so a search can never run forever

# On a scene we already have, the search may refresh all of these.
SCENE_COLUMNS = ["platform", "acquired_at", "cloud_cover_pct", "tile_id",
                 "relative_orbit", "sun_elevation_deg", "view_incidence_deg",
                 "footprint", "assets", "licence", "attribution", "ingestion_run_id"]

KM_PER_DEGREE = 111.32  # length of one degree of latitude, roughly


def attribution(year):
    """The credit line Copernicus asks for."""
    return f"Contains modified Copernicus Sentinel data {year}"


def bbox_around(lat, lon, radius_km):
    """
    A box of about radius_km around a point, as (west, south, east, north).
    Degrees of longitude get shorter as you move away from the equator, so the
    box gets wider in degrees to stay the same size on the ground.
    """
    lat_step = radius_km / KM_PER_DEGREE
    lon_step = radius_km / (KM_PER_DEGREE * max(math.cos(math.radians(lat)), 0.01))
    west = max(lon - lon_step, -180.0)
    south = max(lat - lat_step, -90.0)
    east = min(lon + lon_step, 180.0)
    north = min(lat + lat_step, 90.0)
    return west, south, east, north


def read_band_links(item):
    """For each band we keep: where the file is and how to turn its numbers into reflectance."""
    bands = {}
    for name, asset in (item.get("assets") or {}).items():
        if name not in BANDS_TO_KEEP or not asset.get("href"):
            continue
        https_copy = (asset.get("alternate") or {}).get("https", {})
        bands[name] = {
            "href": asset["href"],               # usually an s3:// address
            "https": https_copy.get("href"),     # the same file over normal https
            "scale": asset.get("raster:scale"),  # reflectance = value * scale + offset
            "offset": asset.get("raster:offset"),
            "gsd_m": asset.get("gsd"),           # pixel size in metres
        }
    return bands


def to_float(value):
    """A number, or None when the catalogue left the field out."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_item(item):
    """Turn one search result into a row for satellite_scenes, or None if unusable."""
    props = item.get("properties", {})
    taken = props.get("datetime") or props.get("start_datetime")
    if not taken or not item.get("geometry"):
        return None

    acquired_at = datetime.fromisoformat(taken.replace("Z", "+00:00"))
    if acquired_at.tzinfo is None:
        acquired_at = acquired_at.replace(tzinfo=timezone.utc)

    footprint = shape(item["geometry"])
    if not footprint.is_valid:
        footprint = footprint.buffer(0)

    tile = props.get("grid:code", "").replace("MGRS-", "")
    cloud = props.get("eo:cloud_cover")

    return {
        "source": SOURCE,
        "source_id": item["id"],
        "platform": props.get("platform"),
        "acquired_at": acquired_at,
        "cloud_cover_pct": float(cloud) if cloud is not None else None,
        "tile_id": tile[:20] or None,
        "relative_orbit": props.get("sat:relative_orbit"),
        "sun_elevation_deg": to_float(props.get("view:sun_elevation")),
        "view_incidence_deg": to_float(props.get("view:incidence_angle")),
        "footprint": f"SRID=4326;{footprint.wkt}",
        "assets": read_band_links(item),
        "licence": LICENCE,
        "attribution": attribution(acquired_at.year),
    }


def search_scenes(http, bbox, start, end, max_cloud_pct=None):
    """
    Find images that touch bbox between start and end, one by one.
    Images cloudier than max_cloud_pct are skipped.
    """
    time_format = "%Y-%m-%dT%H:%M:%SZ"
    url = SEARCH_URL
    method = "POST"
    body = {
        "collections": [SOURCE],
        "bbox": list(bbox),
        "datetime": f"{start.strftime(time_format)}/{end.strftime(time_format)}",
        "limit": 100,
    }

    for _ in range(MAX_PAGES):
        if method == "POST":
            response = http.post(url, json=body, timeout=HTTP_TIMEOUT)
        else:
            response = http.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        page = response.json()

        for item in page.get("features", []):
            cloud = item.get("properties", {}).get("eo:cloud_cover")
            too_cloudy = max_cloud_pct is not None and cloud is not None and cloud > max_cloud_pct
            if not too_cloudy:
                yield item

        # The server tells us where the next page is in a "next" link.
        next_link = None
        for link in page.get("links", []):
            if link.get("rel") == "next":
                next_link = link
        if not next_link or not page.get("features"):
            return
        url = next_link["href"]
        method = (next_link.get("method") or "GET").upper()
        if method == "POST":
            body = next_link.get("body") or body

    log.warning("Stopped after %s pages for bbox %s", MAX_PAGES, bbox)


def ingest_for_facilities(session, start, end, radius_km=10.0, max_cloud_pct=30.0,
                          facility_ids=None, http=None):
    """
    Record the images that cover each facility. Returns (new, updated).
    Give facility_ids to only do some sites.
    """
    http = http or make_http_session()

    query = session.query(Facility.id, Facility.lat, Facility.lon)
    if facility_ids:
        query = query.filter(Facility.id.in_(facility_ids))
    sites = query.all()

    params = {"start": start.isoformat(), "end": end.isoformat(), "radius_km": radius_km,
              "max_cloud_pct": max_cloud_pct, "facilities": len(sites)}

    with ingestion_run(session, SOURCE, params) as run:
        # One image often covers several sites, so collect them by id first.
        scenes = {}
        for _site_id, lat, lon in sites:
            box = bbox_around(lat, lon, radius_km)
            for item in search_scenes(http, box, start, end, max_cloud_pct):
                run.n_fetched += 1
                row = parse_item(item)
                if row:
                    row["ingestion_run_id"] = run.id
                    scenes[row["source_id"]] = row

        new, updated = save_rows(session, SatelliteScene, scenes.values(),
                                 update_columns=SCENE_COLUMNS)
        run.n_inserted = new
        run.n_updated = updated
    return new, updated
