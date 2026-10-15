"""
Tests run against a real Postgres with PostGIS. Point TEST_DATABASE_URL at an
empty database you do not care about: the schema is dropped and rebuilt.

    TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/fluxara_test pytest
"""
import json
import os
import pathlib

import pytest

TEST_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_URL:
    pytest.exit("Set TEST_DATABASE_URL to an empty Postgres+PostGIS database.", returncode=2)
if "test" not in TEST_URL.rsplit("/", 1)[-1]:
    pytest.exit("Refusing to run: the TEST_DATABASE_URL database name must contain 'test'.", returncode=2)

# Must be set before any fluxara module is imported.
os.environ["DATABASE_URL"] = TEST_URL
os.environ["FLUXARA_ENV"] = "development"
os.environ["FLUXARA_SECRET_KEY"] = "test-secret-key-that-is-long-enough-000000"
os.environ["FLUXARA_DEV_KEY"] = "test-dev-key"
os.environ.pop("FLUXARA_ENABLE_LEGACY_INVERSION", None)

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(scope="session")
def alembic_cfg():
    from alembic.config import Config
    return Config(str(ROOT / "alembic.ini"))


@pytest.fixture(scope="session", autouse=True)
def schema(alembic_cfg):
    """Build the schema with the real migrations, not create_all()."""
    from alembic import command
    from sqlalchemy import text
    from fluxara.database.sync import get_engine
    engine = get_engine()
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    command.upgrade(alembic_cfg, "head")
    yield
    engine.dispose()


@pytest.fixture()
def db(schema):
    """A session on a clean set of tables."""
    from sqlalchemy import text
    from fluxara.database.sync import session_scope
    with session_scope() as s:
        s.execute(text("TRUNCATE plume_detections, satellite_scenes, ingestion_runs, "
                       "alerts, inversions, reports, generated_reports, facilities, "
                       "users, organisations RESTART IDENTITY CASCADE"))
    with session_scope() as s:
        yield s


class FakeResponse:
    def __init__(self, payload, status=200, headers=None):
        self._payload, self.status_code, self.headers = payload, status, headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"{self.status_code}")


class FakeHTTP:
    """Stands in for requests.Session. Serves queued responses, records calls."""
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def _next(self, method, url, **kw):
        self.calls.append((method, url, kw))
        r = self.responses.pop(0)
        return r(url, **kw) if callable(r) else r

    def get(self, url, **kw):
        return self._next("GET", url, **kw)

    def post(self, url, **kw):
        return self._next("POST", url, **kw)
