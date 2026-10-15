# fluxara/database/sync.py
"""
Database access for terminal jobs (data ingestion, seeding, migrations).

The API uses the async version in connection.py because it serves many
requests at once. Jobs run one step after another, so the plain (sync)
version is simpler here.
"""
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fluxara.database.connection import DATABASE_URL


def sync_url(url=DATABASE_URL):
    """The API's address uses the asyncpg driver. Jobs use psycopg2 instead."""
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)


_engine = None
_make_session = None


def get_engine():
    """Create the database connection once and reuse it."""
    global _engine, _make_session
    if _engine is None:
        _engine = create_engine(sync_url(os.getenv("DATABASE_URL", DATABASE_URL)))
        _make_session = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


@contextmanager
def session_scope():
    """
    Use it like this:

        with session_scope() as session:
            session.add(...)

    Everything is saved at the end. If an error happens, nothing is saved.
    """
    get_engine()
    session = _make_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
