# fluxara/ingest/emit.py
"""
Methane plumes from NASA's EMIT instrument.

What EMIT is
    A spectrometer on the International Space Station. It sees methane plumes
    at 60 m resolution between about 52 N and 52 S. NASA checks every plume by
    hand before publishing it, so plumes appear about two weeks late.
    Product name: EMITL2BCH4PLM, version 002.

How we collect it, in two steps

    Step 1, catalogue (no login needed)
        Ask NASA's search service (CMR) for plumes. For each one we get the
        outline, the time, the plume id, cloud cover and links to its files.

    Step 2, enrich (needs a free Earthdata token)
        Download each plume's small metadata file. It has the exact peak
        location and, when NASA was able to measure it, the emission rate in
        kg/hr with its uncertainty. When NASA could not measure a plume it
        writes "NA", and we store an empty value (NULL), never a guess.

NASA's own formula for the rate: rate = wind speed x methane mass / plume length.
"""
import logging
import os
from datetime import datetime, timezone

from shapely.geometry import MultiPolygon, Point, Polygon
from sqlalchemy import func

from fluxara.database.models import PlumeDetection
from fluxara.ingest.common import (HTTP_TIMEOUT, ingestion_run, make_http_session,
                                   now_utc, save_rows)

log = logging.getLogger("fluxara.ingest.emit")

SOURCE = "nasa_emit"
PRODUCT = "EMITL2BCH4PLM"
VERSION = "002"
NASA_SEARCH_URL = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
PAGE_SIZE = 500

LICENCE = "NASA EOSDIS open data policy"
ATTRIBUTION = ("EMIT L2B Estimated Methane Plume Complexes 60 m V002, NASA LP DAAC, "
               "doi:10.5067/EMIT/EMITL2BCH4PLM.002")
COMMERCIAL_USE_ALLOWED = True

# Columns the catalogue step is allowed to change on a plume we already have.
# Everything else (emission rate, peak location...) belongs to the enrich step.
CATALOGUE_COLUMNS = [
    "instrument", "product", "product_version", "processing_version",
    "source_url", "source_revised_at", "ingestion_run_id", "raw_properties",
    "licence", "attribution", "commercial_use_allowed", "gas",
    "observed_at", "outline", "cloud_cover_pct",
]

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


# ── Small helpers ────────────────────────────────────────────────────────────

def to_number(value):
    """
    Turn a value from NASA into a float, or None when it is missing.
    NASA writes "NA" for missing numbers. We also reject text, NaN and True/False.
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # only NaN is not equal to itself
        return None
    return number


def to_utc_time(text):
    """'2025-09-22T20:49:33Z' -> a datetime in UTC."""
    moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def for_database(shape):
    """Shapes are stored as text like 'SRID=4326;POINT (lon lat)'. 4326 means plain lon/lat."""
    return f"SRID=4326;{shape.wkt}"


def read_outline(umm):
    """Build the plume outline polygon from NASA's list of corner points."""
    polygons_from_nasa = (umm.get("SpatialExtent", {})
                             .get("HorizontalSpatialDomain", {})
                             .get("Geometry", {})
                             .get("GPolygons", []))
    polygons = []
    for polygon in polygons_from_nasa:
        points = [(p["Longitude"], p["Latitude"]) for p in polygon["Boundary"]["Points"]]
        if len(points) < 4:
            continue
        shape = Polygon(points)
        if not shape.is_valid:
            shape = shape.buffer(0)  # standard trick to repair a self crossing outline
        if not shape.is_empty:
            polygons.append(shape)

    if not polygons:
        return None
    if len(polygons) == 1:
        return polygons[0]
    parts = []
    for shape in polygons:
        if isinstance(shape, MultiPolygon):
            parts.extend(shape.geoms)
        else:
            parts.append(shape)
    return MultiPolygon(parts)


def read_attributes(umm):
    """NASA's extra fields come as a list of {Name, Values}. Make it a simple dict."""
    attributes = {}
    for item in umm.get("AdditionalAttributes", []):
        values = item.get("Values") or [None]
        attributes[item["Name"]] = values[0]
    return attributes


def find_link(umm, ends_with, must_contain=""):
    """First https link whose address ends with `ends_with` (and contains `must_contain`)."""
    for link in umm.get("RelatedUrls", []):
        url = link.get("URL", "")
        if url.startswith("https://") and url.endswith(ends_with) and must_contain in url:
            return url
    return None


# ── Step 1: catalogue ────────────────────────────────────────────────────────

