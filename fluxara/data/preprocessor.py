# fluxara/data/preprocessor.py
import numpy as np
from scipy.interpolate import RegularGridInterpolator

def detect_anomalies(ch4_grid, threshold=1870.0):
    """
    Return True where CH4 > threshold (ppb).
    """
    return ch4_grid > threshold

def quality_filter(ds):
    """
    Apply qa_value >= 0.5 and drop NaNs.
    """
    if 'qa_value' in ds:
        ds = ds.where(ds.qa_value >= 0.5)
    return ds.dropna(dim='latitude', how='all').dropna(dim='longitude', how='all')

def regrid_to_common_grid(data, source_lats, source_lons, target_lats, target_lons):
    """
    scipy-based regridding to align TROPOMI and ERA5.
    """
    interp = RegularGridInterpolator((source_lats, source_lons), data, bounds_error=False, fill_value=None)
    
    grid_lats, grid_lons = np.meshgrid(target_lats, target_lons, indexing='ij')
    points = np.stack([grid_lats.ravel(), grid_lons.ravel()], axis=-1)
    
    regridded = interp(points).reshape(len(target_lats), len(target_lons))
    return regridded.astype(np.float32)
