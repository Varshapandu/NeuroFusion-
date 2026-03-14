#
# import os
# import numpy as np
# import torch
# import torch.nn as nn
# import torch.optim as optim
# import pandas as pd
# from tqdm import tqdm
# from torch.utils.data import DataLoader
# from collections import Counter
#
# from src.models.neurofusion_model import NeuroFusionNet
# from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset
#
#
# def main():
#     # ---------------- CONFIG ----------------
#     torch.backends.cudnn.benchmark = True
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     print(f" Using device: {device}")
#
#     # =====================================================
#     # PATHS (UNCHANGED)
#     # =====================================================
#     PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
#
#     TRAIN_CACHE = os.path.join(PROJECT_ROOT, "Dataset", "splits", "train")
#     VAL_CACHE   = os.path.join(PROJECT_ROOT, "Dataset", "splits", "val")
#
#     CSV_PATH = os.path.join(PROJECT_ROOT, "Dataset", "train.csv")
#     MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT, "models", "neurofusion_best_fast.pt")
#     os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
#
#     # Training parameters
#     BATCH_SIZE = 16
#     EPOCHS = 40
#     LEARNING_RATE = 1e-4
#     NUM_CLASSES = 6
#     ACCUM_STEPS = 2
#
#     # ---------------- LOAD DATASET ----------------
#     print(" Loading EEG dataset...")
#     df = pd.read_csv(CSV_PATH)
#
#     train_set = NeuroFusionDualStreamDataset(df, TRAIN_CACHE)
#     val_set   = NeuroFusionDualStreamDataset(df, VAL_CACHE)
#
#     print(f" Train samples: {len(train_set)}")
#     print(f" Val samples  : {len(val_set)}")
#
#     # ---------------- CLASS IMBALANCE FIX ----------------
#     label_map = {
#         "Seizure": 0,
#         "GPD": 1,
#         "LRDA": 2,
#         "Other": 3,
#         "GRDA": 4,
#         "LPD": 5
#     }
#
#     labels = df["expert_consensus"].map(label_map).values
#     class_counts = Counter(labels)
#     total_samples = sum(class_counts.values())
#
#     class_weights = []
#     for i in range(NUM_CLASSES):
#         class_weights.append(total_samples / (NUM_CLASSES * class_counts[i]))
#
#     class_weights = torch.tensor(class_weights, dtype=torch.float32).to(device)
#     print(" Class weights:", class_weights)
#
#     # ---------------- DATALOADERS ----------------
#     train_loader = DataLoader(
#         train_set,
#         batch_size=BATCH_SIZE,
#         shuffle=True,
#         num_workers=4,
#         pin_memory=True,
#         persistent_workers=True,
#         prefetch_factor=2
#     )
#
#     val_loader = DataLoader(
#         val_set,
#         batch_size=BATCH_SIZE,
#         shuffle=False,
#         num_workers=4,
#         pin_memory=True,
#         persistent_workers=True
#     )
#
#     # ---------------- MODEL, LOSS, OPTIMIZER ----------------
#     model = NeuroFusionNet(num_classes=NUM_CLASSES).to(device)
#
#     if os.path.exists(MODEL_SAVE_PATH):
#         print(f" Found existing model checkpoint at {MODEL_SAVE_PATH}. Resuming training...")
#         model.load_state_dict(
#             torch.load(MODEL_SAVE_PATH, map_location=device, weights_only=True)
#         )
#     else:
#         print(" No previous checkpoint found. Starting fresh training.")
#
#     #  UPDATED LOSS FUNCTION (CLASS-WEIGHTED)
#     criterion = nn.CrossEntropyLoss(weight=class_weights)
#
#     optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
#     scaler = torch.amp.GradScaler(device.type)
#
#     # -------------------------------------------------
#     # 🔹 LEARNING RATE SCHEDULER (ReduceLROnPlateau)
#     # -------------------------------------------------
#     scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
#         optimizer,
#         mode="max",  # we monitor validation accuracy
#         factor=0.5,  # reduce LR by half
#         patience=5,  # wait 5 epochs before reducing
#         verbose=True
#     )
#
#     best_val_acc = 0.0
#     # -------------------------------------------------
#     #  EARLY STOPPING CONFIG
#     # -------------------------------------------------
#     early_stop_patience = 8
#     epochs_no_improve = 0
#
#     # ---------------- TRAIN LOOP ----------------
#     def train_epoch():
#         model.train()
#         running_loss, correct, total = 0, 0, 0
#         pbar = tqdm(train_loader, desc=" Training", leave=False)
#         optimizer.zero_grad()
#
#         for step, (waveform, spectrogram, labels) in enumerate(pbar, start=1):
#             waveform = waveform.to(device, non_blocking=True)
#             spectrogram = spectrogram.to(device, non_blocking=True)
#             labels = labels.to(device, non_blocking=True)
#
#             with torch.autocast(device_type=device.type):
#                 outputs = model(waveform, spectrogram)
#                 loss = criterion(outputs, labels) / ACCUM_STEPS
#
#             if not torch.isfinite(loss):
#                 print(" NaN loss detected — skipping batch.")
#                 continue
#
#             scaler.scale(loss).backward()
#
#             if step % ACCUM_STEPS == 0:
#                 scaler.unscale_(optimizer)
#                 torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
#                 scaler.step(optimizer)
#                 scaler.update()
#                 optimizer.zero_grad()
#
#             running_loss += loss.item() * labels.size(0) * ACCUM_STEPS
#             _, preds = torch.max(outputs, 1)
#             correct += (preds == labels).sum().item()
#             total += labels.size(0)
#
#             pbar.set_postfix(loss=float(loss.item() * ACCUM_STEPS))
#
#         return running_loss / total, correct / total
#
#     # ---------------- VALIDATION LOOP ----------------
#     def evaluate_epoch():
#         model.eval()
#         running_loss, correct, total = 0, 0, 0
#
#         with torch.no_grad():
#             for waveform, spectrogram, labels in tqdm(val_loader, desc=" Validation", leave=False):
#                 waveform = waveform.to(device, non_blocking=True)
#                 spectrogram = spectrogram.to(device, non_blocking=True)
#                 labels = labels.to(device, non_blocking=True)
#
#                 with torch.autocast(device_type=device.type):
#                     outputs = model(waveform, spectrogram)
#                     loss = criterion(outputs, labels)
#                     # Temporal consistency loss (light)
#                     if outputs.size(0) > 1:
#                         temporal_loss = torch.mean(
#                             (outputs[1:] - outputs[:-1]) ** 2
#                         )
#                         loss = loss + 0.01 * temporal_loss
#
#                         # Gradient accumulation
#                     loss = loss / ACCUM_STEPS
#
#
#                 running_loss += loss.item() * labels.size(0)
#                 _, preds = torch.max(outputs, 1)
#                 correct += (preds == labels).sum().item()
#                 total += labels.size(0)
#
#         return running_loss / total, correct / total
#
#     # ---------------- MAIN TRAINING ----------------
#     print(" Starting fast training process...")
#
#     for epoch in range(1, EPOCHS + 1):
#         train_loss, train_acc = train_epoch()
#         val_loss, val_acc = evaluate_epoch()
#
#         # Update learning rate based on validation accuracy
#         scheduler.step(val_acc)
#
#         print(
#             f" Epoch [{epoch}/{EPOCHS}] "
#             f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f} | "
#             f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}"
#         )
#
#         if val_acc > best_val_acc and torch.isfinite(torch.tensor(val_loss)):
#             best_val_acc = val_acc
#             epochs_no_improve = 0
#
#             torch.save(model.state_dict(), MODEL_SAVE_PATH)
#             print(f" Saved best model at epoch {epoch} with acc {val_acc:.4f}")
#
#         else:
#             epochs_no_improve += 1
#
#         # -------------------------------------------------
#         #  EARLY STOPPING CHECK
#         # -------------------------------------------------
#         if epochs_no_improve >= early_stop_patience:
#             print(" Early stopping triggered")
#             break
#
#     print(" Training complete. Best Validation Accuracy:", best_val_acc)
#
#
# #  Windows-safe entry point
# if __name__ == "__main__":
#     torch.multiprocessing.freeze_support()
#     main()

