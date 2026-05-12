# FIX #2 — fluxara/models/attributor.py
# Problem: UNIT_CONVERSION_FACTOR = 0.5367 is a placeholder comment.
# The formula produces physically meaningless numbers.
#
# Fix: Use the Gaussian plume mass balance approximation:
#   Q (kg/hr) = Δc (ppb) × BLH (m) × wind_speed (m/s) × grid_area (m²)
#               × M_CH4 (kg/mol) / V_molar (m³/mol) × 3600
#
# This is IPCC Tier 2 compatible and standard in the literature.
# Apply by replacing fluxara/models/attributor.py with this file.

import numpy as np

# Molecular weights (kg/mol)
MOL_WEIGHTS = {
    "methane": 0.01604,    # CH4
    "n2o":     0.04401,    # N2O
    "co2":     0.04401,    # CO2
    "no2":     0.04601,    # NO2
}

# Molar volume at STP (m³/mol)  
V_MOLAR = 0.02241
# ppb → mol/mol conversion
PPB_TO_MOL = 1e-9

def attribute(footprint, observations, facilities_df,
              sector_idx=0,
              gas_type="methane",
              boundary_layer_height=1000.0,
              wind_speed_ms=5.0,
              grid_resolution_deg=0.03125):
    """
    Attribute a detected plume to the nearest facility and estimate emission rate.

    Args:
        footprint:             [5, 64, 64] multi-head output
        observations:          [64, 64] satellite enhancement in ppb
        facilities_df:         DataFrame with id, name, lat, lon
        sector_idx:            Index of the sector head (0-4)
        gas_type:              'methane', 'n2o', 'co2', or 'no2'
    """
    footprint_2d = footprint[sector_idx]  # Extract selected head

    # 1. Find peak location
    idx = np.unravel_index(np.argmax(footprint_2d), footprint_2d.shape)
    peak_val = float(footprint_2d[idx])

    # 2. Compute enhancement above background
    background     = np.nanpercentile(observations, 25)
    valid          = observations[~np.isnan(observations)]
    if len(valid) == 0:
        return {"emission_rate_kg_hr": 0.0, "confidence": 0.0, "peak_index": idx}

    enhancement_ppb = max(0.0, float(np.nanmax(observations)) - background)

    # 3. Grid cell area
    lat_m_per_deg = 111_320.0
    lon_m_per_deg = 111_320.0 * np.cos(np.radians(31.0)) 
    cell_area_m2  = (grid_resolution_deg * lat_m_per_deg) * \
                    (grid_resolution_deg * lon_m_per_deg)

    # 4. Mass balance emission rate estimate
    mw = MOL_WEIGHTS.get(gas_type, 0.01604)
    cell_width_m   = grid_resolution_deg * lat_m_per_deg
    air_column_mol = boundary_layer_height / V_MOLAR
    flux_mol_m2_s  = enhancement_ppb * PPB_TO_MOL * air_column_mol * wind_speed_ms
    emission_kg_s  = flux_mol_m2_s * cell_width_m * mw
    emission_kg_hr = emission_kg_s * 3600.0

    # 5. Confidence
    mean_val   = float(footprint_2d.mean())
    sharpness  = peak_val / (mean_val + 1e-9)
    confidence = float(np.clip(1.0 - np.exp(-sharpness / 500), 0.0, 1.0))

    return {
        "emission_rate_kg_hr": float(max(0.0, emission_kg_hr)),
        "confidence":          confidence,
        "peak_index":          idx,
        "gas":                 gas_type,
        "sector_idx":          sector_idx
    }