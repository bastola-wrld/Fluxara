# fluxara/data/facilities.py
import pandas as pd
import numpy as np

def load_ghgrp(csv_path):
    """
    Load EPA GHGRP facility CSV and filter to Oil and Gas sector.
    """
    df = pd.read_csv(csv_path, on_bad_lines='skip')

    
    # Required columns
    cols = ['facility_id', 'name', 'state', 'lat', 'lon', 'reported_ch4_kg_hr', 'sector', 'year']
    # Match actual CSV columns (may need adjustment based on real file)
    # df = df[cols] 
    
    # Filter to O&G (example SIC codes or sector names)
    if 'sector' in df.columns:
        df = df[df['sector'].str.contains('Oil and Gas', case=False, na=False)]
    
    if 'lat' not in df.columns or 'lon' not in df.columns:
        return pd.DataFrame()
    return df.dropna(subset=['lat', 'lon'])

def spatial_query(peak_lat, peak_lon, facilities_df, radius_km=50):
    """
    Find the nearest facility within radius using Haversine distance.
    """
    if facilities_df.empty:
        return None
        
    # Haversine calculation
    R = 6371.0
    phi1, phi2 = np.radians(peak_lat), np.radians(facilities_df['lat'])
    dphi = np.radians(facilities_df['lat'] - peak_lat)
    dlambda = np.radians(facilities_df['lon'] - peak_lon)
    
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distances = R * c
    
    facilities_df = facilities_df.assign(dist=distances)
    nearest = facilities_df[facilities_df['dist'] <= radius_km].sort_values('dist')
    
    if nearest.empty:
        return None
    return nearest.iloc[0]