def parse_granule(item):
    """
    Turn one plume from NASA's search results into a row for plume_detections.
    Returns None if the plume has no outline or no time.
    """
    umm = item["umm"]
    meta = item.get("meta", {})

    outline = read_outline(umm)
    times = umm.get("TemporalExtent", {})
    observed = times.get("SingleDateTime") or times.get("RangeDateTime", {}).get("BeginningDateTime")
    if outline is None or not observed:
        log.warning("Skipping %s: no outline or time", umm.get("GranuleUR"))
        return None

    attributes = read_attributes(umm)
    revised = meta.get("revision-date")

    return {
        "source": SOURCE,
        "source_id": umm["GranuleUR"],
        "instrument": "EMIT",
        "product": PRODUCT,
        "product_version": VERSION,
        "processing_version": attributes.get("EMIT_GHG_SOFTWARE_BUILD_VERSION"),
        "source_url": find_link(umm, ".json", must_contain="PLMMETA"),
        "source_revised_at": to_utc_time(revised) if revised else None,
        "raw_properties": {
            "cmr_concept_id": meta.get("concept-id"),
            "cmr_revision_date": revised,
            "plume_id": attributes.get("PLUME_ID"),
            "orbit": attributes.get("ORBIT"),
            "source_scenes": attributes.get("SOURCE_SCENES"),
            "doi": attributes.get("Identifier_product_doi"),
            "geotiff_url": find_link(umm, ".tif"),
            "browse_url": find_link(umm, ".png"),
        },
        "licence": LICENCE,
        "attribution": ATTRIBUTION,
        "commercial_use_allowed": COMMERCIAL_USE_ALLOWED,
        "gas": "CH4",
        "observed_at": to_utc_time(observed),
        # We do not know the peak yet. Use a point that is surely inside the
        # outline. The enrich step replaces it with the real peak.
        "geom": for_database(outline.representative_point()),
        "geom_kind": "outline_centroid",
        "outline": for_database(outline),
        "cloud_cover_pct": to_number(umm.get("CloudCover")),
        # Unknown until the enrich step. Empty, never zero.
        "emission_rate_kg_hr": None,
        "emission_uncertainty_kg_hr": None,
        "max_enhancement_ppm_m": None,
        "wind_speed_ms": None,
        "wind_speed_std_ms": None,
        "wind_source": None,
        "fetch_length_m": None,
    }


