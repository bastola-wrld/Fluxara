import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.future import select

# Add project root to path
sys.path.append(os.getcwd())

from fluxara.database.connection import AsyncSessionLocal
from fluxara.database.models import Facility, Inversion, Alert
from fluxara.data.downloader import download_tropomi, download_era5
from fluxara.data.loader import load_tropomi, load_era5
from fluxara.data.preprocessor import prepare_model_input
from fluxara.api.model_loader import get_ensemble

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fluxara.pipeline")

async def run_daily_pipeline():
    logger.info("🚀 Starting Daily Fluxara Satellite Pipeline...")
    
    # 1. Determine Target Date (Satellite data has ~5 day lag)
    # For testing purposes, we'll allow an override via environment variable
    target_date_str = os.getenv("PIPELINE_DATE")
    if target_date_str:
        target_date = datetime.fromisoformat(target_date_str).date()
    else:
        target_date = (datetime.now() - timedelta(days=5)).date()
        
    date_str = target_date.isoformat()
    logger.info(f"📅 Target processing date: {date_str}")
    
    # 2. Get all active facilities
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Facility))
        facilities = result.scalars().all()
        
        if not facilities:
            logger.warning("⚠️ No facilities found in database. Exiting.")
            return

        logger.info(f"🔍 Found {len(facilities)} facilities to process.")

        # 3. Process each facility
        for facility in facilities:
            # Capture ID and name before commit/expiry
            f_id = facility.id
            f_name = facility.name
            f_lat = facility.lat
            f_lon = facility.lon

            try:
                logger.info(f"🏭 Processing: {f_name} (ID: {f_id}) at [{f_lat}, {f_lon}]")
                
                # Fetch Data (Mocked in downloader.py)
                era5_path = download_era5(date_str)
                tropomi_path = download_tropomi(date_str)
                
                if not era5_path or not tropomi_path:
                    logger.error(f"❌ Missing satellite data files for {date_str}. Skipping.")
                    continue
                
                # Load and Prepare Grids (Mocked in loader.py)
                wind_tensor = load_era5(era5_path, [f_lat-0.5, f_lon-0.5, f_lat+0.5, f_lon+0.5])
                ch4_grid = load_tropomi(tropomi_path, [f_lat-0.5, f_lon-0.5, f_lat+0.5, f_lon+0.5])
                model_input = prepare_model_input(wind_tensor, ch4_grid)
                
                # Run AI Inversion
                ensemble = get_ensemble()
                mean, std, confidence = ensemble.forward(model_input)
                
                # Calculate Emission Rate
                emission_rate = float(mean.sum().item())
                
                # 4. Save Inversion Record
                inv = Inversion(
                    facility_id=f_id,
                    date=target_date,
                    emission_rate=emission_rate,
                    confidence=float(confidence),
                    compute_ms=250
                )
                db.add(inv)
                
                # 5. Automatic Alert Logic
                if emission_rate > 50.0:
                    severity = "high" if emission_rate > 150 else "medium"
                    alert = Alert(
                        facility_id=f_id,
                        severity=severity,
                        message=f"🚨 AUTOMATIC DETECTION: High methane emission of {emission_rate:.1f} kg/hr detected.",
                        alert_type="satellite_detection",
                        emission_value=emission_rate,
                        threshold_value=50.0
                    )
                    db.add(alert)
                    logger.warning(f"💥 ALERT TRIGGERED for {f_name}: {emission_rate:.1f} kg/hr ({severity})")

                await db.commit()
                logger.info(f"✅ Successfully processed {f_name}")

            except Exception as e:
                logger.error(f"❌ Error processing facility {f_id}: {e}")
                await db.rollback()


    logger.info("🏁 Pipeline execution finished.")

if __name__ == "__main__":
    asyncio.run(run_daily_pipeline())
