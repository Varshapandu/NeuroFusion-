# import os
# import sys
# import numpy as np
# import torch
# import torch.nn.functional as F
# from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
# import pandas as pd
#
# # -------------------------------------------------
# # FIX PYTHON PATH (so `src` is visible)
# # -------------------------------------------------
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
# sys.path.insert(0, PROJECT_ROOT)
#
# # -------------------------------------------------
# # PATHS
# # -------------------------------------------------
# MODEL_PATH = r"models/neurofusion_best_fast.pt"
# CSV_PATH   = r"Dataset/test_split.csv"
# CACHE_DIR = r"Dataset/splits/test"
#
# # -------------------------------------------------
# # CONSTANTS (same as dataset)
# # -------------------------------------------------
# TARGET_T_WAVE = 1000
# TARGET_F_SPEC = 64
# TARGET_T_SPEC = 32
# TARGET_CHANNELS = 20
#
# LABEL_MAP = {
#     "Seizure": 0,
#     "GPD": 1,
#     "LRDA": 2,
#     "Other": 3,
#     "GRDA": 4,
#     "LPD": 5
# }
#
# # -------------------------------------------------
# # DEVICE
# # -------------------------------------------------
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(f" Using device: {device}")
#
# # -------------------------------------------------
# # MODEL
# # -------------------------------------------------
# from src.models.neurofusion_model import NeuroFusionNet
#
# model = NeuroFusionNet(num_classes=6)
# model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
# model.to(device)
# model.eval()
#
# print(" Model loaded successfully")
#
# # -------------------------------------------------
# # PREPROCESS HELPERS (same logic as dataset)
# # -------------------------------------------------
# def pad_channels(x, target):
#     if x.shape[0] > target:
#         return x[:target]
#     if x.shape[0] < target:
#         pad = torch.zeros(target - x.shape[0], *x.shape[1:])
#         return torch.cat([x, pad], dim=0)
#     return x
#
# def pad_waveform(x):
#     if x.shape[1] > TARGET_T_WAVE:
#         return x[:, :TARGET_T_WAVE]
#     if x.shape[1] < TARGET_T_WAVE:
#         return F.pad(x, (0, TARGET_T_WAVE - x.shape[1]))
#     return x
#
# def pad_spectrogram(x):
#     if x.shape[2] > TARGET_T_SPEC:
#         x = x[:, :, :TARGET_T_SPEC]
#     if x.shape[2] < TARGET_T_SPEC:
#         x = F.pad(x, (0, TARGET_T_SPEC - x.shape[2]))
#     if x.shape[1] > TARGET_F_SPEC:
#         x = x[:, :TARGET_F_SPEC, :]
#     if x.shape[1] < TARGET_F_SPEC:
#         x = F.pad(x, (0, 0, 0, TARGET_F_SPEC - x.shape[1]))
#     return x
#
# def normalize(wav, spec):
#     wav = (wav - wav.mean(dim=1, keepdim=True)) / (wav.std(dim=1, keepdim=True) + 1e-6)
#     spec = (spec - spec.mean()) / (spec.std() + 1e-6)
#     return wav, spec
#
# # -------------------------------------------------
# # MULTI-WINDOW VOTING
# # -------------------------------------------------
# def predict_with_window_voting(waveforms, specs):
#     logits = []
#
#     with torch.no_grad():
#         for i in range(waveforms.shape[0]):
#             wav = torch.tensor(waveforms[i], dtype=torch.float32)
#             spec = torch.tensor(specs[i], dtype=torch.float32)
#
#             # shape fixes
#             if wav.shape[0] != TARGET_CHANNELS:
#                 wav = wav.permute(1, 0)
#             if spec.shape[0] != TARGET_CHANNELS:
#                 spec = spec.permute(1, 0, 2)
#
#             wav = pad_channels(wav, TARGET_CHANNELS)
#             spec = pad_channels(spec, TARGET_CHANNELS)
#
#             wav = pad_waveform(wav)
#             spec = pad_spectrogram(spec)
#
#             wav, spec = normalize(wav, spec)
#
#             wav = wav.unsqueeze(0).to(device)
#             spec = spec.unsqueeze(0).to(device)
#
#             out = model(wav, spec)
#             logits.append(out.squeeze(0))
#
#     return torch.argmax(torch.mean(torch.stack(logits), dim=0)).item()
#
# # -------------------------------------------------
# # LOAD TEST CSV
# # -------------------------------------------------
# df = pd.read_csv(CSV_PATH)
# print(f" Dataset initialized with {len(df)} EEGs from cache.")
# print(f" Test samples: {len(df)}")
#
# # -------------------------------------------------
# # TESTING
# # -------------------------------------------------
# y_true, y_pred = [], []
#
# for _, row in df.iterrows():
#     eeg_id = str(row["eeg_id"])
#     label = LABEL_MAP[row["expert_consensus"]]
#
#     npz = np.load(os.path.join(CACHE_DIR, f"{eeg_id}.npz"))
#     waveforms = npz["waveform"]
#     specs = npz["spec"]
#
#     if waveforms.ndim == 2:
#         waveforms = waveforms[None, ...]
#     if specs.ndim == 3:
#         specs = specs[None, ...]
#
#     pred = predict_with_window_voting(waveforms, specs)
#
#     y_true.append(label)
#     y_pred.append(pred)
#
# # -------------------------------------------------
# # METRICS
# # -------------------------------------------------
# acc = accuracy_score(y_true, y_pred)
# prec = precision_score(y_true, y_pred, average="weighted")
# rec = recall_score(y_true, y_pred, average="weighted")
# f1 = f1_score(y_true, y_pred, average="weighted")
# cm = confusion_matrix(y_true, y_pred)
#
# print("\n========== MODEL TESTING RESULTS ==========")
# print(f"Accuracy  : {acc:.4f}")
# print(f"Precision : {prec:.4f}")
# print(f"Recall    : {rec:.4f}")
# print(f"F1 Score  : {f1:.4f}")
# print("\nConfusion Matrix:")
# print(cm)
#
# print("\n Multi-window NeuroFusion testing completed successfully")
#

