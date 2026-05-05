# fluxara/training/dataset.py
import os
import glob
import numpy as np
import torch
from torch.utils.data import Dataset

class STILTDataset(Dataset):
    def __init__(self, data_dir: str, transform=None):
        """
        data_dir: Path to folder containing .npz training pairs
        """
        self.files = glob.glob(os.path.join(data_dir, "*.npz"))
        self.transform = transform
        
    def __len__(self):
        return len(self.files)
        
    def __getitem__(self, idx):
        data = np.load(self.files[idx])
        
        # wind: [6, 64, 64], footprint: [1, 64, 64]
        wind = data['wind_field'].astype(np.float32)
        footprint = data['footprint'].astype(np.float32)
        
        # Basic normalization
        wind = (wind - wind.mean()) / (wind.std() + 1e-8)
        
        wind_tensor = torch.from_numpy(wind)
        fp_tensor = torch.from_numpy(footprint)
        
        if self.transform:
            wind_tensor = self.transform(wind_tensor)
            
        return wind_tensor, fp_tensor
