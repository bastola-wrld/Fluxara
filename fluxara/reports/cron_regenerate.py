# fluxara/reports/cron_regenerate.py
"""
CLI script to trigger PDF regeneration.
Can be run via system cron: 
0 0 * * * /path/to/venv/bin/python /path/to/Fluxara/fluxara/reports/cron_regenerate.py
"""
import asyncio
import logging
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fluxara.reports.auto_generator import generate_all_reports

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fluxara.cron")

async def main():
    logger.info("Cron job: Starting manual PDF regeneration...")
    try:
        manifest = await generate_all_reports()
        if manifest:
            logger.info("Cron job: PDF regeneration successful.")
        else:
            logger.error("Cron job: PDF regeneration failed (no manifest generated).")
    except Exception as e:
        logger.error(f"Cron job: Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