# import os
# import sys
# import numpy as np
# import torch
# import torch.nn.functional as F
# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
#
# from sklearn.metrics import (
#     accuracy_score,
#     precision_score,
#     recall_score,
#     f1_score,
#     confusion_matrix,
#     roc_curve,
#     auc
# )
# from sklearn.preprocessing import label_binarize
#
# # -------------------------------------------------
# # FIX PYTHON PATH
# # -------------------------------------------------
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
# sys.path.insert(0, PROJECT_ROOT)
#
# # -------------------------------------------------
# # PATHS
# # -------------------------------------------------
# MODEL_PATH = r"models/neurofusion_best_fast.pt"
# CSV_PATH   = r"Dataset/test_split.csv"
# CACHE_DIR = r"Dataset/splits/test"
#
# # -------------------------------------------------
# # CONSTANTS
# # -------------------------------------------------
# TARGET_T_WAVE = 1000
# TARGET_F_SPEC = 64
# TARGET_T_SPEC = 32
# TARGET_CHANNELS = 20
#
# CLASS_NAMES = ["Seizure", "GPD", "LRDA", "Other", "GRDA", "LPD"]
#
# LABEL_MAP = {
#     "Seizure": 0,
#     "GPD": 1,
#     "LRDA": 2,
#     "Other": 3,
#     "GRDA": 4,
#     "LPD": 5
# }
#
# # -------------------------------------------------
# # DEVICE
# # -------------------------------------------------
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(f" Using device: {device}")
#
# # -------------------------------------------------
# # MODEL
# # -------------------------------------------------
# from src.models.neurofusion_model import NeuroFusionNet
#
# model = NeuroFusionNet(num_classes=6)
# model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
# model.to(device)
# model.eval()
#
# print(" Model loaded successfully")
#
# # -------------------------------------------------
# # PREPROCESS HELPERS (EXACT DATASET LOGIC)
# # -------------------------------------------------
# def pad_channels(x, target):
#     if x.shape[0] > target:
#         return x[:target]
#     if x.shape[0] < target:
#         pad = torch.zeros(target - x.shape[0], *x.shape[1:])
#         return torch.cat([x, pad], dim=0)
#     return x
#
# def pad_waveform(x):
#     if x.shape[1] > TARGET_T_WAVE:
#         return x[:, :TARGET_T_WAVE]
#     if x.shape[1] < TARGET_T_WAVE:
#         return F.pad(x, (0, TARGET_T_WAVE - x.shape[1]))
#     return x
#
# def pad_spectrogram(x):
#     if x.shape[2] > TARGET_T_SPEC:
#         x = x[:, :, :TARGET_T_SPEC]
#     if x.shape[2] < TARGET_T_SPEC:
#         x = F.pad(x, (0, TARGET_T_SPEC - x.shape[2]))
#     if x.shape[1] > TARGET_F_SPEC:
#         x = x[:, :TARGET_F_SPEC, :]
#     if x.shape[1] < TARGET_F_SPEC:
#         x = F.pad(x, (0, 0, 0, TARGET_F_SPEC - x.shape[1]))
#     return x
#
# def normalize(wav, spec):
#     wav = (wav - wav.mean(dim=1, keepdim=True)) / (wav.std(dim=1, keepdim=True) + 1e-6)
#     spec = (spec - spec.mean()) / (spec.std() + 1e-6)
#     return wav, spec
#
# # -------------------------------------------------
# #  MULTI-WINDOW LOGIT AVERAGING (HIGH ACCURACY)
# # -------------------------------------------------
# def predict_with_window_voting(waveforms, specs):
#     logits = []
#
#     with torch.no_grad():
#         for i in range(waveforms.shape[0]):
#             wav = torch.tensor(waveforms[i], dtype=torch.float32)
#             spec = torch.tensor(specs[i], dtype=torch.float32)
#
#             if wav.shape[0] != TARGET_CHANNELS:
#                 wav = wav.permute(1, 0)
#             if spec.shape[0] != TARGET_CHANNELS:
#                 spec = spec.permute(1, 0, 2)
#
#             wav = pad_channels(wav, TARGET_CHANNELS)
#             spec = pad_channels(spec, TARGET_CHANNELS)
#
#             wav = pad_waveform(wav)
#             spec = pad_spectrogram(spec)
#
#             wav, spec = normalize(wav, spec)
#
#             wav = wav.unsqueeze(0).to(device)
#             spec = spec.unsqueeze(0).to(device)
#
#             out = model(wav, spec)
#             logits.append(out.squeeze(0))
#
#     mean_logits = torch.mean(torch.stack(logits), dim=0)
#     probs = torch.softmax(mean_logits, dim=0)
#
#     return torch.argmax(probs).item(), probs.cpu().numpy()
#
# # -------------------------------------------------
# # LOAD TEST DATA
# # -------------------------------------------------
# df = pd.read_csv(CSV_PATH)
# print(f" Test samples: {len(df)}")
#
# y_true, y_pred, y_scores = [], [], []
#
# # -------------------------------------------------
# # TESTING LOOP
# # -------------------------------------------------
# for _, row in df.iterrows():
#     eeg_id = str(row["eeg_id"])
#     label = LABEL_MAP[row["expert_consensus"]]
#
#     npz = np.load(os.path.join(CACHE_DIR, f"{eeg_id}.npz"))
#     waveforms = npz["waveform"]
#     specs = npz["spec"]
#
#     if waveforms.ndim == 2:
#         waveforms = waveforms[None, ...]
#     if specs.ndim == 3:
#         specs = specs[None, ...]
#
#     pred, probs = predict_with_window_voting(waveforms, specs)
#
#     y_true.append(label)
#     y_pred.append(pred)
#     y_scores.append(probs)
#
# y_scores = np.vstack(y_scores)
#
# # -------------------------------------------------
# # GLOBAL METRICS
# # -------------------------------------------------
# acc  = accuracy_score(y_true, y_pred)
# prec = precision_score(y_true, y_pred, average="weighted")
# rec  = recall_score(y_true, y_pred, average="weighted")
# f1   = f1_score(y_true, y_pred, average="weighted")
#
# print("\n========== MODEL TESTING RESULTS ==========")
# print(f"Accuracy  : {acc:.4f}")
# print(f"Precision : {prec:.4f}")
# print(f"Recall    : {rec:.4f}")
# print(f"F1 Score  : {f1:.4f}")
#
# # -------------------------------------------------
# # CONFUSION MATRIX
# # -------------------------------------------------
# cm = confusion_matrix(y_true, y_pred)
#
# plt.figure(figsize=(7, 6))
# sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
#             xticklabels=CLASS_NAMES,
#             yticklabels=CLASS_NAMES)
# plt.xlabel("Predicted Labels")
# plt.ylabel("True Labels")
# plt.title("Confusion Matrix")
# plt.tight_layout()
# plt.show()
#
# # -------------------------------------------------
# # ROC CURVES (MULTI-CLASS)
# # -------------------------------------------------
# y_true_bin = label_binarize(y_true, classes=list(range(6)))
#
# plt.figure(figsize=(7, 6))
# for i, cls in enumerate(CLASS_NAMES):
#     fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_scores[:, i])
#     roc_auc = auc(fpr, tpr)
#     plt.plot(fpr, tpr, lw=2, label=f"{cls} (AUC={roc_auc:.2f})")
#
# plt.plot([0, 1], [0, 1], "k--")
# plt.xlabel("False Positive Rate")
# plt.ylabel("True Positive Rate")
# plt.title("ROC Curve (Multi-class)")
# plt.legend(loc="lower right")
# plt.tight_layout()
# plt.show()
#
# print("\n Multi-window NeuroFusion evaluation completed successfully")

