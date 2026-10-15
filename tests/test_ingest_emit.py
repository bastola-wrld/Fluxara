from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from conftest import FakeHTTP, FakeResponse, load_fixture
from fluxara.database.models import IngestionRun, PlumeDetection
from fluxara.ingest import emit

GRANULE = "EMIT_L2B_CH4PLM_002_20250922T204933_003374"


def cmr_pages():
    """Two pages: the real granule, then an empty page that ends paging."""
    page = load_fixture("emit_cmr_granules.json")
    return [FakeResponse(page, headers={"CMR-Search-After": '["abc"]'}),
            FakeResponse({"hits": 1686, "items": []})]


# ── parsing ──────────────────────────────────────────────────────────────────

def test_parse_real_cmr_granule():
    row = emit.parse_granule(load_fixture("emit_cmr_granules.json")["items"][0])
    assert row["source"] == "nasa_emit" and row["source_id"] == GRANULE
    assert row["observed_at"] == datetime(2025, 9, 22, 20, 49, 33, tzinfo=timezone.utc)
    assert row["cloud_cover_pct"] == 9
    assert row["processing_version"] == "v0.1.2"
    assert row["source_url"].endswith("EMIT_L2B_CH4PLMMETA_002_20250922T204933_003374.json")
    assert row["source_url"].startswith("https://")
    assert row["raw_properties"]["plume_id"] == "3374"
    assert row["raw_properties"]["doi"] == "10.5067/EMIT/EMITL2BCH4PLM.002"
    assert row["outline"].startswith("SRID=4326;POLYGON")
    assert row["geom_kind"] == "outline_centroid"
    # The catalogue has no rate. It must be NULL, never a guess.
    assert row["emission_rate_kg_hr"] is None
    assert row["commercial_use_allowed"] is True and "10.5067/EMIT" in row["attribution"]


def test_parse_granule_without_outline_is_skipped():
    item = load_fixture("emit_cmr_granules.json")["items"][0]
    item["umm"]["SpatialExtent"] = {}
    assert emit.parse_granule(item) is None


def test_parse_quantified_metadata():
    out = emit.parse_plume_metadata(load_fixture("emit_plume_metadata_quantified.json"))
    assert out["emission_rate_kg_hr"] == 1000.0
    assert out["emission_uncertainty_kg_hr"] == 300.0
    assert out["wind_speed_ms"] == 4.2 and out["wind_source"] == "hrrr"
    assert out["geom"] == "SRID=4326;POINT (-102.0489 32.2412)"
    assert out["geom_kind"] == "max_enhancement"


def test_parse_unquantified_metadata_gives_null_not_zero():
    out = emit.parse_plume_metadata(load_fixture("emit_plume_metadata_not_quantified.json"))
    assert out["emission_rate_kg_hr"] is None
    assert out["emission_uncertainty_kg_hr"] is None
    assert out["wind_speed_ms"] is None and out["wind_source"] is None
    assert out["max_enhancement_ppm_m"] == 800.0


@pytest.mark.parametrize("value", ["NA", "", None, "nan", True])
def test_to_number_treats_junk_as_missing(value):
    assert emit.to_number(value) is None


# ── database ─────────────────────────────────────────────────────────────────

def test_catalogue_ingest_stores_plume_with_provenance(db):
    http = FakeHTTP(cmr_pages())
    assert emit.ingest_catalogue(db, http=http, updated_since=datetime(2026, 1, 1, tzinfo=timezone.utc)) == (1, 0)

    p = db.query(PlumeDetection).one()
    assert p.source_id == GRANULE and p.instrument == "EMIT"
    lon, lat, inside = db.execute(text(
        "SELECT ST_X(geom), ST_Y(geom), ST_Contains(outline, geom) FROM plume_detections")).one()
    assert -102.06 < lon < -102.04 and 32.23 < lat < 32.25 and inside

    run = db.query(IngestionRun).one()
    assert run.status == "success" and (run.n_fetched, run.n_inserted, run.n_updated) == (1, 1, 0)
    assert p.ingestion_run_id == run.id and run.code_version

    # Request shape: right product, incremental filter, and the paging header on page two.
    assert http.calls[0][2]["params"]["short_name"] == "EMITL2BCH4PLM"
    assert http.calls[0][2]["params"]["updated_since"] == "2026-01-01T00:00:00Z"
    assert http.calls[1][2]["headers"] == {"CMR-Search-After": '["abc"]'}


