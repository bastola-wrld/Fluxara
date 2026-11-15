"""Sentinel 2 methane retrieval: scene angles and site_observations.

Adds:
  * satellite_scenes.relative_orbit, sun_elevation_deg, view_incidence_deg
  * site_observations: one row per (facility, image, method), including the
    checks that found nothing

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TZ = sa.DateTime(timezone=True)


def upgrade():
    op.add_column("satellite_scenes", sa.Column("relative_orbit", sa.Integer))
    op.add_column("satellite_scenes", sa.Column("sun_elevation_deg", sa.Float))
    op.add_column("satellite_scenes", sa.Column("view_incidence_deg", sa.Float))

    op.create_table(
        "site_observations",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("facility_id", sa.Integer,
                  sa.ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scene_id", sa.BigInteger,
                  sa.ForeignKey("satellite_scenes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_scene_id", sa.BigInteger,
                  sa.ForeignKey("satellite_scenes.id", ondelete="SET NULL")),
        sa.Column("method", sa.String(50), nullable=False),
        sa.Column("method_version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("observed_at", TZ, nullable=False),
        sa.Column("usable_fraction", sa.Float),
        sa.Column("noise_mol_m2", sa.Float),
        sa.Column("detection_limit_kg_hr", sa.Float),
        sa.Column("wind_speed_10m_ms", sa.Float),
        sa.Column("wind_from_deg", sa.Float),
        sa.Column("wind_source", sa.String(50)),
        sa.Column("plume_detection_id", sa.BigInteger,
                  sa.ForeignKey("plume_detections.id", ondelete="SET NULL")),
        sa.Column("distance_to_plume_m", sa.Float),
        sa.Column("wind_agreement", sa.String(20)),
        sa.Column("created_at", TZ, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TZ, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("facility_id", "scene_id", "method", name="uq_site_observation"),
        sa.CheckConstraint("status IN ('plume_detected', 'no_plume', 'unusable')",
                           name="ck_site_observation_status"),
    )
    op.create_index("ix_site_observations_facility_id", "site_observations", ["facility_id"])
    op.create_index("ix_site_observations_observed_at", "site_observations", ["observed_at"])


def downgrade():
    op.drop_table("site_observations")
    op.drop_column("satellite_scenes", "view_incidence_deg")
    op.drop_column("satellite_scenes", "sun_elevation_deg")
    op.drop_column("satellite_scenes", "relative_orbit")