def search_granules(http, since=None, until=None, bbox=None, updated_since=None):
    """
    Ask NASA for plumes, one page at a time, and hand them back one by one.

    since / until   only plumes observed in this time window
    bbox            (west, south, east, north) only plumes in this box
    updated_since   only plumes NASA published or changed after this moment.
                    Best for a daily job: it also catches reprocessed plumes.
    """
    params = {
        "short_name": PRODUCT,
        "version": VERSION,
        "page_size": PAGE_SIZE,
        "sort_key": "start_date",
    }
    if since or until:
        start = since.strftime(TIME_FORMAT) if since else ""
        end = until.strftime(TIME_FORMAT) if until else ""
        params["temporal"] = f"{start},{end}"
    if bbox:
        params["bounding_box"] = ",".join(str(x) for x in bbox)
    if updated_since:
        params["updated_since"] = updated_since.strftime(TIME_FORMAT)

    headers = {}
    while True:
        response = http.get(NASA_SEARCH_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        plumes = response.json().get("items", [])
        for plume in plumes:
            yield plume

        # NASA gives a bookmark for the next page in this header.
        next_page = response.headers.get("CMR-Search-After")
        if not plumes or not next_page:
            return
        headers = {"CMR-Search-After": next_page}


def ingest_catalogue(session, http=None, **search):
    """
    Step 1. Fetch plumes from NASA and save them.
    Accepts the same filters as search_granules. Returns (new, updated).
    """
    http = http or make_http_session()
    params = {"pass": "catalogue"}
    for name, value in search.items():
        if value:
            params[name] = value.isoformat() if isinstance(value, datetime) else value

    with ingestion_run(session, SOURCE, params) as run:
        rows = []
        for item in search_granules(http, **search):
            run.n_fetched += 1
            row = parse_granule(item)
            if row:
                row["ingestion_run_id"] = run.id
                rows.append(row)

        new, updated = save_rows(
            session, PlumeDetection, rows,
            update_columns=CATALOGUE_COLUMNS,
            merge_json_columns=["raw_properties"],  # keep what step 2 stored there
        )
        run.n_inserted = new
        run.n_updated = updated
    return new, updated


# ── Step 2: enrich ───────────────────────────────────────────────────────────

def parse_plume_metadata(geojson):
    """
    Read the numbers out of one plume's metadata file.
    Returns a dict of column -> value, or None if the file has no plume in it.
    The field names are the ones NASA's own code writes.
    """
    features = geojson.get("features") or []
    if not features:
        return None
    fields = features[0].get("properties", {})

    result = {
        "emission_rate_kg_hr": to_number(fields.get("Emissions Rate Estimate (kg/hr)")),
        "emission_uncertainty_kg_hr": to_number(fields.get("Emissions Rate Estimate Uncertainty (kg/hr)")),
        "max_enhancement_ppm_m": to_number(fields.get("Max Plume Concentration (ppm m)")),
        "wind_speed_ms": to_number(fields.get("Wind Speed (m/s)")),
        "wind_speed_std_ms": to_number(fields.get("Wind Speed Std (m/s)")),
        "fetch_length_m": to_number(fields.get("Fetch Length (m)")),
        "wind_source": None,
        "metadata_properties": fields,  # the whole original, kept for reference
    }

    wind_source = fields.get("Wind Speed Source")
    if isinstance(wind_source, str) and wind_source.strip().upper() != "NA":
        result["wind_source"] = wind_source.strip()[:50]

    # A negative emission rate is impossible, so treat it as "not measured".
    rate = result["emission_rate_kg_hr"]
    if rate is not None and rate < 0:
        result["emission_rate_kg_hr"] = None
        result["emission_uncertainty_kg_hr"] = None

    # Use the real peak location when NASA gives a sensible one.
    lat = to_number(fields.get("Latitude of max concentration"))
    lon = to_number(fields.get("Longitude of max concentration"))
    if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
        result["geom"] = for_database(Point(lon, lat))
        result["geom_kind"] = "max_enhancement"

    return result


def plumes_needing_enrichment(session, limit):
    """
    Plumes we have not enriched yet, or that NASA changed since we enriched them.
    We remember which NASA revision we enriched in raw_properties["enriched_revision"].
    """
    extra = PlumeDetection.raw_properties
    enriched_revision = extra["enriched_revision"].astext
    current_revision = func.coalesce(extra["cmr_revision_date"].astext, "")

    return (session.query(PlumeDetection)
            .filter(PlumeDetection.source == SOURCE)
            .filter(PlumeDetection.source_url.isnot(None))
            .filter(enriched_revision.is_distinct_from(current_revision))
            .order_by(PlumeDetection.observed_at.desc())
            .limit(limit)
            .all())


def enrich(session, http=None, token=None, limit=500):
    """
    Step 2. Download the metadata file for plumes that need it.
    Needs EARTHDATA_TOKEN (free: https://urs.earthdata.nasa.gov, then "Generate Token").
    Returns how many plumes were enriched.
    """
    token = token or os.getenv("EARTHDATA_TOKEN")
    if not token:
        raise RuntimeError("EARTHDATA_TOKEN is not set. Create a free Earthdata "
                           "Login account and generate a token.")
    http = http or make_http_session()
    login = {"Authorization": f"Bearer {token}"}

    plumes = plumes_needing_enrichment(session, limit)
    enriched = 0
    failed = 0

    with ingestion_run(session, SOURCE, {"pass": "enrich", "candidates": len(plumes)}) as run:
        for plume in plumes:
            run.n_fetched += 1
            if run.n_fetched % 25 == 0:
                log.info("Enriching plume %s of %s", run.n_fetched, len(plumes))

            response = http.get(plume.source_url, headers=login, timeout=HTTP_TIMEOUT)
            if response.status_code in (401, 403):
                # A bad token will fail for every plume, so stop now.
                raise PermissionError(
                    "Earthdata rejected the token. It may have expired, or the LP DAAC "
                    "application is not approved on your Earthdata profile.")
            try:
                response.raise_for_status()
                numbers = parse_plume_metadata(response.json())
            except Exception as error:
                # One broken file should not stop the others.
                failed += 1
                log.warning("Could not enrich %s: %s", plume.source_id, error)
                continue
            if not numbers:
                continue

            original_fields = numbers.pop("metadata_properties")
            for column, value in numbers.items():
                setattr(plume, column, value)
            plume.raw_properties = {
                **plume.raw_properties,
                "metadata_properties": original_fields,
                "enriched_revision": plume.raw_properties.get("cmr_revision_date") or "",
            }
            plume.ingestion_run_id = run.id
            plume.updated_at = now_utc()
            enriched += 1
            run.n_updated = enriched

        run.n_updated = enriched
        if plumes and failed == len(plumes):
            raise RuntimeError(f"All {failed} metadata downloads failed.")

    return enriched