import os
import sys
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from torch.utils.data import DataLoader
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_curve,
    auc
)
from sklearn.preprocessing import label_binarize

# -------------------------------------------------
# FIX PYTHON PATH
# -------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# IMPORT MODEL & DATASET
# -------------------------------------------------
from src.models.neurofusion_model import NeuroFusionNet
from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset

# -------------------------------------------------
# PATHS (UPDATED)
# -------------------------------------------------
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "neurofusion_best_fast.pt")
CSV_PATH   = os.path.join(PROJECT_ROOT, "Dataset", "test_split.csv")
CACHE_DIR  = os.path.join(PROJECT_ROOT, "Dataset", "splits", "test")

# -------------------------------------------------
# CONSTANTS
# -------------------------------------------------
NUM_CLASSES = 6
CLASS_NAMES = ["Seizure", "GPD", "LRDA", "Other", "GRDA", "LPD"]

# -------------------------------------------------
# DEVICE
# -------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using device: {device}")

# -------------------------------------------------
# LOAD MODEL
# -------------------------------------------------
model = NeuroFusionNet(num_classes=NUM_CLASSES)
model.load_state_dict(
    torch.load(MODEL_PATH, map_location=device, weights_only=True)
)
model.to(device)
model.eval()

print("✅ Model loaded successfully")

