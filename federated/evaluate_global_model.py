# federated/evaluate_global_model.py
"""
Evaluate a global model checkpoint produced by the FL server.

Outputs:
 - evaluation_logs/round_X_metrics.json
 - evaluation_logs/round_X_confusion.png
 - evaluation_logs/round_X_confusion_normalized.png
"""

import os
import json
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    precision_recall_fscore_support
)

from torch.utils.data import DataLoader, random_split

# Project imports
from federated.config import CSV_PATH, CACHE_DIR, NUM_CLASSES, BATCH_SIZE, DEVICE
from src.models.neurofusion_model import NeuroFusionNet
from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset


# ----------------------
# Helper: Load Dataset
# ----------------------
def load_dataset():
    df = pd.read_csv(CSV_PATH)
    dataset = NeuroFusionDualStreamDataset(df, CACHE_DIR)

    # Split exactly like training
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    _, val_set = random_split(dataset, [train_size, test_size])

    return DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False)


# ----------------------
# Helper: Load Checkpoint
# ----------------------
def load_checkpoint(path):
    print(f"Loading checkpoint: {path}")
    ckpt = torch.load(path, map_location=DEVICE)

    # Flower saves params in a list (numpy arrays)
    params_list = ckpt["params"]
    return params_list, ckpt.get("round", None)


# ----------------------
# Convert Flower parameters -> state_dict
# ----------------------
def list_to_state_dict(param_list, template):
    keys = list(template.keys())
    assert len(keys) == len(param_list), "Checkpoint parameter mismatch!"

    new_state = {}
    for k, arr in zip(keys, param_list):
        new_state[k] = torch.tensor(arr, dtype=template[k].dtype)
    return new_state


# ----------------------
# Plot Confusion Matrix
# ----------------------
def plot_confusion(cm, labels, out_path, normalized=False):
    plt.figure(figsize=(10, 8))
    cmap = plt.cm.Blues
    plt.imshow(cm, interpolation="nearest", cmap=cmap)
    plt.title("Confusion Matrix" + (" (Normalized)" if normalized else ""))
    plt.colorbar()

    tick_marks = np.arange(len(labels))
    plt.xticks(tick_marks, labels, rotation=45)
    plt.yticks(tick_marks, labels)

    fmt = ".2f" if normalized else "d"
    thresh = cm.max() / 2.

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(
                j, i, format(cm[i, j], fmt),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black"
            )

    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"Saved confusion matrix → {out_path}")


# ----------------------
# EVALUATION
# ----------------------
def evaluate_checkpoint(ckpt_path):
    # Load dataset
    loader = load_dataset()

    # Build model
    model = NeuroFusionNet(num_classes=NUM_CLASSES).to(DEVICE)
    model.eval()

    # Load checkpoint parameters
    param_list, round_id = load_checkpoint(ckpt_path)
    template = model.state_dict()
    state_dict = list_to_state_dict(param_list, template)
    model.load_state_dict({k: v.to(DEVICE) for k, v in state_dict.items()})

    print(f"Evaluating model from round {round_id}...")

    # Metrics
    all_labels = []
    all_preds = []
    criterion = torch.nn.CrossEntropyLoss()
    total_loss = 0
    count = 0

    with torch.no_grad():
        for waveform, spectrogram, labels in loader:
            waveform = waveform.to(DEVICE)
            spectrogram = spectrogram.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(waveform, spectrogram)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * labels.size(0)
            count += labels.size(0)

            _, pred = torch.max(outputs, 1)
            all_labels.extend(labels.cpu().numpy())
            all_preds.extend(pred.cpu().numpy())

    avg_loss = total_loss / count
    acc = accuracy_score(all_labels, all_preds)

    # Multi-class metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average=None
    )
    class_report = classification_report(all_labels, all_preds, digits=4)

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

    # Save confusion matrix images
    labels = [str(i) for i in range(NUM_CLASSES)]
    os.makedirs("evaluation_logs", exist_ok=True)

    plot_confusion(cm, labels, f"evaluation_logs/round_{round_id}_confusion.png")
    plot_confusion(cm_norm, labels, f"evaluation_logs/round_{round_id}_confusion_normalized.png", normalized=True)

    # Save metrics JSON
    metrics = {
        "round": round_id,
        "accuracy": float(acc),
        "loss": float(avg_loss),
        "precision_per_class": precision.tolist(),
        "recall_per_class": recall.tolist(),
        "f1_per_class": f1.tolist(),
        "classification_report": class_report,
    }

    json_path = f"evaluation_logs/round_{round_id}_metrics.json"
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=4)

    print(f"Saved metrics → {json_path}")
    print("\n===== FINAL EVALUATION =====")
    print(f"Accuracy: {acc:.4f}")
    print(f"Loss: {avg_loss:.4f}")
    print(class_report)

    return metrics


# ----------------------
# MAIN
# ----------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate a global FL checkpoint.")
    parser.add_argument("--ckpt", required=True, help="Path to global_round_X.pt")
    args = parser.parse_args()

    evaluate_checkpoint(args.ckpt)
