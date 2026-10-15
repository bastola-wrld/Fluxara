from datetime import datetime, timezone

from sqlalchemy import text

from conftest import FakeHTTP, FakeResponse, load_fixture
from fluxara.database.models import Facility, SatelliteScene
from fluxara.ingest import sentinel2

SCENE = "S2A_MSIL1C_20260909T101701_N0512_R065_T32SKA_20260909T171525"
START, END = datetime(2026, 9, 1, tzinfo=timezone.utc), datetime(2026, 9, 10, tzinfo=timezone.utc)


def pages():
    return [FakeResponse(load_fixture("sentinel2_stac_search.json")),
            FakeResponse({"type": "FeatureCollection", "features": [], "links": []})]


def test_parse_real_stac_item():
    row = sentinel2.parse_item(load_fixture("sentinel2_stac_search.json")["features"][0])
    assert row["source_id"] == SCENE and row["source"] == "sentinel-2-l1c"
    assert row["platform"] == "sentinel-2a" and row["tile_id"] == "32SKA"
    assert row["cloud_cover_pct"] == 0.0            # zero is a real value, not missing
    assert row["acquired_at"].year == 2026 and row["acquired_at"].tzinfo is not None
    assert set(row["assets"]) == {"B11", "B12", "TCI"}          # thumbnail dropped
    b12 = row["assets"]["B12"]
    assert b12["href"].startswith("s3://eodata/") and b12["https"].startswith("https://download.dataspace")
    assert (b12["scale"], b12["offset"], b12["gsd_m"]) == (0.0001, -0.1, 20)
    assert row["attribution"] == "Contains modified Copernicus Sentinel data 2026"


def test_bbox_around_is_wider_in_longitude_away_from_equator():
    w, s, e, n = sentinel2.bbox_around(60.0, 10.0, 10.0)
    assert round(n - s, 3) == round(2 * 10 / 111.32, 3)
    assert (e - w) > 1.9 * (n - s)
    assert sentinel2.bbox_around(89.99, 179.9, 50)[2] <= 180


def test_ingest_scenes_over_facility_and_follow_paging(db):
    db.add(Facility(name="Hassi Messaoud", lat=31.67, lon=6.07))
    db.commit()
    http = FakeHTTP(pages())
    assert sentinel2.ingest_for_facilities(db, START, END, http=http) == (1, 0)

    s = db.query(SatelliteScene).one()
    assert s.source_id == SCENE and s.assets["B11"]["href"].endswith("_B11.jp2")
    # The scene footprint really covers the facility.
    assert db.execute(text("""SELECT ST_Contains(s.footprint, f.geom)
                              FROM satellite_scenes s, facilities f""")).scalar() is True
    # First call is a POST search with our bbox, second follows the GET "next" link.
    assert http.calls[0][0] == "POST" and http.calls[0][2]["json"]["collections"] == ["sentinel-2-l1c"]
    assert http.calls[1][0] == "GET" and "token=next" in http.calls[1][1]

    assert sentinel2.ingest_for_facilities(db, START, END, http=FakeHTTP(pages())) == (0, 1)
    assert db.query(SatelliteScene).count() == 1


def test_cloudy_scenes_are_filtered(db):
    db.add(Facility(name="X", lat=31.67, lon=6.07))
    db.commit()
    p = pages()
    p[0]._payload["features"][0]["properties"]["eo:cloud_cover"] = 80.0
    assert sentinel2.ingest_for_facilities(db, START, END, max_cloud_pct=30, http=FakeHTTP(p)) == (0, 0)
