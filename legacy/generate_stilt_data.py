#!/usr/bin/env python3
"""
Generate Synthetic Training Data (STILT Footprints)
Simulates atmospheric footprints mathematically for initial training.
"""
import numpy as np
import os
import argparse

def generate_synthetic_footprint(wind_u, wind_v, source_lat, source_lon, grid_size=64):
    x = np.linspace(-2, 2, grid_size)
    y = np.linspace(-2, 2, grid_size)
    xx, yy = np.meshgrid(x, y)
    
    wind_speed = np.sqrt(wind_u**2 + wind_v**2) + 0.1
    wind_dir_x = wind_u / wind_speed
    wind_dir_y = wind_v / wind_speed
    
    # Gaussian footprint
    sigma_along = 0.3 + 0.1 * wind_speed
    sigma_cross = 0.15
    
    cos_a = wind_dir_x
    sin_a = wind_dir_y
    xx_rot = xx * cos_a + yy * sin_a
    yy_rot = -xx * sin_a + yy * cos_a
    
    footprint = np.exp(
        -(xx_rot - 0.5)**2 / (2 * sigma_along**2) 
        - yy_rot**2 / (2 * sigma_cross**2)
    )
    
    footprint += np.random.exponential(0.01, footprint.shape)
    footprint = np.maximum(footprint, 0)
    footprint /= (footprint.sum() + 1e-8)
    
    return footprint

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=5000, help="Number of training pairs to generate")
    args = parser.parse_args()

    os.makedirs("training_data", exist_ok=True)
    np.random.seed(42)
    
    print(f"Generating {args.samples} synthetic training pairs...")
    
    for i in range(args.samples):
        wind_u = np.random.uniform(-15, 15, (64, 64))
        wind_v = np.random.uniform(-15, 15, (64, 64))
        temp   = np.random.uniform(270, 310, (64, 64))
        blh    = np.random.uniform(200, 2000, (64, 64))
        press  = np.random.uniform(850, 1013, (64, 64))
        stab   = np.random.uniform(0, 1, (64, 64))
        
        wind_field = np.stack([wind_u, wind_v, temp, blh, press, stab])
        mean_u = wind_u.mean()
        mean_v = wind_v.mean()
        
        footprint = generate_synthetic_footprint(mean_u, mean_v, 0, 0, 64)
        footprint = footprint[np.newaxis, :, :]
        
        np.savez_compressed(
            f"training_data/sample_{i:06d}.npz",
            wind_field=wind_field.astype(np.float32),
            footprint=footprint.astype(np.float32)
        )
        
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i+1}/{args.samples} samples")
            
    print(f"\nDone — saved to training_data/")

if __name__ == "__main__":
    main()
