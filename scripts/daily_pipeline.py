#!/usr/bin/env python3
"""
Daily ingestion of real satellite data. Run from cron or a scheduler:

    python scripts/daily_pipeline.py

Equivalent to:  python -m fluxara.ingest.run daily
Exit code is non zero if any source failed, so the scheduler can alert you.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fluxara.ingest.run import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(["daily"]))
