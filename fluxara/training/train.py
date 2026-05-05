import torch
import os
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from fluxara.models.inversion import FluxaraInversionNet
from fluxara.training.dataset import STILTDataset

def train():
    # 1. Config
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    batch_size = 16
    epochs = 80
    lr = 3e-4
    
    # 2. Data
    full_dataset = STILTDataset("training_data/")
    if len(full_dataset) == 0:
        print("Error: No training data found in training_data/")
        return
        
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_ds, val_ds = random_split(full_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    
    # 3. Model
    model = FluxaraInversionNet().to(device)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.MSELoss()
    
    # 4. Loop
    print(f"Starting training on {device}...")
    best_val_loss = float('inf')
    patience = 7
    no_improve = 0
    
    os.makedirs("checkpoints", exist_ok=True)

    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            pred = model(x)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        scheduler.step()
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                pred = model(x)
                val_loss += criterion(pred, y).item()
        
        avg_val_loss = val_loss / len(val_loader)
        print(f"Epoch {epoch+1}/{epochs} - Train: {train_loss/len(train_loader):.6f}, Val: {avg_val_loss:.6f}")
        
        # Save best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), "checkpoints/fluxara_best.pt")
            print(f"🌟 Best model saved at epoch {epoch+1}")
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"🛑 Early stopping triggered at epoch {epoch+1}")
                break

    print("✅ Training complete!")

if __name__ == "__main__":
    train()
