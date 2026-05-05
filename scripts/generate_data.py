# scripts/generate_data.py
import os
import numpy as np
import argparse
from tqdm import tqdm

def generate_sample(sample_id, output_dir):
    """
    Simulate a STILT footprint and wind field pair.
    Footprint: [1, 64, 64] - Sums to ~1.0
    Wind Field: [6, 64, 64] - Normalized u-wind at 6 levels
    """
    # Create a plausible footprint (gaussian plume simulation)
    footprint = np.zeros((1, 64, 64), dtype=np.float32)
    center_y, center_x = np.random.randint(10, 54), np.random.randint(10, 54)
    
    y, x = np.ogrid[:64, :64]
    # Plume follows random wind direction
    angle = np.random.uniform(0, 2 * np.pi)
    sigma_y, sigma_x = np.random.uniform(2, 5), np.random.uniform(5, 15)
    
    # Rotation
    rot_x = (x - center_x) * np.cos(angle) - (y - center_y) * np.sin(angle)
    rot_y = (x - center_x) * np.sin(angle) + (y - center_y) * np.cos(angle)
    
    # Plume mask (one-sided)
    plume = np.exp(-(rot_y**2 / (2 * sigma_y**2) + (rot_x > 0).astype(float) * rot_x**2 / (2 * sigma_x**2)))
    plume[rot_x < -2] = 0 # No plume behind source
    
    footprint[0] = plume / (plume.sum() + 1e-9)
    
    # Create a related wind field
    wind_field = np.random.normal(0, 1, (6, 64, 64)).astype(np.float32)
    # Add some vertical shear and coherence
    base_u = np.cos(angle) * 5.0
    for i in range(6):
        wind_field[i] += base_u * (1.0 + i * 0.2) # Wind speed increases with height
        
    # Save as .npz
    filename = f"sample_{sample_id:06d}.npz"
    np.savez_compressed(os.path.join(output_dir, filename), wind_field=wind_field, footprint=footprint)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--start", type=int, default=5000)
    parser.add_argument("--dir", type=str, default="training_data")
    args = parser.parse_args()
    
    os.makedirs(args.dir, exist_ok=True)
    
    logger_msg = f"Generating {args.count} samples starting from {args.start}..."
    print(logger_msg)
    
    for i in tqdm(range(args.start, args.start + args.count)):
        generate_sample(i, args.dir)
        
    print(f"✅ Generated {args.count} samples in {args.dir}")

if __name__ == "__main__":
    main()
