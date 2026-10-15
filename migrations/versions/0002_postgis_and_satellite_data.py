"""PostGIS, facility geometry, and real satellite data tables.

Adds:
  * PostGIS extension
  * facilities.geom (POINT, 4326) with a GiST index, backfilled from lat/lon
    and kept in sync by a trigger
  * facilities.data_source
  * ingestion_runs, plume_detections, satellite_scenes

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SRID = 4326
TZ = sa.DateTime(timezone=True)


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ── facilities ───────────────────────────────────────────────────────────
    # An older optional code path may have created geom as geography. It is
    # fully derived from lat/lon, so rebuilding it loses nothing.
    op.execute("ALTER TABLE facilities DROP COLUMN IF EXISTS geom")
    op.add_column("facilities", sa.Column(
        "geom", Geometry("POINT", srid=SRID, spatial_index=False)))
    op.add_column("facilities", sa.Column(
        "data_source", sa.String(50), nullable=False,
        server_default="manual_unverified"))
    op.execute(f"""
        UPDATE facilities
           SET geom = ST_SetSRID(ST_MakePoint(lon, lat), {SRID})
         WHERE lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180
    """)
    op.create_index("ix_facilities_geom", "facilities", ["geom"],
                    postgresql_using="gist")
    op.execute(f"""
        CREATE OR REPLACE FUNCTION facilities_set_geom() RETURNS trigger AS $$
        BEGIN
            IF NEW.lat IS NULL OR NEW.lon IS NULL THEN
                NEW.geom := NULL;
            ELSE
                NEW.geom := ST_SetSRID(ST_MakePoint(NEW.lon, NEW.lat), {SRID});
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER facilities_set_geom
        BEFORE INSERT OR UPDATE OF lat, lon ON facilities
        FOR EACH ROW EXECUTE FUNCTION facilities_set_geom();
    """)
    # NOT VALID: enforced for new and changed rows, without failing on old bad rows.
    op.execute("""
        ALTER TABLE facilities ADD CONSTRAINT ck_facilities_lat_lon_range
        CHECK (lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180) NOT VALID
    """)

    # ── ingestion_runs ───────────────────────────────────────────────────────
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("params", JSONB, nullable=False, server_default="{}"),
        sa.Column("code_version", sa.String(64)),
        sa.Column("n_fetched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("n_inserted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("n_updated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", sa.Text),
        sa.Column("started_at", TZ, nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", TZ),
    )
    op.create_index("ix_ingestion_runs_source", "ingestion_runs", ["source"])

    # ── plume_detections ─────────────────────────────────────────────────────
    op.create_table(
        "plume_detections",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("instrument", sa.String(50), nullable=False),
        sa.Column("product", sa.String(100)),
        sa.Column("product_version", sa.String(20)),
        sa.Column("processing_version", sa.String(50)),
        sa.Column("source_url", sa.Text),
        sa.Column("source_revised_at", TZ),
        sa.Column("ingestion_run_id", sa.Integer, sa.ForeignKey("ingestion_runs.id")),
        sa.Column("raw_properties", JSONB, nullable=False, server_default="{}"),
        sa.Column("licence", sa.String(100), nullable=False),
        sa.Column("attribution", sa.Text, nullable=False),
        sa.Column("commercial_use_allowed", sa.Boolean, nullable=False),
        sa.Column("gas", sa.String(10), nullable=False, server_default="CH4"),
        sa.Column("observed_at", TZ, nullable=False),
        sa.Column("geom", Geometry("POINT", srid=SRID, spatial_index=False), nullable=False),
        sa.Column("geom_kind", sa.String(30), nullable=False),
        sa.Column("outline", Geometry("GEOMETRY", srid=SRID, spatial_index=False)),
        sa.Column("cloud_cover_pct", sa.Float),
        sa.Column("emission_rate_kg_hr", sa.Float),
        sa.Column("emission_uncertainty_kg_hr", sa.Float),
        sa.Column("max_enhancement_ppm_m", sa.Float),
        sa.Column("wind_speed_ms", sa.Float),
        sa.Column("wind_speed_std_ms", sa.Float),
        sa.Column("wind_source", sa.String(50)),
        sa.Column("fetch_length_m", sa.Float),
        sa.Column("first_seen_at", TZ, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TZ, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source", "source_id", name="uq_plume_source_id"),
        sa.CheckConstraint("emission_rate_kg_hr IS NULL OR emission_rate_kg_hr >= 0",
                           name="ck_plume_rate_non_negative"),
    )
    op.create_index("ix_plume_detections_observed_at", "plume_detections", ["observed_at"])
    op.create_index("ix_plume_detections_geom", "plume_detections", ["geom"],
                    postgresql_using="gist")

    # ── satellite_scenes ─────────────────────────────────────────────────────
    op.create_table(
        "satellite_scenes",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(50)),
        sa.Column("acquired_at", TZ, nullable=False),
        sa.Column("cloud_cover_pct", sa.Float),
        sa.Column("tile_id", sa.String(20)),
        sa.Column("footprint", Geometry("GEOMETRY", srid=SRID, spatial_index=False), nullable=False),
        sa.Column("assets", JSONB, nullable=False, server_default="{}"),
        sa.Column("licence", sa.String(100), nullable=False),
        sa.Column("attribution", sa.Text, nullable=False),
        sa.Column("ingestion_run_id", sa.Integer, sa.ForeignKey("ingestion_runs.id")),
        sa.Column("first_seen_at", TZ, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TZ, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source", "source_id", name="uq_scene_source_id"),
    )
    op.create_index("ix_satellite_scenes_acquired_at", "satellite_scenes", ["acquired_at"])
    op.create_index("ix_satellite_scenes_tile_id", "satellite_scenes", ["tile_id"])
    op.create_index("ix_satellite_scenes_footprint", "satellite_scenes", ["footprint"],
                    postgresql_using="gist")


def downgrade():
    op.drop_table("satellite_scenes")
    op.drop_table("plume_detections")
    op.drop_table("ingestion_runs")
    op.drop_constraint("ck_facilities_lat_lon_range", "facilities", type_="check")
    op.execute("DROP TRIGGER IF EXISTS facilities_set_geom ON facilities")
    op.execute("DROP FUNCTION IF EXISTS facilities_set_geom()")
    op.drop_index("ix_facilities_geom", table_name="facilities")
    op.drop_column("facilities", "data_source")
    op.drop_column("facilities", "geom")
    # PostGIS itself is left installed on purpose.