def test_rerunning_is_idempotent(db):
    emit.ingest_catalogue(db, http=FakeHTTP(cmr_pages()))
    first_seen = db.query(PlumeDetection).one().first_seen_at
    assert emit.ingest_catalogue(db, http=FakeHTTP(cmr_pages())) == (0, 1)
    db.expire_all()
    assert db.query(PlumeDetection).count() == 1
    assert db.query(PlumeDetection).one().first_seen_at == first_seen


def test_enrich_then_recatalogue_keeps_emission_rate(db):
    emit.ingest_catalogue(db, http=FakeHTTP(cmr_pages()))
    meta = FakeHTTP([FakeResponse(load_fixture("emit_plume_metadata_quantified.json"))])
    assert emit.enrich(db, http=meta, token="tok") == 1
    assert meta.calls[0][2]["headers"] == {"Authorization": "Bearer tok"}

    # A later catalogue pass has no rate. It must not wipe the enriched values.
    emit.ingest_catalogue(db, http=FakeHTTP(cmr_pages()))
    db.expire_all()
    p = db.query(PlumeDetection).one()
    assert p.emission_rate_kg_hr == 1000.0 and p.emission_uncertainty_kg_hr == 300.0
    assert p.geom_kind == "max_enhancement"
    assert p.raw_properties["metadata_properties"]["Wind Speed Source"] == "hrrr"
    assert round(db.execute(text("SELECT ST_X(geom) FROM plume_detections")).scalar(), 4) == -102.0489

    # Already enriched at this revision: nothing left to do, no network call.
    assert emit.enrich(db, http=FakeHTTP([]), token="tok") == 0


def test_revised_granule_is_enriched_again(db):
    emit.ingest_catalogue(db, http=FakeHTTP(cmr_pages()))
    emit.enrich(db, http=FakeHTTP([FakeResponse(load_fixture("emit_plume_metadata_quantified.json"))]), token="t")
    pages = cmr_pages()
    pages[0]._payload["items"][0]["meta"]["revision-date"] = "2026-09-01T00:00:00.000Z"
    emit.ingest_catalogue(db, http=FakeHTTP(pages))
    assert emit.enrich(db, http=FakeHTTP([FakeResponse(load_fixture("emit_plume_metadata_not_quantified.json"))]), token="t") == 1
    db.expire_all()
    assert db.query(PlumeDetection).one().emission_rate_kg_hr is None   # NASA withdrew the rate


def test_enrich_needs_token(db, monkeypatch):
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="EARTHDATA_TOKEN"):
        emit.enrich(db, http=FakeHTTP([]))


def test_rejected_token_fails_the_run_loudly(db):
    emit.ingest_catalogue(db, http=FakeHTTP(cmr_pages()))
    with pytest.raises(PermissionError):
        emit.enrich(db, http=FakeHTTP([FakeResponse({}, status=401)]), token="bad")
    db.expire_all()
    assert db.query(IngestionRun).order_by(IngestionRun.id.desc()).first().status == "failed"


def test_failed_run_is_recorded_and_writes_nothing(db):
    http = FakeHTTP([FakeResponse({}, status=500)])
    with pytest.raises(Exception):
        emit.ingest_catalogue(db, http=http)
    db.expire_all()
    run = db.query(IngestionRun).one()
    assert run.status == "failed" and "HTTPError" in run.error and run.finished_at
    assert db.query(PlumeDetection).count() == 0
