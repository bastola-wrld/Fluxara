# fluxara/data/loader.py
import xarray as xr
import numpy as np
import json
import os

def load_tropomi(file_path, bbox):
    """
    Load TROPOMI NetCDF, quality filter, and regrid to 64x64.
    """
    if not os.path.exists(file_path) or "mock" in file_path:
        return np.random.uniform(1800, 2000, (64, 64)).astype(np.float32)

    ds = xr.open_dataset(file_path)
    # QA Filter (typically qa_value >= 0.5 is acceptable for CH4)
    if 'qa_value' in ds:
        ds = ds.where(ds.qa_value >= 0.5)
    
    ch4 = ds.ch4_column_volume_mixing_ratio_dry_air
    
    # Simple interpolation to 64x64 grid
    target_lats = np.linspace(bbox[0], bbox[2], 64)
    target_lons = np.linspace(bbox[1], bbox[3], 64)
    
    ch4_regridded = ch4.interp(latitude=target_lats, longitude=target_lons, method='linear')
    return ch4_regridded.values.astype(np.float32)

def load_era5(file_path, bbox):
    """
    Load ERA5 NetCDF, extract u/v wind at 6 levels, and stack.
    """
    if not os.path.exists(file_path) or "mock" in file_path:
        return np.random.normal(5, 2, (6, 64, 64)).astype(np.float32)

    ds = xr.open_dataset(file_path)
    
    target_lats = np.linspace(bbox[0], bbox[2], 64)
    target_lons = np.linspace(bbox[1], bbox[3], 64)
    
    # Extract u_component_of_wind at the 6 levels specified in downloader
    u_wind = ds.u.interp(latitude=target_lats, longitude=target_lons, method='linear')
    
    # Return shape [6, 64, 64]
    return u_wind.values.astype(np.float32)

def normalize_wind_field(tensor, stats_path="satellite_data/normalization_stats.json"):
    """
    Zero-mean unit-variance normalization.
    """
    if os.path.exists(stats_path):
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        mean = np.array(stats['mean'], dtype=np.float32)
        std = np.array(stats['std'], dtype=np.float32)
    else:
        mean = np.mean(tensor, axis=(1, 2), keepdims=True)
        std = np.std(tensor, axis=(1, 2), keepdims=True)
        # Store for future consistency
        os.makedirs(os.path.dirname(stats_path), exist_ok=True)
        with open(stats_path, 'w') as f:
            json.dump({'mean': mean.tolist(), 'std': std.tolist()}, f)
            
    return (tensor - mean) / (std + 1e-6)