# -------------------------------------------------
# LOAD TEST DATASET (SAME AS TRAINING LOGIC)
# -------------------------------------------------
df = pd.read_csv(CSV_PATH)
test_dataset = NeuroFusionDualStreamDataset(df, CACHE_DIR)

test_loader = DataLoader(
    test_dataset,
    batch_size=32,
    shuffle=False,
    num_workers=0,
    pin_memory=True
)

print(f"📊 Test samples: {len(test_dataset)}")

# -------------------------------------------------
# EVALUATION LOOP
# -------------------------------------------------
y_true = []
y_pred = []
y_scores = []

with torch.no_grad():
    for waveforms, spectrograms, labels in test_loader:

        waveforms = waveforms.to(device)
        spectrograms = spectrograms.to(device)
        labels = labels.to(device)

        outputs = model(waveforms, spectrograms)
        probs = torch.softmax(outputs, dim=1)

        preds = torch.argmax(probs, dim=1)

        y_true.extend(labels.cpu().numpy())
        y_pred.extend(preds.cpu().numpy())
        y_scores.extend(probs.cpu().numpy())

y_scores = np.array(y_scores)

# -------------------------------------------------
# METRICS
# -------------------------------------------------
acc  = accuracy_score(y_true, y_pred)
prec = precision_score(y_true, y_pred, average="weighted")
rec  = recall_score(y_true, y_pred, average="weighted")
f1   = f1_score(y_true, y_pred, average="weighted")

print("\n========== FINAL TEST RESULTS ==========")
print(f"Accuracy  : {acc:.4f}")
print(f"Precision : {prec:.4f}")
print(f"Recall    : {rec:.4f}")
print(f"F1 Score  : {f1:.4f}")

# -------------------------------------------------
# CONFUSION MATRIX
# -------------------------------------------------
cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(7, 6))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=CLASS_NAMES,
    yticklabels=CLASS_NAMES
)
plt.xlabel("Predicted Labels")
plt.ylabel("True Labels")
plt.title("Confusion Matrix")
plt.tight_layout()
plt.show()

# -------------------------------------------------
# ROC CURVES (MULTI-CLASS)
# -------------------------------------------------
y_true_bin = label_binarize(y_true, classes=list(range(NUM_CLASSES)))

plt.figure(figsize=(7, 6))

for i, cls in enumerate(CLASS_NAMES):
    fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_scores[:, i])
    roc_auc = auc(fpr, tpr)
    plt.plot(fpr, tpr, lw=2, label=f"{cls} (AUC={roc_auc:.2f})")

plt.plot([0, 1], [0, 1], "k--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve (Multi-class)")
plt.legend(loc="lower right")
plt.tight_layout()
plt.show()

print("\n✅ Final NeuroFusion evaluation completed successfully.")
