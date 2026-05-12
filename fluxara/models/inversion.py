# FIX #1 — fluxara/models/inversion.py
# Problem: No dropout → BayesianEnsemble always returns std=0, confidence=1.0
# Fix: Add nn.Dropout2d(p=0.1) to ConvBlock after each activation
# Apply by replacing fluxara/models/inversion.py with this file.

import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch, dropout_p=0.1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.GELU(),
            nn.Dropout2d(p=dropout_p),          # <-- ADDED: enables MC uncertainty
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.GELU(),
        )
    def forward(self, x):
        return self.block(x)


class FluxaraInversionNet(nn.Module):
    """
    U-Net atmospheric inversion with Multi-Sector Heads.
    Input:  [B, 6, 64, 64]  — wind field tensor
    Output: [B, 5, 64, 64]  — atmospheric footprints (sum to 1 per channel)
    
    Heads:
    0: Methane (General/Existing)
    1: Agriculture (N2O)
    2: Waste (CH4)
    3: Industry (CO2)
    4: Supply Chain (NO2)
    """
    def __init__(self, dropout_p=0.1):
        super().__init__()
        self.enc1       = ConvBlock(6, 64, dropout_p)
        self.enc2       = ConvBlock(64, 128, dropout_p)
        self.enc3       = ConvBlock(128, 256, dropout_p)
        self.enc4       = ConvBlock(256, 512, dropout_p)
        self.bottleneck = ConvBlock(512, 1024, dropout_p)
        self.up4        = nn.ConvTranspose2d(1024, 512, 2, stride=2)
        self.dec4       = ConvBlock(1024, 512, dropout_p)
        self.up3        = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec3       = ConvBlock(512, 256, dropout_p)
        self.up2        = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec2       = ConvBlock(256, 128, dropout_p)
        self.up1        = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec1       = ConvBlock(128, 64, dropout_p)
        
        # 5 output channels for 5 sector heads
        self.out        = nn.Sequential(nn.Conv2d(64, 5, 1), nn.Softplus())
        self.pool       = nn.MaxPool2d(2)

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
        fp = self.out(d1) # [B, 5, 64, 64]
        
        # Normalise each channel independently so footprints sum to 1
        return fp / (fp.sum(dim=[2, 3], keepdim=True) + 1e-8)

    def load_state_dict(self, state_dict, strict=True):
        """Map legacy checkpoint keys and handle multi-head weight expansion."""
        new_state_dict = {}
        # Check if legacy key shift is needed
        is_legacy = any('.block.3.' in k for k in state_dict.keys())
        
        for k, v in state_dict.items():
            new_key = k
            if is_legacy:
                if '.block.3.' in k:
                    new_key = k.replace('.block.3.', '.block.4.')
                elif '.block.4.' in k:
                    new_key = k.replace('.block.4.', '.block.5.')
            
            # Handle output layer expansion (1 channel -> 5 channels)
            if 'out.0.weight' in new_key and v.shape[0] == 1:
                v = v.repeat(5, 1, 1, 1)
            if 'out.0.bias' in new_key and v.shape[0] == 1:
                v = v.repeat(5)
                
            new_state_dict[new_key] = v
        return super().load_state_dict(new_state_dict, strict=False)