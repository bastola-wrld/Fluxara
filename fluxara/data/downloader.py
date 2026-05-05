# fluxara/data/downloader.py
import os
import cdsapi
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fluxara.downloader")

# Check for .cdsapirc
if not os.path.exists(os.path.expanduser("~/.cdsapirc")):
    logger.warning("~/.cdsapirc not found. CDS downloads will fail until configured.")

class CDSDownloader:
    def __init__(self, output_dir="satellite_data"):
        self.c = cdsapi.Client()
        self.output_dir = output_dir
        os.makedirs(f"{output_dir}/tropomi", exist_ok=True)
        os.makedirs(f"{output_dir}/era5", exist_ok=True)

    def download_tropomi(self, date, bbox):
        """
        Download TROPOMI CH4 Column Volume Mixing Ratio.
        bbox: [lat_min, lon_min, lat_max, lon_max]
        """
        filename = f"tropomi_{date}_{'_'.join(map(str, bbox))}.nc"
        filepath = os.path.join(self.output_dir, "tropomi", filename)

        if os.path.exists(filepath):
            logger.info(f"TROPOMI data already exists: {filename}")
            return filepath

        logger.info(f"Downloading TROPOMI for {date}...")
        try:
            self.c.retrieve(
                'satellite-methane',
                {
                    'format': 'netcdf',
                    'variable': 'ch4_column_volume_mixing_ratio_dry_air',
                    'sensor': 'tropomi_proxy_nir_swir',
                    'year': date.split('-')[0],
                    'month': date.split('-')[1],
                    'day': date.split('-')[2],
                    # Bounding box [North, West, South, East]
                    'area': [bbox[2], bbox[1], bbox[0], bbox[3]],
                },
                filepath
            )
            return filepath
        except Exception as e:
            logger.error(f"Failed to download TROPOMI for {date}: {e}")
            return None

    def download_era5(self, date, bbox):
        """
        Download ERA5 wind components at multiple pressure levels.
        """
        filename = f"era5_{date}_{'_'.join(map(str, bbox))}.nc"
        filepath = os.path.join(self.output_dir, "era5", filename)

        if os.path.exists(filepath):
            logger.info(f"ERA5 data already exists: {filename}")
            return filepath

        logger.info(f"Downloading ERA5 for {date}...")
        try:
            self.c.retrieve(
                'reanalysis-era5-pressure-levels',
                {
                    'product_type': 'reanalysis',
                    'format': 'netcdf',
                    'variable': [
                        'u_component_of_wind', 'v_component_of_wind',
                        'boundary_layer_height', 'temperature'
                    ],
                    'pressure_level': ['1000', '925', '850', '700', '500', '250'],
                    'year': date.split('-')[0],
                    'month': date.split('-')[1],
                    'day': date.split('-')[2],
                    'time': '12:00', # Approximate satellite overpass time
                    'area': [bbox[2], bbox[1], bbox[0], bbox[3]],
                },
                filepath
            )
            return filepath
        except Exception as e:
            logger.error(f"Failed to download ERA5 for {date}: {e}")
            return None

    def batch_download(self, dates, bbox, workers=4):
        """
        Download TROPOMI and ERA5 data for a range of dates in parallel.
        """
        with ThreadPoolExecutor(max_workers=workers) as executor:
            tasks = []
            for date in dates:
                tasks.append(executor.submit(self.download_tropomi, date, bbox))
                tasks.append(executor.submit(self.download_era5, date, bbox))
            
            for _ in tqdm(tasks, desc="Cloud Data Acquisition"):
                pass # Results logged internally
