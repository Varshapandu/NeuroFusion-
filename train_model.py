import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from tqdm import tqdm
from torch.utils.data import DataLoader, random_split
from src.models.neurofusion_model import NeuroFusionNet
from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset

# ---------------- CONFIG ----------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f" Using device: {device}")

# Paths
CACHE_DIR = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\cache"
CSV_PATH = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\train.csv"
MODEL_SAVE_PATH = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\models\neurofusion_best.pt"

#  Ensure save directory exists
os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)

# Training parameters
BATCH_SIZE = 8
EPOCHS = 15
LEARNING_RATE = 1e-5  #  Lowered for stability
NUM_CLASSES = 6

# ---------------- LOAD DATASET ----------------
print(" Loading EEG dataset...")
df = pd.read_csv(CSV_PATH)
dataset = NeuroFusionDualStreamDataset(df, CACHE_DIR)
print(f" Dataset ready with {len(dataset)} samples.")

# Split into train/validation
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_set, val_set = random_split(dataset, [train_size, val_size])

train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, pin_memory=True)
val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=0, pin_memory=True)

# ---------------- MODEL, LOSS, OPTIMIZER ----------------
model = NeuroFusionNet(num_classes=NUM_CLASSES).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
# scaler = torch.amp.GradScaler('cuda')  #  new syntax (avoid deprecation warning)
# ---- Resume from checkpoint if available ----
CHECKPOINT_PATH = MODEL_SAVE_PATH.replace(".pt", "_checkpoint.pth")
start_epoch = 1  # default if no checkpoint

if os.path.exists(CHECKPOINT_PATH):
    print(f"🔁 Found checkpoint at {CHECKPOINT_PATH}. Resuming training...")
    checkpoint = torch.load(CHECKPOINT_PATH, map_location=device)
    model.load_state_dict(checkpoint["model_state"])
    optimizer.load_state_dict(checkpoint["optimizer_state"])
    best_val_acc = checkpoint["best_val_acc"]
    start_epoch = checkpoint["epoch"] + 1
    print(f"✅ Resumed from epoch {checkpoint['epoch']} (Best Val Acc: {best_val_acc:.4f})")
else:
    print("🆕 No checkpoint found. Starting fresh training.")

best_val_acc = 0.0

# ---------------- TRAIN LOOP ----------------
def train_epoch():
    model.train()
    running_loss, correct, total = 0, 0, 0
    pbar = tqdm(train_loader, desc=" Training", leave=False)
    for waveform, spectrogram, labels in pbar:
        waveform, spectrogram, labels = waveform.to(device), spectrogram.to(device), labels.to(device)

        optimizer.zero_grad()

        # ----- Forward Pass (no AMP for stability test) -----
        outputs = model(waveform, spectrogram)
        loss = criterion(outputs, labels)

        # ----- NaN / Inf check -----
        if not torch.isfinite(loss):
            print(" NaN or Inf loss — skipping batch.")
            print("   waveform mean:", waveform.mean().item(), "std:", waveform.std().item())
            print("   spec mean:", spectrogram.mean().item(), "std:", spectrogram.std().item())
            continue

        # ----- Backward -----
        loss.backward()

        # Clip gradients to prevent explosion
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()

        running_loss += loss.item() * labels.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

        pbar.set_postfix(loss=float(loss.item()))

    return running_loss / total, correct / total


# ---------------- VALIDATION LOOP ----------------
def evaluate_epoch():
    model.eval()
    running_loss, correct, total = 0, 0, 0
    with torch.no_grad():
        for waveform, spectrogram, labels in tqdm(val_loader, desc=" Validation", leave=False):
            waveform, spectrogram, labels = waveform.to(device), spectrogram.to(device), labels.to(device)
            with torch.amp.autocast('cuda'):
                outputs = model(waveform, spectrogram)
                loss = criterion(outputs, labels)

            running_loss += loss.item() * labels.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

    return running_loss / total, correct / total


# ---------------- MAIN TRAINING ----------------
print(" Starting training process...")
for epoch in range(start_epoch, EPOCHS + 1):

    train_loss, train_acc = train_epoch()
    val_loss, val_acc = evaluate_epoch()

    print(f" Epoch [{epoch}/{EPOCHS}] "
          f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f} | "
          f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

    CHECKPOINT_PATH = MODEL_SAVE_PATH.replace(".pt", "_checkpoint.pth")

    if val_acc > best_val_acc and torch.isfinite(torch.tensor(val_loss)):
        best_val_acc = val_acc
        checkpoint = {
            "epoch": epoch,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "best_val_acc": best_val_acc,
        }
        torch.save(checkpoint, CHECKPOINT_PATH)
        print(f"💾 Saved checkpoint at epoch {epoch} with acc {val_acc:.4f}")

print(" Training complete. Best Validation Accuracy:", best_val_acc)
