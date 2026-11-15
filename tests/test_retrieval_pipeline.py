"""The whole chain on made up images: database in, database out, and the API."""
from datetime import datetime, timedelta, timezone

import pytest
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin
from rasterio.warp import transform
from sqlalchemy import text

import synthetic
from fluxara.database.models import Facility, PlumeDetection, SatelliteScene, SiteObservation
from fluxara.retrieval import pipeline
from fluxara.retrieval.wind import FixedWind

KEY = {"X-API-Key": "test-dev-key"}
WHEN = datetime(2026, 9, 9, 10, 17, tzinfo=timezone.utc)
START, END = WHEN - timedelta(days=1), WHEN + timedelta(days=1)
WIND = FixedWind(3.0, 270.0)
SCALE, OFFSET = 0.0001, -0.1
SIZE = 600                                   # the file is a bit bigger than the 500 pixel crop
WEST, NORTH = 300000, 3600000                # UTM zone 32N


def site_lonlat():
    """The middle of the made up image, as longitude and latitude."""
    x, y = WEST + SIZE / 2 * 20, NORTH - SIZE / 2 * 20
    lons, lats = transform("EPSG:32632", "EPSG:4326", [x], [y])
    return lons[0], lats[0]


class FilesOnDisk:
    """Stands in for BandFetcher: writes made up band files instead of downloading."""
    def __init__(self, folder, images):
        self.folder, self.images = folder, images      # images: scene id -> (b11, b12)

    def path(self, scene, band):
        path = self.folder / f"{scene.source_id}_{band}.tif"
        if not path.exists():
            b11, b12 = self.images[scene.source_id]
            reflectance = b11 if band == "B11" else b12
            stored = ((reflectance - OFFSET) / SCALE).round().astype("uint16")
            with rasterio.open(path, "w", driver="GTiff", height=SIZE, width=SIZE, count=1,
                               dtype="uint16", crs="EPSG:32632",
                               transform=from_origin(WEST, NORTH, 20, 20)) as file:
                file.write(stored, 1)
        return path


def add_scene(db, source_id, when, platform="sentinel-2a", cloud=0.0):
    lon, lat = site_lonlat()
    band = {"https": "https://example/band", "scale": SCALE, "offset": OFFSET}
    scene = SatelliteScene(
        source="sentinel-2-l1c", source_id=source_id, platform=platform, acquired_at=when,
        cloud_cover_pct=cloud, tile_id="32SKA", relative_orbit=65,
        sun_elevation_deg=90 - synthetic.SUN_ZENITH, view_incidence_deg=synthetic.VIEW_ZENITH,
        footprint=f"SRID=4326;POLYGON(({lon-1} {lat-1},{lon+1} {lat-1},{lon+1} {lat+1},"
                  f"{lon-1} {lat+1},{lon-1} {lat-1}))",
        assets={"B11": band, "B12": band}, licence="test",
        attribution="Contains modified Copernicus Sentinel data 2026")
    db.add(scene)
    return scene


@pytest.fixture()
def world(db, tmp_path):
    """A facility, a clear reference image ten days earlier, and a target image."""
    lon, lat = site_lonlat()
    facility = Facility(name="Test site", lat=lat, lon=lon)
    db.add(facility)
    add_scene(db, "REFERENCE", WHEN - timedelta(days=10))
    add_scene(db, "TARGET", WHEN)
    db.commit()

    reference = synthetic.with_noise(*synthetic.ground(0, size=SIZE), 1)
    target = synthetic.with_noise(*synthetic.ground(0, size=SIZE), 2)
    images = {"REFERENCE": reference, "TARGET": target}
    return facility, images, FilesOnDisk(tmp_path, images)


def put_plume_in_target(images, peak=1.0):
    truth = synthetic.plume_column(peak, 270.0, size=SIZE)
    b11, b12 = images["TARGET"]
    images["TARGET"] = (b11, synthetic.add_plume(b12, truth))
    return synthetic.true_rate_kg_hr(truth, 3.0)


def run(db, facility, fetcher):
    return pipeline.run_for_facility(db, facility.id, START, END, fetcher, WIND)


