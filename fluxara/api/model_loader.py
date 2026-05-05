# fluxara/api/model_loader.py
import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAVE_DIR = "../satellite_data/processed"

# ─────────────────────────────────────────────────────────
# FNO Architecture (v2 — STILT trained)
# ─────────────────────────────────────────────────────────
class SpectralConv2d(nn.Module):
    def __init__(self, in_ch, out_ch, modes1, modes2):
        super().__init__()
        self.modes1  = modes1
        self.modes2  = modes2
        scale        = 1 / (in_ch * out_ch)
        self.weights = nn.Parameter(
            scale * torch.randn(in_ch, out_ch, modes1, modes2,
                                dtype=torch.cfloat)
        )
    def forward(self, x):
        B      = x.shape[0]
        x_ft   = torch.fft.rfft2(x)
        out_ft = torch.zeros(B, self.weights.shape[1],
                             x.size(-2), x.size(-1)//2+1,
                             dtype=torch.cfloat, device=x.device)
        out_ft[:, :, :self.modes1, :self.modes2] = torch.einsum(
            "bixy,ioxy->boxy",
            x_ft[:, :, :self.modes1, :self.modes2], self.weights
        )
        return torch.fft.irfft2(out_ft, s=(x.size(-2), x.size(-1)))

class FNOBlock(nn.Module):
    def __init__(self, width, modes):
        super().__init__()
        self.spectral = SpectralConv2d(width, width, modes, modes)
        self.residual = nn.Conv2d(width, width, kernel_size=1)
        self.norm     = nn.InstanceNorm2d(width)
    def forward(self, x):
        return F.gelu(self.norm(self.spectral(x) + self.residual(x)))

class FluxaraFNO_v2(nn.Module):
    def __init__(self, in_channels=6, out_channels=1,
                 width=48, modes=16, n_layers=6):
        super().__init__()
        self.lift   = nn.Conv2d(in_channels, width, kernel_size=1)
        self.blocks = nn.ModuleList(
            [FNOBlock(width, modes) for _ in range(n_layers)]
        )
        self.project = nn.Sequential(
            nn.Conv2d(width, 128, kernel_size=1), nn.GELU(),
            nn.Conv2d(128,   64, kernel_size=1), nn.GELU(),
            nn.Conv2d(64,  out_channels, kernel_size=1),
            nn.Softplus()
        )
    def forward(self, x):
        x   = self.lift(x)
        for block in self.blocks:
            x = block(x)
        out = self.project(x)
        return out / (out.sum(dim=[2,3], keepdim=True) + 1e-8)

# Alias so old imports still work
FluxaraInversionNet = FluxaraFNO_v2

# ─────────────────────────────────────────────────────────
# Singleton loader
# ─────────────────────────────────────────────────────────
_model  = None
_device = None

def get_model():
    global _model, _device

    if _model is not None:
        return _model, _device

    # Device selection
    if torch.backends.mps.is_available():
        _device = torch.device("mps")
    elif torch.cuda.is_available():
        _device = torch.device("cuda")
    else:
        _device = torch.device("cpu")

    print(f"Loading model on {_device}")

    # ── Try v2 checkpoint first (STILT-trained) ──
    v2_path = os.path.join(
        os.path.dirname(__file__),
        "../../satellite_data/processed/fluxara_fno_v2.pt"
    )

    # ── Fall back to STILT best checkpoint ──
    stilt_path = os.path.join(
        os.path.dirname(__file__),
        "../../checkpoints/fluxara_stilt_best.pt"
    )

    # ── Fall back to v1 ──
    v1_path = os.path.join(
        os.path.dirname(__file__),
        "../../satellite_data/processed/fluxara_fno_v1.pt"
    )

    # ── Fall back to original checkpoint ──
    legacy_path = os.path.join(
        os.path.dirname(__file__),
        "../../checkpoints/fluxara_best.pt"
    )

    if os.path.exists(v2_path):
        ckpt_path  = v2_path
        ckpt_label = "FNO v2 (STILT-trained)"
    elif os.path.exists(stilt_path):
        ckpt_path  = stilt_path
        ckpt_label = "STILT best checkpoint"
    elif os.path.exists(v1_path):
        ckpt_path  = v1_path
        ckpt_label = "FNO v1"
    elif os.path.exists(legacy_path):
        ckpt_path  = legacy_path
        ckpt_label = "legacy checkpoint"
    else:
        ckpt_path  = None
        ckpt_label = None

    if ckpt_path:
        print(f"Loading: {ckpt_label}")
        ckpt = torch.load(ckpt_path,
                          map_location="cpu",
                          weights_only=False)

        # Get config from checkpoint or use defaults
        cfg = ckpt.get("config", {
            "in_channels" : 6,
            "out_channels": 1,
            "width"       : 48,
            "modes"       : 16,
            "n_layers"    : 6,
        })

        _model = FluxaraFNO_v2(
            in_channels  = cfg.get("in_channels",  6),
            out_channels = cfg.get("out_channels", 1),
            width        = cfg.get("width",        48),
            modes        = cfg.get("modes",        16),
            n_layers     = cfg.get("n_layers",     6),
        ).to(_device)

        _model.load_state_dict(ckpt["model_state_dict"])
        print(f"✅ {ckpt_label} loaded on {_device}")

    else:
        print("⚠️  No checkpoint found — using untrained model")
        _model = FluxaraFNO_v2().to(_device)

    _model.eval()
    return _model, _device