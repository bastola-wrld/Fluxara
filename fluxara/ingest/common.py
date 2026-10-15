# fluxara/ingest/common.py
"""
Small helpers shared by every ingestion job.

1. make_http_session()  a web client that retries when a server has a hiccup
2. ingestion_run()      writes a row in ingestion_runs so we can see what ran
3. save_rows()          inserts new rows and updates rows we already have
"""
import logging
import os
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import tuple_
from sqlalchemy.dialects.postgresql import insert
from urllib3.util.retry import Retry

from fluxara.database.models import IngestionRun

log = logging.getLogger("fluxara.ingest")

HTTP_TIMEOUT = 60  # seconds to wait for a server before giving up


def make_http_session():
    """
    A requests session that tries again (up to 4 times, waiting a bit longer
    each time) when a server is busy or has a temporary error.
    """
    retry = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "fluxara-ingest/0.1"
    return session


def current_code_version():
    """The git commit we are running, so every run says which code made it."""
    if os.getenv("FLUXARA_CODE_VERSION"):
        return os.getenv("FLUXARA_CODE_VERSION")
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        )
        return commit.strip()
    except Exception:
        return "unknown"


def now_utc():
    return datetime.now(timezone.utc)


@contextmanager
def ingestion_run(session, source, params):
    """
    Use it like this:

        with ingestion_run(session, "nasa_emit", {"days": 30}) as run:
            ... fetch and save data, update run.n_fetched etc ...

    If the block finishes, the run is marked "success".
    If anything fails, everything the block wrote is undone, the run is marked
    "failed" with the error message, and the error is raised again so you see it.
    """
    run = IngestionRun(
        source=source,
        status="running",
        params=params,
        code_version=current_code_version(),
    )
    session.add(run)
    session.commit()  # save the "running" row straight away
    run_id = run.id

    try:
        yield run
    except Exception as error:
        session.rollback()  # throw away the half finished work
        failed_run = session.get(IngestionRun, run_id)
        failed_run.status = "failed"
        failed_run.error = f"{type(error).__name__}: {error}"[:2000]
        failed_run.finished_at = now_utc()
        session.commit()
        log.error("%s run %s failed: %s", source, run_id, error)
        raise

    run.status = "success"
    run.finished_at = now_utc()
    session.commit()
    log.info("%s run %s done: fetched=%s new=%s updated=%s",
             source, run_id, run.n_fetched, run.n_inserted, run.n_updated)


def save_rows(session, model, rows, update_columns, merge_json_columns=()):
    """
    Save rows into a table that has a unique (source, source_id) pair.

    New rows are inserted. Rows we already have are updated, but only in the
    columns listed in update_columns. Every other column keeps its old value.
    That is how a quick catalogue pass avoids wiping out details that a later,
    slower pass added.

    merge_json_columns: JSON columns where the new keys are added to the old
    object instead of replacing it.

    Safe to run again and again with the same data.
    Returns (number_inserted, number_updated).
    """
    # If the same plume appears twice in one batch, keep the last copy.
    unique_rows = {}
    for row in rows:
        unique_rows[(row["source"], row["source_id"])] = row
    rows = list(unique_rows.values())
    if not rows:
        return 0, 0

    table = model.__table__

    # Count how many of these we already have, so we can report new vs updated.
    keys = list(unique_rows.keys())
    already_there = session.query(table.c.source, table.c.source_id).filter(
        tuple_(table.c.source, table.c.source_id).in_(keys)
    ).count()

    # Postgres can insert and update in one statement ("upsert"). Send in
    # batches of 500 so a single statement never gets too big.
    for start in range(0, len(rows), 500):
        batch = rows[start:start + 500]
        statement = insert(table).values(batch)
        new_values = statement.excluded  # the values we just tried to insert

        changes = {"updated_at": now_utc()}
        for column in update_columns:
            if column in merge_json_columns:
                # For JSON, "old || new" joins both objects. New keys win.
                changes[column] = table.c[column].op("||")(new_values[column])
            else:
                changes[column] = new_values[column]

        statement = statement.on_conflict_do_update(
            index_elements=["source", "source_id"],
            set_=changes,
        )
        session.execute(statement)

    return len(rows) - already_there, already_there