# import os
# import torch
# import torch.nn as nn
# import torch.optim as optim
# import pandas as pd
# from tqdm import tqdm
# from torch.utils.data import DataLoader
# from collections import Counter
#
# from src.models.neurofusion_model import NeuroFusionNet
# from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset
#
#
# # ======================================================
# # MAIN
# # ======================================================
# def main():
#
#     # ---------------- SYSTEM ----------------
#     torch.backends.cudnn.benchmark = True
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     print(f"🚀 Using device: {device}")
#
#     # ---------------- PATHS ----------------
#     PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
#
#     TRAIN_CACHE = os.path.join(PROJECT_ROOT, "Dataset", "splits", "train")
#     VAL_CACHE   = os.path.join(PROJECT_ROOT, "Dataset", "splits", "val")
#     CSV_PATH    = os.path.join(PROJECT_ROOT, "Dataset", "train.csv")
#
#     # 🔥 Proper full checkpoint (new)
#     FULL_CKPT_PATH = os.path.join(PROJECT_ROOT, "checkpoints", "neurofusion_fast_resume.pt")
#
#     # 🔥 Your 59% trained model
#     BEST_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "neurofusion_best_fast.pt")
#
#     os.makedirs(os.path.dirname(FULL_CKPT_PATH), exist_ok=True)
#
#     # ---------------- HYPERPARAMS ----------------
#     NUM_CLASSES = 6
#     BATCH_SIZE = 32
#     ACCUM_STEPS = 2
#     EPOCHS = 50
#     LR = 3e-4
#     WEIGHT_DECAY = 1e-4
#
#     # ---------------- DATA ----------------
#     print("📦 Loading dataset...")
#     df = pd.read_csv(CSV_PATH)
#
#     train_set = NeuroFusionDualStreamDataset(df, TRAIN_CACHE, train=True)
#     val_set   = NeuroFusionDualStreamDataset(df, VAL_CACHE, train=False)
#
#     print(f"Train samples: {len(train_set)}")
#     print(f"Val samples  : {len(val_set)}")
#
#     # ---------------- CLASS WEIGHTS ----------------
#     label_map = {
#         "Seizure": 0,
#         "GPD": 1,
#         "LRDA": 2,
#         "Other": 3,
#         "GRDA": 4,
#         "LPD": 5
#     }
#
#     labels = df["expert_consensus"].map(label_map).values
#     counts = Counter(labels)
#     total = sum(counts.values())
#
#     class_weights = torch.tensor(
#         [total / (NUM_CLASSES * counts[i]) for i in range(NUM_CLASSES)],
#         dtype=torch.float32,
#         device=device
#     )
#
#     print("⚖️ Class weights:", class_weights)
#
#     # ---------------- DATALOADERS ----------------
#     train_loader = DataLoader(
#         train_set,
#         batch_size=BATCH_SIZE,
#         shuffle=True,
#         num_workers=2,
#         pin_memory=True,
#         persistent_workers=True,
#         prefetch_factor=4
#     )
#
#     val_loader = DataLoader(
#         val_set,
#         batch_size=BATCH_SIZE,
#         shuffle=False,
#         num_workers=1,
#         pin_memory=True,
#         persistent_workers=True
#     )
#
#     # ---------------- MODEL ----------------
#     model = NeuroFusionNet(num_classes=NUM_CLASSES).to(device)
#
#     criterion = nn.CrossEntropyLoss(weight=class_weights)
#     optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
#     scaler = torch.amp.GradScaler("cuda")
#
#     scheduler = optim.lr_scheduler.ReduceLROnPlateau(
#         optimizer,
#         mode="max",
#         factor=0.3,
#         patience=3,
#         min_lr=1e-6
#     )
#
#     # ======================================================
#     # CHECKPOINT LOGIC
#     # ======================================================
#     start_epoch = 1
#     best_val_acc = 0.0
#
#     # 1️⃣ Resume full checkpoint (preferred)
#     if os.path.exists(FULL_CKPT_PATH):
#
#         print(f"🔁 Resuming full training checkpoint: {FULL_CKPT_PATH}")
#         ckpt = torch.load(FULL_CKPT_PATH, map_location=device)
#
#         model.load_state_dict(ckpt["model"])
#         optimizer.load_state_dict(ckpt["optimizer"])
#         scaler.load_state_dict(ckpt["scaler"])
#
#         best_val_acc = ckpt["best_acc"]
#         start_epoch = ckpt["epoch"] + 1
#
#         print(f"✅ Resumed from epoch {start_epoch-1}, best acc {best_val_acc:.4f}")
#
#     # 2️⃣ Else load your previously trained 59% model
#     elif os.path.exists(BEST_MODEL_PATH):
#
#         print(f"🔄 Loading best saved model: {BEST_MODEL_PATH}")
#         model.load_state_dict(torch.load(BEST_MODEL_PATH, map_location=device))
#
#         start_epoch = 21        # since you trained 20 epochs
#         best_val_acc = 0.5999   # your known val accuracy
#
#         print(f"✅ Loaded pretrained weights. Starting from epoch {start_epoch}")
#
#     else:
#         print("🆕 No checkpoint found. Starting fresh training.")
#
#     # ======================================================
#     # TRAIN ONE EPOCH
#     # ======================================================
#     def train_epoch():
#         model.train()
#         total_loss, correct, total = 0.0, 0, 0
#         optimizer.zero_grad()
#
#         for step, (wave, spec, labels) in enumerate(
#             tqdm(train_loader, desc="🟢 Train", leave=False), start=1
#         ):
#             wave = wave.to(device, non_blocking=True)
#             spec = spec.to(device, non_blocking=True)
#             labels = labels.to(device, non_blocking=True)
#
#             with torch.amp.autocast("cuda"):
#                 outputs = model(wave, spec)
#                 loss = criterion(outputs, labels)
#
#                 # Temporal consistency regularization
#                 if outputs.size(0) > 1:
#                     loss = loss + 0.01 * torch.mean(
#                         (outputs[1:] - outputs[:-1]) ** 2
#                     )
#
#                 loss = loss / ACCUM_STEPS
#
#             scaler.scale(loss).backward()
#
#             if step % ACCUM_STEPS == 0:
#                 scaler.unscale_(optimizer)
#                 torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
#                 scaler.step(optimizer)
#                 scaler.update()
#                 optimizer.zero_grad()
#
#             total_loss += loss.item() * labels.size(0) * ACCUM_STEPS
#             preds = outputs.argmax(1)
#             correct += (preds == labels).sum().item()
#             total += labels.size(0)
#
#         return total_loss / total, correct / total
#
#     # ======================================================
#     # VALIDATION
#     # ======================================================
#     def validate():
#         model.eval()
#         total_loss, correct, total = 0.0, 0, 0
#
#         with torch.no_grad():
#             for wave, spec, labels in tqdm(val_loader, desc="🔵 Val", leave=False):
#                 wave = wave.to(device, non_blocking=True)
#                 spec = spec.to(device, non_blocking=True)
#                 labels = labels.to(device, non_blocking=True)
#
#                 with torch.amp.autocast("cuda"):
#                     outputs = model(wave, spec)
#                     loss = criterion(outputs, labels)
#
#                 total_loss += loss.item() * labels.size(0)
#                 preds = outputs.argmax(1)
#                 correct += (preds == labels).sum().item()
#                 total += labels.size(0)
#
#         return total_loss / total, correct / total
#
#     # ======================================================
#     # TRAIN LOOP
#     # ======================================================
#     print("🔥 Starting training...")
#
#     for epoch in range(start_epoch, EPOCHS + 1):
#
#         train_loss, train_acc = train_epoch()
#         val_loss, val_acc = validate()
#
#         scheduler.step(val_acc)
#
#         print(
#             f"Epoch [{epoch}/{EPOCHS}] | "
#             f"Train: {train_loss:.4f}, Acc {train_acc:.4f} | "
#             f"Val: {val_loss:.4f}, Acc {val_acc:.4f}"
#         )
#
#         if val_acc > best_val_acc:
#             best_val_acc = val_acc
#
#             torch.save({
#                 "epoch": epoch,
#                 "model": model.state_dict(),
#                 "optimizer": optimizer.state_dict(),
#                 "scaler": scaler.state_dict(),
#                 "best_acc": best_val_acc
#             }, FULL_CKPT_PATH)
#
#             print(f"💾 Saved new best checkpoint (acc={best_val_acc:.4f})")
#
#     print("✅ Training complete. Best Val Acc:", best_val_acc)


