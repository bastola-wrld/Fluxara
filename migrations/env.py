"""Alembic environment. Run with:  alembic upgrade head"""
from logging.config import fileConfig

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy import create_engine, pool

from fluxara.database.connection import Base, DATABASE_URL
from fluxara.database.sync import sync_url
import fluxara.database.models  # noqa: F401  (registers all tables on Base.metadata)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
URL = sync_url(DATABASE_URL)

COMMON = dict(
    target_metadata=target_metadata,
    compare_type=True,
    # Ignore PostGIS's own tables (spatial_ref_sys etc.) during autogenerate
    include_object=alembic_helpers.include_object,
    process_revision_directives=alembic_helpers.writer,
    render_item=alembic_helpers.render_item,
)


def run_migrations_offline():
    context.configure(url=URL, literal_binds=True, **COMMON)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(URL, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, **COMMON)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
