# fluxara/retrieval/wind.py
"""
The wind at a site at the moment the satellite passed.

The leak rate is  wind x mass / length,  so a wrong wind gives a wrong rate.
We use ERA5, the weather record from the Copernicus Climate Change Service:
the wind 10 m above the ground, every hour, on a grid of about 30 km.

ERA5 needs a free Climate Data Store account. Put the key in .env:

    CDSAPI_URL=https://cds.climate.copernicus.eu/api
    CDSAPI_KEY=your key

ERA5 is published about five days late, so very recent images have to wait.
"""
import logging
import math
import os
import pathlib
from datetime import timezone

log = logging.getLogger("fluxara.retrieval.wind")

DATASET = "reanalysis-era5-single-levels"
ATTRIBUTION = ("Wind: ERA5 hourly data on single levels, Copernicus Climate "
               "Change Service, doi:10.24381/cds.adbb2d47")
DEFAULT_CACHE = "satellite_data/cache"


def speed_and_direction(u, v):
    """
    u is the wind blowing towards the east, v towards the north, in m/s.
    Returns (speed, direction the wind comes FROM in degrees, 0 = north,
    90 = east), which is how weather reports say it.
    """
    speed = math.hypot(u, v)
    comes_from = math.degrees(math.atan2(-u, -v)) % 360
    return speed, comes_from


class FixedWind:
    """A wind you choose yourself. For tests and for trying things out."""
    source = "fixed"

    def __init__(self, speed_ms, from_deg):
        self.speed_ms = speed_ms
        self.from_deg = from_deg

    def at(self, lat, lon, when):
        return self.speed_ms, self.from_deg


class Era5Wind:
    """
    ERA5 wind, one small file per site and day, kept in a cache folder.

        speed, comes_from = Era5Wind().at(31.67, 6.07, when)
    """
    source = "era5"

    def __init__(self, cache_dir=None):
        root = cache_dir or os.getenv("FLUXARA_CACHE_DIR") or DEFAULT_CACHE
        self.folder = pathlib.Path(root) / "era5"

    def at(self, lat, lon, when):
        when = when.astimezone(timezone.utc)
        return read_wind_file(self.file_for(lat, lon, when), lat, lon, when)

    def file_for(self, lat, lon, when):
        """The cached file for this site and day, downloaded if we do not have it."""
        name = f"{when:%Y%m%d}_{lat:+.2f}_{lon:+.2f}.nc"
        path = self.folder / name
        if path.exists():
            return path

        import cdsapi   # imported here so the rest works without the package
        self.folder.mkdir(parents=True, exist_ok=True)
        part = path.with_name(name + ".part")
        log.info("Downloading ERA5 wind for %s at %.2f, %.2f", when.date(), lat, lon)
        cdsapi.Client(quiet=True).retrieve(DATASET, {
            "product_type": ["reanalysis"],
            "variable": ["10m_u_component_of_wind", "10m_v_component_of_wind"],
            "year": [f"{when:%Y}"], "month": [f"{when:%m}"], "day": [f"{when:%d}"],
            "time": [f"{hour:02d}:00" for hour in range(24)],
            "area": [lat + 0.5, lon - 0.5, lat - 0.5, lon + 0.5],   # north, west, south, east
            "data_format": "netcdf",
            "download_format": "unarchived",
        }, str(part))
        part.rename(path)
        return path


def read_wind_file(path, lat, lon, when):
    """
    Read the wind at (lat, lon) and time `when` from an ERA5 file.
    Takes the nearest grid point and blends the hour before and the hour
    after, because the satellite rarely passes exactly on the hour.
    """
    import numpy as np
    import xarray as xr

    with xr.open_dataset(path) as data:
        time_name = "valid_time" if "valid_time" in data.coords else "time"
        point = data.sel(latitude=lat, longitude=lon, method="nearest")
        moment = np.datetime64(when.replace(tzinfo=None))
        times = point[time_name].values
        if moment < times.min() or moment > times.max():
            # e.g. 23:30, after the last hour in the file. Use the closest hour.
            point = point.sel({time_name: moment}, method="nearest")
        else:
            point = point.interp({time_name: moment})
        u, v = float(point["u10"]), float(point["v10"])

    if math.isnan(u) or math.isnan(v):
        raise ValueError(f"ERA5 has no wind for {when} at {lat}, {lon}")
    return speed_and_direction(u, v)
