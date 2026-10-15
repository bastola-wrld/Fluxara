from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from conftest import FakeHTTP, FakeResponse, load_fixture
from fluxara.database.models import Facility, PlumeDetection
from fluxara.ingest import emit

KEY = {"X-API-Key": "test-dev-key"}


@pytest.fixture()
def client(db):
    # The async engine keeps connections bound to an event loop, so use a fresh
    # pool for each test client.
    from fluxara.database import connection
    from fluxara.api.main import app
    with TestClient(app) as c:
        yield c
    import asyncio
    asyncio.run(connection.engine.dispose())


@pytest.fixture()
def seeded(db):
    """One facility 300 m from the real EMIT plume, one far away, plume enriched."""
    db.add_all([Facility(name="Near", lat=32.2440, lon=-102.0489),
                Facility(name="Far", lat=40.0, lon=-80.0)])
    db.commit()
    page = load_fixture("emit_cmr_granules.json")
    emit.ingest_catalogue(db, http=FakeHTTP([FakeResponse(page), FakeResponse({"items": []})]))
    emit.enrich(db, http=FakeHTTP([FakeResponse(load_fixture("emit_plume_metadata_quantified.json"))]), token="t")
    db.commit()
    return {f.name: f.id for f in db.query(Facility)}


def test_app_imports_without_torch():
    import sys
    import fluxara.api.main  # noqa: F401
    assert "torch" not in sys.modules


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "healthy" and body["postgis"] is True
    assert body["plume_detections"] == 0 and body["legacy_inversion_enabled"] is False


def test_requests_without_credentials_are_rejected(client):
    assert client.get("/v1/plumes").status_code == 401
    assert client.get("/v1/timeseries").status_code == 401
    assert client.get("/v1/plumes", headers={"X-API-Key": "fluxara-dev-key-2024"}).status_code == 401


def test_legacy_invert_route_is_not_mounted(client):
    r = client.post("/v1/invert", headers=KEY,
                    json={"latitude": 31.85, "longitude": -102.1, "date": "2024-06-15"})
    assert r.status_code == 404
    assert "847.3" not in r.text


def test_timeseries_is_empty_when_there_is_no_data(client):
    body = client.get("/v1/timeseries", headers=KEY).json()
    assert body["dates"] == [] and body["fluxara"] == [] and body["epa"] == []
    assert body["has_data"] is False


def test_plumes_near_facility(client, seeded):
    body = client.get(f"/v1/plumes?facility_id={seeded['Near']}&radius_km=5", headers=KEY).json()
    assert body["total"] == 1
    p = body["items"][0]
    assert p["source"] == "nasa_emit" and p["instrument"] == "EMIT"
    assert p["emission_rate_kg_hr"] == 1000.0 and p["emission_uncertainty_kg_hr"] == 300.0
    assert (round(p["lat"], 4), round(p["lon"], 4)) == (32.2412, -102.0489)
    assert 0.25 < p["distance_km"] < 0.40          # 0.0028 deg of latitude is about 310 m
    assert p["commercial_use_allowed"] is True and p["attribution"] and p["licence"]

    assert client.get(f"/v1/plumes?facility_id={seeded['Far']}&radius_km=5", headers=KEY).json()["total"] == 0
    assert client.get(f"/v1/plumes?facility_id={seeded['Near']}&radius_km=0.1", headers=KEY).json()["total"] == 0


def test_plumes_filters(client, seeded):
    assert client.get("/v1/plumes", headers=KEY).json()["total"] == 1
    assert client.get("/v1/plumes?lat=32.2412&lon=-102.0489&radius_km=1", headers=KEY).json()["total"] == 1
    assert client.get("/v1/plumes?since=2026-01-01T00:00:00Z", headers=KEY).json()["total"] == 0
    assert client.get("/v1/plumes?until=2025-12-31T00:00:00Z&quantified_only=true&commercial_only=true",
                      headers=KEY).json()["total"] == 1
    assert client.get("/v1/plumes?lat=32.2", headers=KEY).status_code == 422
    assert client.get("/v1/plumes?facility_id=999999", headers=KEY).status_code == 404


def test_timeseries_reports_only_observed_months(client, seeded):
    body = client.get(f"/v1/timeseries?facility_id={seeded['Near']}", headers=KEY).json()
    assert body["dates"] == ["2025-09"]
    assert body["fluxara"] == [1000.0] and body["detections"] == [1] and body["quantified"] == [1]
    assert body["epa"] == [None]                     # nothing reported, so nothing shown
    far = client.get(f"/v1/timeseries?facility_id={seeded['Far']}", headers=KEY).json()
    assert far["dates"] == [] and far["has_data"] is False
    assert client.get("/v1/timeseries?facility_id=999999", headers=KEY).status_code == 404


def test_unquantified_plume_counts_as_detection_with_null_rate(client, db, seeded):
    p = db.query(PlumeDetection).one()
    p.emission_rate_kg_hr = p.emission_uncertainty_kg_hr = None
    db.commit()
    body = client.get(f"/v1/timeseries?facility_id={seeded['Near']}", headers=KEY).json()
    assert body["detections"] == [1] and body["quantified"] == [0] and body["fluxara"] == [None]
    assert client.get("/v1/plumes?quantified_only=true", headers=KEY).json()["total"] == 0


def test_pdf_generation_is_switched_off_until_rebuilt(client, seeded):
    r = client.get(f"/v1/reports/facility/{seeded['Near']}/pdf", headers=KEY)
    assert r.status_code == 503 and "switched off" in r.json()["detail"]
    assert client.post("/v1/reports/regenerate", headers=KEY).status_code == 503
    assert client.get("/v1/reports/library", headers=KEY).status_code == 200     # listing still works
