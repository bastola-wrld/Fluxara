# fluxara/data/daily_fetch.py
import logging
import schedule
import time
from datetime import datetime, timedelta
from fluxara.data.downloader import download_tropomi, download_era5
from fluxara.data.loader import load_tropomi, load_era5
from fluxara.data.preprocessor import prepare_model_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fluxara.fetcher")

def fetch_and_process_day(date_str: str, lat: float = 31.85, lon: float = -102.1):
    """
    Orchestrate the download and processing for a single day.
    """
    logger.info(f"--- Processing pipeline for {date_str} ---")
    
    # 1. Download
    era5_path = download_era5(date_str)
    tropomi_path = download_tropomi(date_str)
    
    if not era5_path:
        logger.error(f"Critical data (ERA5) missing for {date_str}. Aborting.")
        return
    
    # 2. Load & Grid
    logger.info("Loading and regridding NetCDF data...")
    wind_tensor = load_era5(era5_path, lat, lon)
    ch4_grid = load_tropomi(tropomi_path, lat, lon)
    
    # 3. Preprocess
    logger.info("Normalizing and preparing model input...")
    model_input = prepare_model_input(wind_tensor, ch4_grid)
    
    logger.info(f"✅ Pipeline complete for {date_str}. Input shape: {model_input.shape}")
    return model_input

def run_daily_job():
    # TROPOMI has ~5 day lag
    target_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    fetch_and_process_day(target_date)

if __name__ == "__main__":
    logger.info("Fluxara Daily Fetcher Orchestrator started.")
    
    # Backfill if needed
    run_daily_job()
    
    # Schedule
    schedule.every().day.at("08:00").do(run_daily_job)
    
    while True:
        schedule.run_pending()
        time.sleep(3600)