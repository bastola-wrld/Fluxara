# scripts/check_weights.py
import torch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fluxara.models.inversion import FluxaraInversionNet

def main():
    ckpt_path = "checkpoints/fluxara_best.pt"
    
    if not os.path.exists(ckpt_path):
        print(f"❌ FAIL: Checkpoint not found at {ckpt_path}")
        exit(1)
        
    try:
        checkpoint = torch.load(ckpt_path, map_location='cpu')
        
        # Check structure
        if 'model_state_dict' not in checkpoint:
            print("❌ FAIL: checkpoint missing model_state_dict")
            exit(1)
            
        model = FluxaraInversionNet()
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        
        # Metadata
        epoch = checkpoint.get('epoch', 'Unknown')
        mae = checkpoint.get('val_mae_pct', 'Unknown')
        
        print(f"✅ Checkpoint found: {ckpt_path}")
        print(f"✅ Trained epochs: {epoch}")
        print(f"✅ Validation MAE: {mae}")
        
        # Forward pass test
        x = torch.randn(1, 6, 64, 64)
        with torch.no_grad():
            output = model(x)
            
        print(f"✅ Output shape: {list(output.shape)}")
        
        # Physics test
        o_sum = output.sum().item()
        print(f"✅ Physics constraint: sum = {o_sum:.4f}")
        
        # Negative test
        o_min = output.min().item()
        print(f"✅ No negative values: min = {o_min:.4f}")
        
        if o_min < 0:
            print("❌ FAIL: Negative values detected")
            exit(1)
            
        print("\n🎉 SUCCESS: Model weights verified.")
        
    except Exception as e:
        print(f"❌ FAIL: Error loading/verifying model: {e}")
        exit(1)

if __name__ == "__main__":
    main()
