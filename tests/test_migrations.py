from alembic import command
from sqlalchemy import inspect, text

from fluxara.database.sync import get_engine


def test_schema_has_postgis_tables_and_gist_indexes():
    eng = get_engine()
    insp = inspect(eng)
    tables = set(insp.get_table_names())
    assert {"facilities", "plume_detections", "satellite_scenes", "ingestion_runs"} <= tables
    with eng.connect() as c:
        assert c.execute(text("SELECT count(*) FROM pg_extension WHERE extname='postgis'")).scalar() == 1
        gist = {r[0] for r in c.execute(text(
            "SELECT indexname FROM pg_indexes WHERE indexdef ILIKE '%USING gist%'"))}
    assert {"ix_facilities_geom", "ix_plume_detections_geom", "ix_satellite_scenes_footprint"} <= gist


def test_models_match_migrations(alembic_cfg):
    """Fails if someone changes models.py without writing a migration."""
    command.check(alembic_cfg)


def test_downgrade_and_upgrade_round_trip(alembic_cfg):
    command.downgrade(alembic_cfg, "0001")
    assert "plume_detections" not in inspect(get_engine()).get_table_names()
    command.upgrade(alembic_cfg, "head")
    assert "plume_detections" in inspect(get_engine()).get_table_names()


def test_facility_geom_follows_lat_lon(db):
    db.execute(text("INSERT INTO facilities (name, lat, lon) VALUES ('A', 31.67, 6.07)"))
    x, y, src = db.execute(text(
        "SELECT ST_X(geom), ST_Y(geom), data_source FROM facilities WHERE name='A'")).one()
    assert (round(x, 2), round(y, 2)) == (6.07, 31.67)      # x is longitude, y is latitude
    assert src == "manual_unverified"
    db.execute(text("UPDATE facilities SET lat = 10, lon = 20 WHERE name='A'"))
    assert db.execute(text("SELECT ST_X(geom), ST_Y(geom) FROM facilities WHERE name='A'")).one() == (20, 10)


def test_impossible_coordinates_are_rejected(db):
    import pytest
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        db.execute(text("INSERT INTO facilities (name, lat, lon) VALUES ('bad', 131.0, 6.0)"))
    db.rollback()
