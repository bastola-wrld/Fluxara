# fluxara/retrieval/bands.py
"""
Get the pixels: download band 11 and band 12 of a Sentinel 2 image and cut
out the small square around a site.

Downloading needs a free Copernicus Data Space account. Put the login in .env:

    CDSE_USERNAME=your email
    CDSE_PASSWORD=your password

Each band file is about 30 to 60 MB. Files are kept in a cache folder, so an
image is only ever downloaded once.
"""
import logging
import os
import pathlib

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform, transform_geom
from rasterio.windows import Window
from shapely.geometry import shape
from shapely.ops import unary_union

from fluxara.ingest.common import make_http_session

log = logging.getLogger("fluxara.retrieval.bands")

TOKEN_URL = ("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
             "protocol/openid-connect/token")
DOWNLOAD_TIMEOUT = 300
DEFAULT_CACHE = "satellite_data/cache"
LONLAT = "EPSG:4326"


class LoginFailed(Exception):
    """Copernicus did not accept the username and password."""


def get_token(http, username, password):
    """Swap the username and password for a short lived access token."""
    response = http.post(TOKEN_URL, timeout=60, data={
        "grant_type": "password", "client_id": "cdse-public",
        "username": username, "password": password,
    })
    if response.status_code != 200:
        raise LoginFailed(f"Copernicus login failed ({response.status_code}). "
                          "Check CDSE_USERNAME and CDSE_PASSWORD in .env.")
    return response.json()["access_token"]


def download_file(http, url, token, destination):
    """
    Download url to destination. The Copernicus server answers with redirects,
    and the normal redirect handling drops the login on the way, so we follow
    them by hand. The file is written as ".part" first and renamed at the end,
    so a download that was cut off never looks like a finished file.
    """
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(5):
        response = http.get(url, headers=headers, stream=True,
                            allow_redirects=False, timeout=DOWNLOAD_TIMEOUT)
        if response.status_code in (301, 302, 303, 307, 308):
            url = response.headers["Location"]
            continue
        break
    response.raise_for_status()

    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name(destination.name + ".part")
    with open(part, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            file.write(chunk)
    part.rename(destination)


class BandFetcher:
    """
    Hands out the local path of a band file, downloading it the first time.

        fetcher = BandFetcher()
        path = fetcher.path(scene, "B12")
    """
    def __init__(self, cache_dir=None, http=None, username=None, password=None):
        root = cache_dir or os.getenv("FLUXARA_CACHE_DIR") or DEFAULT_CACHE
        self.folder = pathlib.Path(root) / "sentinel2"
        self.http = http or make_http_session()
        self.username = username or os.getenv("CDSE_USERNAME")
        self.password = password or os.getenv("CDSE_PASSWORD")
        self.token = None

    def path(self, scene, band):
        destination = self.folder / scene.source_id / f"{band}.jp2"
        if destination.exists():
            return destination

        url = (scene.assets.get(band) or {}).get("https")
        if not url:
            raise FileNotFoundError(f"{scene.source_id} has no download link for {band}")
        if not self.username or not self.password:
            raise LoginFailed("CDSE_USERNAME and CDSE_PASSWORD are not set in .env.")
        if self.token is None:
            self.token = get_token(self.http, self.username, self.password)

        log.info("Downloading %s %s", scene.source_id, band)
        try:
            download_file(self.http, url, self.token, destination)
        except Exception as error:
            # Tokens last ten minutes. Get a new one and try once more.
            if getattr(getattr(error, "response", None), "status_code", None) != 401:
                raise
            self.token = get_token(self.http, self.username, self.password)
            download_file(self.http, url, self.token, destination)
        return destination


class Crop:
    """A square cut out of a band file, plus what is needed to place it on a map."""
    def __init__(self, data, transform_, crs, site_row, site_col):
        self.data = data              # reflectance, NaN where there is no data
        self.transform = transform_   # pixel (col, row) -> map coordinates
        self.crs = crs
        self.site_row = site_row      # where the site is inside the crop
        self.site_col = site_col


def read_crop(path, lat, lon, half_size_m, scale=0.0001, offset=0.0):
    """
    Cut the square of 2 x half_size_m around (lat, lon) out of a band file.
    Stored numbers are turned into reflectance: value x scale + offset.
    A stored 0 means "no data" and becomes NaN.
    Returns None when the site is too close to the edge of the image.
    """
    with rasterio.open(path) as band:
        xs, ys = transform(LONLAT, band.crs, [lon], [lat])
        site_row, site_col = band.index(xs[0], ys[0])
        half = int(round(half_size_m / abs(band.transform.a)))

        top, left = site_row - half, site_col - half
        size = 2 * half
        if top < 0 or left < 0 or top + size > band.height or left + size > band.width:
            return None

        window = Window(left, top, size, size)
        raw = band.read(1, window=window).astype("float64")
        data = raw * scale + offset
        data[raw == 0] = np.nan
        return Crop(data, band.window_transform(window), band.crs, half, half)


def scene_crop(fetcher, scene, band, lat, lon, half_size_m):
    """Download (if needed) and crop one band of one image."""
    details = scene.assets.get(band) or {}
    scale = details.get("scale") if details.get("scale") is not None else 0.0001
    offset = details.get("offset") if details.get("offset") is not None else 0.0
    return read_crop(fetcher.path(scene, band), lat, lon, half_size_m, scale, offset)


def pixel_lonlat(crop, row, col):
    """Longitude and latitude of the centre of a pixel in the crop."""
    x, y = rasterio.transform.xy(crop.transform, row, col)   # centre of the pixel
    lons, lats = transform(crop.crs, LONLAT, [x], [y])
    return lons[0], lats[0]


def mask_outline_lonlat(crop, mask):
    """The outline of a plume mask as a shape in longitude and latitude."""
    pieces = [shape(transform_geom(crop.crs, LONLAT, geometry))
              for geometry, value in shapes(mask.astype("uint8"), mask=mask,
                                            transform=crop.transform)
              if value == 1]
    return unary_union(pieces) if pieces else None