def test_plume_is_saved_with_its_source_and_numbers(db, world):
    facility, images, fetcher = world
    expected = put_plume_in_target(images)

    assert run(db, facility, fetcher) == {"plume_detected": 1, "no_plume": 0,
                                          "unusable": 0, "failed": 0}
    check = db.query(SiteObservation).one()
    assert check.status == "plume_detected" and check.wind_agreement == "consistent"
    assert check.wind_source == "fixed" and check.wind_speed_10m_ms == 3.0
    assert check.detection_limit_kg_hr > 0 and check.distance_to_plume_m < 100

    plume = db.query(PlumeDetection).one()
    assert plume.id == check.plume_detection_id and plume.source == "fluxara_s2"
    assert plume.emission_rate_kg_hr == pytest.approx(expected, rel=0.25)
    assert plume.emission_uncertainty_kg_hr > 0 and plume.commercial_use_allowed is True
    assert "Copernicus Sentinel data 2026" in plume.attribution and "Varon" in plume.attribution
    assert plume.raw_properties["reference_scene"] == "REFERENCE"
    # The plume is drawn on the map right at the facility.
    metres = db.execute(text("""SELECT ST_Distance(p.geom::geography, f.geom::geography)
                                FROM plume_detections p, facilities f""")).scalar()
    assert metres < 100
    assert db.execute(text("SELECT ST_Area(outline::geography) FROM plume_detections")).scalar() > 10000


def test_clean_image_is_saved_as_no_plume_with_a_limit(db, world):
    facility, _images, fetcher = world
    assert run(db, facility, fetcher)["no_plume"] == 1
    check = db.query(SiteObservation).one()
    assert check.status == "no_plume" and check.plume_detection_id is None
    assert 1000 < check.detection_limit_kg_hr < 3000
    assert db.query(PlumeDetection).count() == 0


def test_running_again_replaces_the_result_and_removes_a_stale_plume(db, world):
    facility, images, fetcher = world
    put_plume_in_target(images)
    run(db, facility, fetcher)
    assert db.query(PlumeDetection).count() == 1

    # Check the same image again, this time it shows no plume.
    clean = FilesOnDisk(fetcher.folder / "again", {
        "REFERENCE": images["REFERENCE"],
        "TARGET": synthetic.with_noise(*synthetic.ground(0, size=SIZE), 2)})
    clean.folder.mkdir()
    assert run(db, facility, clean)["no_plume"] == 1
    assert db.query(SiteObservation).count() == 1
    assert db.query(PlumeDetection).count() == 0


def test_images_that_cannot_be_used_say_why(db, world):
    facility, _images, fetcher = world
    add_scene(db, "FROM_2C", WHEN + timedelta(hours=1), platform="sentinel-2c")
    db.commit()
    counts = pipeline.run_for_facility(db, facility.id, START, END + timedelta(days=1),
                                       fetcher, WIND)
    assert counts["unusable"] == 1 and counts["no_plume"] == 1
    reasons = {c.status: c.reason for c in db.query(SiteObservation)}
    assert "sentinel-2c" in reasons["unusable"]


def test_no_reference_image_is_unusable(db, world):
    facility, _images, fetcher = world
    db.query(SatelliteScene).filter_by(source_id="REFERENCE").delete()
    db.commit()
    assert run(db, facility, fetcher)["unusable"] == 1
    assert "no clear earlier image" in db.query(SiteObservation).one().reason


def test_one_broken_image_does_not_stop_the_rest(db, world):
    facility, images, fetcher = world
    add_scene(db, "BROKEN", WHEN + timedelta(days=2))      # no pixels for this one
    db.commit()
    counts = pipeline.run_for_facility(db, facility.id, START, END + timedelta(days=3),
                                       fetcher, WIND)
    assert counts["failed"] == 1 and counts["no_plume"] == 1
    assert db.query(SiteObservation).count() == 1


def test_two_tiles_of_the_same_pass_count_once(db, world):
    facility, _images, _fetcher = world
    add_scene(db, "TARGET_OTHER_TILE", WHEN + timedelta(seconds=8), cloud=12.0)
    db.commit()
    scenes = pipeline.scenes_over(db, facility, START, END)
    assert [s.source_id for s in pipeline.one_image_per_pass(scenes)] == ["TARGET"]


def test_observations_api(db, world):
    facility, images, fetcher = world
    put_plume_in_target(images)
    run(db, facility, fetcher)

    from fluxara.database import connection
    from fluxara.api.main import app
    with TestClient(app) as client:
        assert client.get(f"/v1/observations?facility_id={facility.id}").status_code == 401
        body = client.get(f"/v1/observations?facility_id={facility.id}", headers=KEY).json()
        assert body["total"] == 1
        assert body["counts"] == {"plume_detected": 1, "no_plume": 0, "unusable": 0}
        item = body["items"][0]
        assert item["status"] == "plume_detected" and item["emission_rate_kg_hr"] > 0
        assert item["wind_agreement"] == "consistent"

        none = client.get(f"/v1/observations?facility_id={facility.id}&status=no_plume",
                          headers=KEY).json()
        assert none["total"] == 0 and none["counts"]["plume_detected"] == 1
        assert client.get("/v1/observations?facility_id=999", headers=KEY).status_code == 404
        assert client.get(f"/v1/observations?facility_id={facility.id}&status=maybe",
                          headers=KEY).status_code == 422
    import asyncio
    asyncio.run(connection.engine.dispose())
