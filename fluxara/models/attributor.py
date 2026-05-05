# fluxara/models/attributor.py
import numpy as np
from fluxara.data.facilities import spatial_query

UNIT_CONVERSION_FACTOR = 0.5367 # Placeholder for ppb-m to kg/hr conversion

def attribute(footprint, tropomi_ch4, facilities_df, boundary_layer_height=1000.0):
    """
    Attribute a detected plume to the nearest facility and estimate emission rate.
    """
    # 1. Find peak of footprint
    # footprint is [1, 64, 64]
    footprint_2d = footprint[0]
    idx = np.unravel_index(np.argmax(footprint_2d), footprint_2d.shape)
    
    # 2. Convert grid index to lat/lon (simplified - needs bbox context)
    # In a real app, we pass the bbox coordinates
    # For now, we return the relative peak location and confidence
    peak_val = footprint_2d[idx]
    
    # 3. Estimate emission rate
    # enhancement = peak_ch4 - background
    ch4_enhancement = np.max(tropomi_ch4) - np.mean(tropomi_ch4)
    
    # Simple mass balance estimation
    emission_rate = peak_val * ch4_enhancement * boundary_layer_height * UNIT_CONVERSION_FACTOR
    
    # 4. Confidence
    # Sharpness of the peak
    confidence = float(peak_val) # Normalised peak value is a good proxy for source clarity
    
    return {
        "emission_rate_kg_hr": float(emission_rate),
        "confidence": float(np.clip(confidence, 0.0, 1.0)),
        "peak_index": idx
    }
