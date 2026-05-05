# scripts/check_data_integrity.py
import os
import numpy as np
from tqdm import tqdm

def check_file(filepath):
    """
    Verify shapes and physics constraints of a training sample.
    """
    try:
        data = np.load(filepath)
        wind = data['wind_field']
        footprint = data['footprint']
        
        # Shape Checks
        if wind.shape != (6, 64, 64):
            return False, f"Wind shape mismatch: {wind.shape}"
        if footprint.shape != (1, 64, 64):
            return False, f"Footprint shape mismatch: {footprint.shape}"
            
        # Physics Checks
        f_sum = footprint.sum()
        if not (0.9 < f_sum < 1.1):
            return False, f"Physics violation: footprint sum {f_sum:.4f}"
            
        # Value Checks
        if np.isnan(wind).any() or np.isinf(wind).any():
            return False, "NaN/Inf in wind field"
        if np.isnan(footprint).any() or np.isinf(footprint).any():
            return False, "NaN/Inf in footprint"
            
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    data_dir = "training_data"
    files = [f for f in os.listdir(data_dir) if f.endswith('.npz')]
    
    passed = 0
    failed = []
    
    print(f"Scanning {len(files)} files for integrity...")
    for f in tqdm(files):
        filepath = os.path.join(data_dir, f)
        ok, msg = check_file(filepath)
        if ok:
            passed += 1
        else:
            failed.append((f, msg))
            
    pass_rate = (passed / len(files)) * 100 if files else 0
    print(f"\nSummary:")
    print(f"Total Samples: {len(files)}")
    print(f"Passed:        {passed}")
    print(f"Failed:        {len(failed)}")
    print(f"Pass Rate:     {pass_rate:.2f}%")
    
    if failed:
        print("\nFailed File Samples:")
        for f, msg in failed[:10]:
            print(f"- {f}: {msg}")
            
    if pass_rate < 99:
        print("\n❌ FAIL: Pass rate below 99%. Integrity check failed.")
        exit(1)
    else:
        print("\n✅ PASS: Data integrity verified.")

if __name__ == "__main__":
    main()
