#!/usr/bin/env python3
"""
Train Local Model (Fluxara FNIE)
Trains the FluxaraInversionNet using generated synthetic footprints.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import glob
import os
import time

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if torch.backends.mps.is_available():
    device = torch.device('mps')

class FluxaraDataset(Dataset):
    def __init__(self, data_dir='training_data', split='train'):
        self.files = sorted(glob.glob(f'{data_dir}/*.npz'))
        if len(self.files) == 0:
            raise ValueError('No .npz files found in training_data/. Run generate_stilt_data.py first.')
        
        n = len(self.files)
        split_idx = int(0.8 * n)
        
        if split == 'train':
            self.files = self.files[:split_idx]
        else:
            self.files = self.files[split_idx:]
            
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        sample = np.load(self.files[idx])
        wind_field = torch.FloatTensor(sample['wind_field'])
        footprint = torch.FloatTensor(sample['footprint'])
        return wind_field, footprint

class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.GELU(),
            nn.Dropout2d(0.1),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.GELU(),
            nn.Dropout2d(0.1),
        )
    def forward(self, x):
        return self.block(x)

class FluxaraInversionNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc1 = ConvBlock(6, 64)
        self.enc2 = ConvBlock(64, 128)
        self.enc3 = ConvBlock(128, 256)
        self.enc4 = ConvBlock(256, 512)
        self.bottleneck = ConvBlock(512, 1024)
        self.up4  = nn.ConvTranspose2d(1024, 512, 2, stride=2)
        self.dec4 = ConvBlock(1024, 512)
        self.up3  = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec3 = ConvBlock(512, 256)
        self.up2  = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec2 = ConvBlock(256, 128)
        self.up1  = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec1 = ConvBlock(128, 64)
        self.out  = nn.Sequential(nn.Conv2d(64, 1, 1), nn.Softplus())
        self.pool = nn.MaxPool2d(2)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))
        b  = self.bottleneck(self.pool(e4))
        d4 = self.dec4(torch.cat([self.up4(b), e4], dim=1))
        d3 = self.dec3(torch.cat([self.up3(d4), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        footprint = self.out(d1)
        return footprint / (footprint.sum(dim=[2,3], keepdim=True) + 1e-8)

class FluxaraLoss(nn.Module):
    def __init__(self):
        super().__init__()
    def forward(self, pred, target):
        mse = F.mse_loss(pred, target)
        cons = F.mse_loss(pred.sum(dim=[2,3]), target.sum(dim=[2,3]))
        smooth = (torch.abs(pred[:,:,1:,:] - pred[:,:,:-1,:]).mean() +
                  torch.abs(pred[:,:,:,1:] - pred[:,:,:,:-1]).mean())
        return mse + 0.1 * cons + 0.01 * smooth

def mae_percent(pred, target):
    mae = torch.abs(pred - target).mean()
    return (mae / (target.abs().mean() + 1e-8) * 100).item()

def r2_score(pred, target):
    p = pred.view(-1)
    t = target.view(-1)
    ss_res = ((t - p)**2).sum()
    ss_tot = ((t - t.mean())**2).sum()
    return (1 - ss_res / (ss_tot + 1e-8)).item()

def main():
    print(f'Using device: {device}')
    
    train_dataset = FluxaraDataset(split='train')
    val_dataset   = FluxaraDataset(split='val')
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    val_loader   = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)
    
    model = FluxaraInversionNet().to(device)
    criterion = FluxaraLoss()
    optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80, eta_min=1e-6)
    
    os.makedirs('checkpoints', exist_ok=True)
    EPOCHS = 80
    best_val_mae = float('inf')
    
    print('Training started...')
    start = time.time()
    
    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_losses = []
        for wind, foot in train_loader:
            wind, foot = wind.to(device), foot.to(device)
            optimizer.zero_grad()
            pred = model(wind)
            loss = criterion(pred, foot)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_losses.append(loss.item())
        
        model.eval()
        val_losses, val_maes, val_r2s = [], [], []
        with torch.no_grad():
            for wind, foot in val_loader:
                wind, foot = wind.to(device), foot.to(device)
                pred = model(wind)
                val_losses.append(criterion(pred, foot).item())
                val_maes.append(mae_percent(pred, foot))
                val_r2s.append(r2_score(pred, foot))
        
        scheduler.step()
        v_mae = np.mean(val_maes)
        
        if v_mae < best_val_mae:
            best_val_mae = v_mae
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
            }, 'checkpoints/fluxara_best.pt')
            
        if epoch % 5 == 0 or epoch == 1:
            mins = (time.time() - start) / 60
            print(f"Epoch {epoch:3d}/{EPOCHS} | Loss: {np.mean(val_losses):.4f} | MAE: {v_mae:.1f}% | R2: {np.mean(val_r2s):.3f} | {mins:.1f}min")

if __name__ == "__main__":
    main()
