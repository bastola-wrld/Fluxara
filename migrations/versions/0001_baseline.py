"""Baseline: the tables that existed before migrations were introduced.

If your database was already created by the old create_all() startup code,
do not run this. Mark it as applied instead:

    alembic stamp 0001
    alembic upgrade head

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organisations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("org_type", sa.String(20), nullable=False),
        sa.Column("plan", sa.String(20)),
        sa.Column("country", sa.String(50)),
        sa.Column("active", sa.Boolean),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("ix_organisations_id", "organisations", ["id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255)),
        sa.Column("role", sa.String(20)),
        sa.Column("api_key", sa.String(64)),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("organisations.id")),
        sa.Column("active", sa.Boolean),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_api_key", "users", ["api_key"], unique=True)

    op.create_table(
        "facilities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("state", sa.String(2)),
        sa.Column("country", sa.String(3)),
        sa.Column("lat", sa.Float, nullable=False),
        sa.Column("lon", sa.Float, nullable=False),
        sa.Column("epa_reported", sa.Float),
        sa.Column("fluxara_latest", sa.Float),
        sa.Column("risk_level", sa.String(10)),
        sa.Column("sector", sa.String(50)),
        sa.Column("ghgrp_id", sa.String(50)),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("organisations.id")),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_facilities_id", "facilities", ["id"])

    op.create_table(
        "inversions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("facility_id", sa.Integer, sa.ForeignKey("facilities.id")),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("emission_rate", sa.Float),
        sa.Column("uncertainty", sa.Float),
        sa.Column("confidence", sa.Float),
        sa.Column("compute_ms", sa.Integer),
        sa.Column("tropomi_file", sa.String(255)),
        sa.Column("era5_file", sa.String(255)),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("ix_inversions_id", "inversions", ["id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("facility_id", sa.Integer, sa.ForeignKey("facilities.id")),
        sa.Column("alert_type", sa.String(50)),
        sa.Column("severity", sa.String(10)),
        sa.Column("message", sa.Text),
        sa.Column("emission_value", sa.Float),
        sa.Column("threshold_value", sa.Float),
        sa.Column("resolved", sa.Boolean),
        sa.Column("resolved_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("ix_alerts_id", "alerts", ["id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("facility_id", sa.Integer, sa.ForeignKey("facilities.id")),
        sa.Column("report_type", sa.String(50)),
        sa.Column("date_from", sa.Date),
        sa.Column("date_to", sa.Date),
        sa.Column("total_emissions", sa.Float),
        sa.Column("status", sa.String(20)),
        sa.Column("pdf_path", sa.String(255)),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("ix_reports_id", "reports", ["id"])

    op.create_table(
        "generated_reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("region", sa.String(100)),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("organisations.id")),
        sa.Column("facility_id", sa.Integer, sa.ForeignKey("facilities.id")),
        sa.Column("date_from", sa.Date),
        sa.Column("date_to", sa.Date),
        sa.Column("total_facilities", sa.Integer),
        sa.Column("total_emissions", sa.Float),
        sa.Column("pdf_data", sa.LargeBinary, nullable=False),
        sa.Column("file_size", sa.Integer),
        sa.Column("generated_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("ix_generated_reports_id", "generated_reports", ["id"])


def downgrade():
    for t in ("generated_reports", "reports", "alerts", "inversions",
              "facilities", "users", "organisations"):
        op.drop_table(t)
