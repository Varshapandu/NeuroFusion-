# federated/config.py
import torch
import os

# Project paths (edit to match your machine)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# -------------------------------
# SPLIT CSV PATHS (NEW)
# -------------------------------
TRAIN_CSV = os.path.join(ROOT_DIR, "Dataset", "train_split.csv")
VAL_CSV   = os.path.join(ROOT_DIR, "Dataset", "val_split.csv")
TEST_CSV  = os.path.join(ROOT_DIR, "Dataset", "test_split.csv")

CACHE_DIR = os.path.join(ROOT_DIR, "Dataset", "cache")


# Device / runtime
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model / data
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 32))
NUM_CLASSES = 6

# Optimizer
LR = float(os.environ.get("LR", 1e-3))  # ✅ Increased from 1e-4 to 1e-3

# Federated settings
NUM_ROUNDS = int(os.environ.get("NUM_ROUNDS", 30))  # ✅ Increased from 3 to 30 rounds
CLIENTS_PER_ROUND = int(os.environ.get("CLIENTS_PER_ROUND", 3))  # ✅ Changed to 3
TOTAL_CLIENTS = int(os.environ.get("TOTAL_CLIENTS", 3))           # ✅ Changed to 3

# FedProx + Update-level DP defaults (tunable)
FEDPROX_MU = float(os.environ.get("FEDPROX_MU", 1e-3))
UPDATE_CLIP_NORM = float(os.environ.get("UPDATE_CLIP_NORM", 1.0))
UPDATE_NOISE_MULTIPLIER = float(os.environ.get("UPDATE_NOISE_MULTIPLIER", 0.0))  # ✅ Disabled DP noise for initial training
LOCAL_EPOCHS = int(os.environ.get("LOCAL_EPOCHS", 5))  # ✅ Increased from 1 to 5
PERSONALIZATION_EPOCHS = int(os.environ.get("PERSONALIZATION_EPOCHS", 0))

# For legacy/compat: previous Opacus variables mapped if present
DP_NOISE = float(os.environ.get("DP_NOISE", UPDATE_NOISE_MULTIPLIER))
DP_MAX_GRAD_NORM = float(os.environ.get("DP_MAX_GRAD_NORM", UPDATE_CLIP_NORM))

# Accountant defaults
DELTA = float(os.environ.get("DP_DELTA", 1e-5))

# Flower server address default (change if needed)
FLOWER_SERVER_ADDRESS = os.environ.get("FLOWER_SERVER_ADDRESS", "127.0.0.1:8082")
