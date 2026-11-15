"""Reading band files, the wind, and choosing the reference image."""
import math
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from fluxara.retrieval import bands, pipeline
from fluxara.retrieval.wind import FixedWind, read_wind_file, speed_and_direction

WHEN = datetime(2026, 9, 9, 10, 17, tzinfo=timezone.utc)


def write_band(path, values, west=300000, north=3600000):
    """A small band file in UTM zone 32N with 20 m pixels, like a real one."""
    with rasterio.open(path, "w", driver="GTiff", height=values.shape[0], width=values.shape[1],
                       count=1, dtype="uint16", crs="EPSG:32632",
                       transform=from_origin(west, north, 20, 20)) as file:
        file.write(values.astype("uint16"), 1)


def lonlat_of_pixel(path, row, col):
    from rasterio.warp import transform
    with rasterio.open(path) as band:
        x, y = band.xy(row, col)
        lons, lats = transform(band.crs, "EPSG:4326", [x], [y])
    return lons[0], lats[0]


def test_read_crop_cuts_the_right_square_and_scales(tmp_path):
    values = np.arange(200 * 200).reshape(200, 200) % 5000 + 1000
    values[100, 100] = 0                                    # a gap in the data
    path = tmp_path / "B12.tif"
    write_band(path, values)
    lon, lat = lonlat_of_pixel(path, 100, 100)

    crop = bands.read_crop(path, lat, lon, half_size_m=400, scale=0.0001, offset=-0.1)
    assert crop.data.shape == (40, 40) and (crop.site_row, crop.site_col) == (20, 20)
    assert math.isnan(crop.data[20, 20])                    # stored 0 means no data
    assert crop.data[0, 0] == pytest.approx(values[80, 80] * 0.0001 - 0.1)
    # A pixel of the crop maps back to the right place on Earth.
    back_lon, back_lat = bands.pixel_lonlat(crop, 20, 20)
    assert back_lon == pytest.approx(lon, abs=1e-4) and back_lat == pytest.approx(lat, abs=1e-4)


def test_read_crop_refuses_a_site_at_the_edge(tmp_path):
    path = tmp_path / "B12.tif"
    write_band(path, np.full((200, 200), 3000))
    lon, lat = lonlat_of_pixel(path, 5, 5)
    assert bands.read_crop(path, lat, lon, half_size_m=400) is None


def test_mask_outline_is_a_shape_on_the_map(tmp_path):
    path = tmp_path / "B12.tif"
    write_band(path, np.full((200, 200), 3000))
    lon, lat = lonlat_of_pixel(path, 100, 100)
    crop = bands.read_crop(path, lat, lon, half_size_m=400)
    mask = np.zeros((40, 40), dtype=bool)
    mask[18:22, 18:26] = True
    outline = bands.mask_outline_lonlat(crop, mask)
    assert outline.area > 0
    assert abs(outline.centroid.x - lon) < 0.01 and abs(outline.centroid.y - lat) < 0.01


def test_band_fetcher_uses_the_cache_and_needs_a_login(tmp_path):
    scene = SimpleNamespace(source_id="S2A_TEST", assets={"B12": {"https": "https://example/B12"}})
    fetcher = bands.BandFetcher(cache_dir=tmp_path, username="", password="")
    with pytest.raises(bands.LoginFailed):
        fetcher.path(scene, "B12")

    cached = tmp_path / "sentinel2" / "S2A_TEST" / "B12.jp2"
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"already here")
    assert fetcher.path(scene, "B12") == cached            # no download, no login needed


def test_wind_direction_is_where_it_comes_from():
    assert speed_and_direction(3.0, 0.0) == pytest.approx((3.0, 270.0))    # blowing east
    assert speed_and_direction(0.0, -4.0) == pytest.approx((4.0, 0.0))     # blowing south
    assert FixedWind(2.5, 90).at(0, 0, WHEN) == (2.5, 90)


def test_era5_file_is_blended_between_the_hours(tmp_path):
    import xarray as xr
    hours = np.array(["2026-09-09T10:00", "2026-09-09T11:00"], dtype="datetime64[ns]")
    data = xr.Dataset(
        {"u10": (("valid_time", "latitude", "longitude"), np.array([[[2.0]], [[4.0]]])),
         "v10": (("valid_time", "latitude", "longitude"), np.array([[[0.0]], [[0.0]]]))},
        coords={"valid_time": hours, "latitude": [31.75], "longitude": [6.0]})
    path = tmp_path / "wind.nc"
    data.to_netcdf(path)

    speed, comes_from = read_wind_file(path, 31.67, 6.07, WHEN.replace(minute=30))
    assert speed == pytest.approx(3.0) and comes_from == pytest.approx(270.0)
    # Outside the hours in the file, the closest hour is used.
    late, _ = read_wind_file(path, 31.67, 6.07, WHEN.replace(hour=11, minute=40))
    assert late == pytest.approx(4.0)


def scene(days_before, cloud=0.0, platform="sentinel-2a", tile="32SKA", orbit=65):
    return SimpleNamespace(platform=platform, tile_id=tile, relative_orbit=orbit,
                           cloud_cover_pct=cloud, acquired_at=WHEN - timedelta(days=days_before))


def test_choose_reference_rules():
    target = scene(0)
    same_orbit, other_orbit = scene(10), scene(5, orbit=22)
    assert pipeline.choose_reference(target, [other_orbit, same_orbit]) is same_orbit
    clearer = scene(20, cloud=0.0)
    assert pipeline.choose_reference(target, [scene(10, cloud=8.0), clearer]) is clearer

    not_allowed = [scene(-1),                          # later than the target
                   scene(60),                          # too old
                   scene(5, cloud=40.0),               # cloudy
                   scene(5, tile="32SKB"),             # pixels would not line up
                   scene(5, platform="sentinel-2c")]   # no calibration
    assert pipeline.choose_reference(target, not_allowed) is None


def test_sun_elevation_from_time_is_about_right():
    # Solar noon at the equator on the March equinox: the sun is overhead.
    noon = datetime(2026, 3, 20, 12, 7, tzinfo=timezone.utc)
    assert pipeline.sun_elevation_from_time(noon, 0.0, 0.0) > 88
    # The catalogue value wins when there is one.
    with_angle = SimpleNamespace(sun_elevation_deg=55.0, acquired_at=noon)
    assert pipeline.sun_zenith_deg(with_angle, 0, 0) == 35.0
    without = SimpleNamespace(sun_elevation_deg=None, acquired_at=noon)
    assert pipeline.sun_zenith_deg(without, 0, 0) < 2