# ======================================================
# ENTRY
# ======================================================
# if __name__ == "__main__":
#     torch.multiprocessing.freeze_support()
#     main()

import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from tqdm import tqdm
from torch.utils.data import DataLoader
from collections import Counter

from src.models.neurofusion_model import NeuroFusionNet
from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset


# ======================================================
# MAIN
# ======================================================
def main():

    # ---------------- SYSTEM ----------------
    torch.backends.cudnn.benchmark = True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Using device: {device}")

    # ---------------- PATHS ----------------
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

    TRAIN_CACHE = os.path.join(PROJECT_ROOT, "Dataset", "splits", "train")
    VAL_CACHE   = os.path.join(PROJECT_ROOT, "Dataset", "splits", "val")
    CSV_PATH    = os.path.join(PROJECT_ROOT, "Dataset", "train.csv")

    FULL_CKPT_PATH = os.path.join(
        PROJECT_ROOT, "checkpoints", "neurofusion_fast_resume.pt"
    )

    os.makedirs(os.path.dirname(FULL_CKPT_PATH), exist_ok=True)

    # ---------------- HYPERPARAMS ----------------
    NUM_CLASSES = 6
    BATCH_SIZE = 32
    ACCUM_STEPS = 2
    EPOCHS = 50
    LR = 3e-4
    WEIGHT_DECAY = 1e-4

    # ---------------- DATA ----------------
    print("📦 Loading dataset...")
    df = pd.read_csv(CSV_PATH)

    train_set = NeuroFusionDualStreamDataset(df, TRAIN_CACHE, train=True)
    val_set   = NeuroFusionDualStreamDataset(df, VAL_CACHE, train=False)

    print(f"Train samples: {len(train_set)}")
    print(f"Val samples  : {len(val_set)}")

    # ---------------- CLASS WEIGHTS ----------------
    label_map = {
        "Seizure": 0,
        "GPD": 1,
        "LRDA": 2,
        "Other": 3,
        "GRDA": 4,
        "LPD": 5
    }

    labels = df["expert_consensus"].map(label_map).values
    counts = Counter(labels)
    total = sum(counts.values())

    class_weights = torch.tensor(
        [total / (NUM_CLASSES * counts[i]) for i in range(NUM_CLASSES)],
        dtype=torch.float32,
        device=device
    )

    print("⚖️ Class weights:", class_weights)

    # ---------------- DATALOADERS ----------------
    train_loader = DataLoader(
        train_set,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=2,
        pin_memory=True,
        persistent_workers=True,
        prefetch_factor=4
    )

    val_loader = DataLoader(
        val_set,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=1,
        pin_memory=True,
        persistent_workers=True
    )

    # ---------------- MODEL ----------------
    model = NeuroFusionNet(num_classes=NUM_CLASSES).to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scaler = torch.amp.GradScaler("cuda")

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.3,
        patience=3,
        min_lr=1e-6
    )

    # ======================================================
    # CHECKPOINT RESUME (SAFE + AUTOMATIC)
    # ======================================================
    start_epoch = 1
    best_val_acc = 0.0

    if os.path.exists(FULL_CKPT_PATH):

        print(f"🔁 Resuming from checkpoint: {FULL_CKPT_PATH}")
        ckpt = torch.load(FULL_CKPT_PATH, map_location=device)

        model.load_state_dict(ckpt["model"])

        # Safe optimizer restore
        if ckpt.get("optimizer") is not None:
            optimizer.load_state_dict(ckpt["optimizer"])
            print("✅ Optimizer state restored")
        else:
            print("⚠️ Optimizer state missing — starting fresh optimizer")

        # Safe scaler restore
        if ckpt.get("scaler") is not None:
            scaler.load_state_dict(ckpt["scaler"])
            print("✅ AMP scaler restored")
        else:
            print("⚠️ Scaler state missing — starting fresh scaler")

        best_val_acc = ckpt["best_acc"]
        start_epoch = ckpt["epoch"] + 1

        print(f"📌 Resumed from epoch {start_epoch-1}")
        print(f"🏆 Best validation accuracy so far: {best_val_acc:.4f}")

    else:
        print("🆕 No checkpoint found. Starting fresh training.")

    # ======================================================
    # TRAIN ONE EPOCH
    # ======================================================
    def train_epoch():
        model.train()
        total_loss, correct, total = 0.0, 0, 0
        optimizer.zero_grad()

        for step, (wave, spec, labels) in enumerate(
            tqdm(train_loader, desc="🟢 Train", leave=False), start=1
        ):
            wave = wave.to(device, non_blocking=True)
            spec = spec.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            with torch.amp.autocast("cuda"):
                outputs = model(wave, spec)
                loss = criterion(outputs, labels)

                # Optional temporal consistency regularization
                if outputs.size(0) > 1:
                    loss = loss + 0.01 * torch.mean(
                        (outputs[1:] - outputs[:-1]) ** 2
                    )

                loss = loss / ACCUM_STEPS

            scaler.scale(loss).backward()

            if step % ACCUM_STEPS == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()

            total_loss += loss.item() * labels.size(0) * ACCUM_STEPS
            preds = outputs.argmax(1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        return total_loss / total, correct / total

    # ======================================================
    # VALIDATION
    # ======================================================
    def validate():
        model.eval()
        total_loss, correct, total = 0.0, 0, 0

        with torch.no_grad():
            for wave, spec, labels in tqdm(val_loader, desc="🔵 Val", leave=False):
                wave = wave.to(device, non_blocking=True)
                spec = spec.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)

                with torch.amp.autocast("cuda"):
                    outputs = model(wave, spec)
                    loss = criterion(outputs, labels)

                total_loss += loss.item() * labels.size(0)
                preds = outputs.argmax(1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        return total_loss / total, correct / total

    # ======================================================
    # TRAIN LOOP
    # ======================================================
    print("🔥 Starting training...")

    for epoch in range(start_epoch, EPOCHS + 1):

        train_loss, train_acc = train_epoch()
        val_loss, val_acc = validate()

        scheduler.step(val_acc)

        print(
            f"Epoch [{epoch}/{EPOCHS}] | "
            f"Train: {train_loss:.4f}, Acc {train_acc:.4f} | "
            f"Val: {val_loss:.4f}, Acc {val_acc:.4f}"
        )

        # Save best model checkpoint
        if val_acc > best_val_acc:
            best_val_acc = val_acc

            torch.save({
                "epoch": epoch,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scaler": scaler.state_dict(),
                "best_acc": best_val_acc
            }, FULL_CKPT_PATH)

            print(f"💾 Saved new best checkpoint (acc={best_val_acc:.4f})")

    print("✅ Training complete.")
    print(f"🏆 Final Best Validation Accuracy: {best_val_acc:.4f}")


# ======================================================
# ENTRY
# ======================================================
if __name__ == "__main__":
    torch.multiprocessing.freeze_support()
    main()