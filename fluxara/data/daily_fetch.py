# fluxara/data/daily_fetch.py
"""
Long running scheduler for the `fetcher` container: runs ingestion once at
start, then every day at 06:00 UTC.
"""
import logging
import time

import schedule

from fluxara.ingest.run import run_daily

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("fluxara.fetcher")


def job():
    failures = run_daily()
    if failures:
        logger.error("Daily ingestion finished with %s failed job(s)", failures)
    else:
        logger.info("Daily ingestion finished")


if __name__ == "__main__":
    logger.info("Fluxara fetcher started")
    job()
    schedule.every().day.at("06:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)
