# federated/supernode_client.py
"""
Federated client (Flower NumPyClient) implementing:
 - FedProx local training (proximal term w.r.t global weights)
 - Update-level Differential Privacy (clip update, add Gaussian noise to update)
 - Optional local personalization (fine-tune locally; NOT sent to server)
 - Lightweight metrics reporting: preclip_update_norm, clip, sigma (and per-round eps if accountant present)
"""

import sys
import os
import math
import logging
from typing import Tuple, List, Dict, Any
from federated.config import TRAIN_CSV, VAL_CSV, CACHE_DIR

# Fix Python path (project root)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
print("ROOT_DIR = ", ROOT_DIR)

# Standard libs
import numpy as np
import pandas as pd
from tqdm import tqdm

# PyTorch & Flower
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import flwr as fl

# Project-specific imports (adjusted to your project layout)
from src.models.neurofusion_model import NeuroFusionNet
from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset

# Config
from federated.config import *
# def heartbeat_loop():
#     import socket, time, requests
#
#     node_id = socket.gethostname()
#
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(("8.8.8.8", 80))
#         ip = s.getsockname()[0]
#         s.close()
#     except Exception:
#         ip = "127.0.0.1"
#
#     while True:
#         try:
#             requests.post(
#                 "http://127.0.0.1:5000/api/fl/node_heartbeat",
#                 json={
#                     "node_id": node_id,
#                     "ip": ip,
#                     "status": "idle"
#                 },
#                 timeout=2
#             )
#         except Exception as e:
#             print("Heartbeat error:", e)
#
#         time.sleep(5)



# Optional accountant (if present) to compute eps -> per-round epsilon reporting
try:
    from federated.accountant import compute_eps_from_sigma
    _HAS_ACCOUNTANT = True
except Exception:
    _HAS_ACCOUNTANT = False



# Logging
logger = logging.getLogger("supernode_client")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(handler)

# ---------------------------
# Readable config defaults
# ---------------------------
DEVICE = globals().get("DEVICE", torch.device("cuda" if torch.cuda.is_available() else "cpu"))
BATCH_SIZE = globals().get("BATCH_SIZE", 32)
CSV_PATH = globals().get("CSV_PATH", os.path.join(ROOT_DIR, "converted_file.csv"))
CACHE_DIR = globals().get("CACHE_DIR", os.path.join(ROOT_DIR, "cache"))
NUM_CLASSES = globals().get("NUM_CLASSES", 2)
LR = globals().get("LR", 1e-4)

# FedProx + update-DP hyperparams (can be set in federated.config or env)
FEDPROX_MU = globals().get("FEDPROX_MU", 1e-3)
UPDATE_CLIP_NORM = globals().get("UPDATE_CLIP_NORM", 1.0)
UPDATE_NOISE_MULTIPLIER = globals().get("UPDATE_NOISE_MULTIPLIER", 0.5)
LOCAL_EPOCHS = globals().get("LOCAL_EPOCHS", 1)
PERSONALIZATION_EPOCHS = globals().get("PERSONALIZATION_EPOCHS", 0)

logger.info(
    f"Client config -> device={DEVICE} batch={BATCH_SIZE} lr={LR} "
    f"mu={FEDPROX_MU} clip={UPDATE_CLIP_NORM} sigma={UPDATE_NOISE_MULTIPLIER} "
    f"local_epochs={LOCAL_EPOCHS} personalization={PERSONALIZATION_EPOCHS}"
)

# ---------------------------
# Data loading
# ---------------------------
def load_data():
    from federated.config import TRAIN_CSV, VAL_CSV, CACHE_DIR

    train_df = pd.read_csv(TRAIN_CSV)
    val_df   = pd.read_csv(VAL_CSV)

    train_dataset = NeuroFusionDualStreamDataset(
        csv_df=train_df,
        cache_dir=CACHE_DIR
    )

    val_dataset = NeuroFusionDualStreamDataset(
        csv_df=val_df,
        cache_dir=CACHE_DIR
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        drop_last=False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    logger.info(
        f"Train samples={len(train_dataset)}, Val samples={len(val_dataset)}"
    )

    return train_loader, val_loader




# ---------------------------
# Param converters (state_dict <-> list)
# ---------------------------
def _state_dict_to_list(state_dict: Dict[str, torch.Tensor]) -> List[np.ndarray]:
    return [v.detach().cpu().numpy() for v in state_dict.values()]

def _list_to_state_dict(params_list: List[np.ndarray], template_state: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    keys = list(template_state.keys())
    assert len(keys) == len(params_list), f"Parameter count mismatch: {len(keys)} vs {len(params_list)}"
    new_state = {}
    for k, arr in zip(keys, params_list):
        # preserve dtype of template
        new_state[k] = torch.tensor(arr, dtype=template_state[k].dtype)
    return new_state

# ---------------------------
# Local train with FedProx
# ---------------------------
def _local_train_fedprox(
    model,
    loader,
    optimizer,
    criterion,
    global_state_tensors,
    mu,
    device,
    local_epochs,
):
    model.train()

    for epoch in range(local_epochs):
        for batch_idx, batch in enumerate(tqdm(loader, desc="Local Training", leave=False)):

            # ---------------- UI progress update ----------------
            if batch_idx % 10 == 0:
                try:
                    from backend.routes.fl_routes import update_training_progress
                    update_training_progress(batch_idx, len(loader))
                except Exception:
                    pass

            # ---------------- Unpack batch ----------------
            waveform, spectrogram, labels = (
                batch[0].to(device),
                batch[1].to(device),
                batch[2].to(device),
            )

            # ---------------- Forward ----------------
            optimizer.zero_grad()
            outputs = model(waveform, spectrogram)
            loss = criterion(outputs, labels)

            # ---------------- FedProx term ----------------
            if mu and mu > 0.0:
                prox = 0.0
                for name, param in model.named_parameters():
                    gw = global_state_tensors[name]
                    prox += torch.sum((param - gw) ** 2)
                loss += (mu / 2.0) * prox

            # ---------------- Backward ----------------
            loss.backward()
            optimizer.step()


# ---------------------------
# Privatize update: clip + noise
# ---------------------------
def _privatize_update(
    initial_state: Dict[str, torch.Tensor],
    local_state: Dict[str, torch.Tensor],
    clip_norm: float,
    sigma: float,
    device: torch.device,
) -> Tuple[Dict[str, torch.Tensor], float]:
    """Compute delta = local - initial; clip by L2; add Gaussian noise; return privatized_state and preclip norm."""
    deltas = {}
    sq_norm = 0.0
    for k in initial_state.keys():
        delta = (local_state[k].detach().to(device) - initial_state[k].to(device)).detach()
        deltas[k] = delta
        sq_norm += float(torch.sum(delta ** 2).item())

    preclip_norm = math.sqrt(sq_norm)
    logger.info(f"raw update L2 norm = {preclip_norm:.6f}")

    # Clip
    if preclip_norm > 0 and preclip_norm > clip_norm:
        scale = clip_norm / (preclip_norm + 1e-12)
        for k in deltas:
            deltas[k] = deltas[k] * scale
        logger.info(f"clipped update by scale {scale:.6f}")
        preclip_norm = clip_norm

    # Add Gaussian noise
    noise_std = sigma * clip_norm
    if sigma > 0.0:
        for k in deltas:
            noise = torch.randn_like(deltas[k], device=device) * noise_std
            deltas[k] = deltas[k] + noise
        logger.info(f"added Gaussian noise std={noise_std:.6f} to update")

    # Assemble privatized state: initial + noisy_delta
    privatized = {}
    with torch.no_grad():
        for k in initial_state.keys():
            privatized[k] = (initial_state[k].to(device) + deltas[k]).cpu()

    return privatized, float(preclip_norm)

# ---------------------------
# Evaluation helper (same as before)
# ---------------------------
def _evaluate_local(model: nn.Module, loader: DataLoader, criterion: nn.Module) -> Tuple[float, float]:
    model.eval()
    total, correct, loss_sum = 0, 0, 0.0
    with torch.no_grad():
        for batch in loader:
            waveform, spectrogram, labels = batch[0].to(DEVICE), batch[1].to(DEVICE), batch[2].to(DEVICE)
            outputs = model(waveform, spectrogram)
            loss = criterion(outputs, labels)
            loss_sum += float(loss.item()) * labels.size(0)
            _, pred = torch.max(outputs, 1)
            correct += (pred == labels).sum().item()
            total += labels.size(0)
    avg_loss = loss_sum / total if total > 0 else float("nan")
    acc = correct / total if total > 0 else float("nan")
    return avg_loss, acc

# ---------------------------
# Flower Client
# ---------------------------
class FlowerClient(fl.client.NumPyClient):
    def __init__(self):
        self.model = NeuroFusionNet(num_classes=NUM_CLASSES).to(DEVICE)
        self.trainloader, self.valloader = load_data()
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.AdamW(self.model.parameters(), lr=LR)

        # FedProx/DP params
        self.mu = FEDPROX_MU
        self.clip = UPDATE_CLIP_NORM
        self.sigma = UPDATE_NOISE_MULTIPLIER
        self.local_epochs = LOCAL_EPOCHS
        self.personalization_epochs = PERSONALIZATION_EPOCHS

        logger.info("Flower client initialized.")

    # Flower supports different signatures; accept optional config
    def get_parameters(self, config: Dict[str, Any] = None) -> List[np.ndarray]:
        return _state_dict_to_list(self.model.state_dict())

    def set_parameters(self, parameters: List[np.ndarray], config: Dict[str, Any] = None) -> None:
        template = self.model.state_dict()
        new_state = _list_to_state_dict(parameters, template)
        # align dtypes and device
        aligned = {k: v.to(DEVICE).type_as(template[k]) for k, v in new_state.items()}
        self.model.load_state_dict(aligned)

    def fit(self, parameters: List[np.ndarray], config: Dict[str, Any]) -> Tuple[List[np.ndarray], int, Dict]:
        # 1) load global params
        # ---- dashboard: mark training ----
        try:
            import socket, requests
            requests.post(
                "http://127.0.0.1:5000/api/fl/node_heartbeat",
                json={
                    "node_id": socket.gethostname(),
                    "status": "training"
                },
                timeout=2
            )
        except:
            pass

        template = self.model.state_dict()
        global_state = _list_to_state_dict(parameters, template)
        global_state_tensors = {k: v.to(DEVICE).clone().detach() for k, v in global_state.items()}

        # 2) load into model
        self.model.load_state_dict({k: v.clone().to(DEVICE) for k, v in global_state_tensors.items()})

        # 3) keep initial copy for delta computation
        initial_state = {k: v.clone().detach().to(DEVICE) for k, v in self.model.state_dict().items()}

        # 4) local training with FedProx
        _local_train_fedprox(
            self.model,
            self.trainloader,
            self.optimizer,
            self.criterion,
            global_state_tensors,
            mu=self.mu,
            device=DEVICE,
            local_epochs=self.local_epochs,
        )

        # 5) compute local state and privatize update
        local_state = {k: v.clone().detach().to(DEVICE) for k, v in self.model.state_dict().items()}
        privatized_state, preclip_norm = _privatize_update(initial_state, local_state, clip_norm=self.clip, sigma=self.sigma, device=DEVICE)

        # 6) apply privatized state locally (keeps client continuity)
        self.model.load_state_dict({k: privatized_state[k].to(DEVICE) for k in privatized_state.keys()})

        # 7) optional personalization (local-only fine-tune)
        if self.personalization_epochs and self.personalization_epochs > 0:
            logger.info(f"Running personalization: {self.personalization_epochs} epochs (local-only)")
            # personalization uses mu=0 to not pull toward global during local-only fine-tuning
            _local_train_fedprox(self.model, self.trainloader, self.optimizer, self.criterion, global_state_tensors, mu=0.0, device=DEVICE, local_epochs=self.personalization_epochs)

        # 8) prepare return values
        num_examples = len(self.trainloader.dataset) if hasattr(self.trainloader.dataset, "__len__") else 0
        params_list = _state_dict_to_list(privatized_state)

        metrics = {
            "preclip_update_norm": preclip_norm,
            "clip": float(self.clip),
            "sigma": float(self.sigma),
        }

        # Optional: compute per-round epsilon (conservative single-round epsilon) if accountant is available
        if _HAS_ACCOUNTANT:
            try:
                per_round_eps, best_a = compute_eps_from_sigma(self.sigma, rounds=1, delta=globals().get("DELTA", 1e-5))
                metrics["per_round_epsilon"] = float(per_round_eps)
                metrics["per_round_alpha"] = int(best_a)
            except Exception:
                pass

        # ---- dashboard: back to idle ----
        try:
            import socket, requests
            requests.post(
                "http://127.0.0.1:5000/api/fl/node_heartbeat",
                json={
                    "node_id": socket.gethostname(),
                    "status": "idle" ,
                    "rounds_completed": 1
                },
                timeout=2
            )
        except:
            pass

        return params_list, num_examples, metrics

    def evaluate(self, parameters: List[np.ndarray], config: Dict[str, Any]) -> Tuple[float, int, Dict]:
        # load global params into model
        template = self.model.state_dict()
        global_state = _list_to_state_dict(parameters, template)
        self.model.load_state_dict({k: v.to(DEVICE) for k, v in global_state.items()})

        loss, acc = _evaluate_local(self.model, self.valloader, self.criterion)
        num_examples = len(self.valloader.dataset) if hasattr(self.valloader.dataset, "__len__") else 0
        return float(loss), num_examples, {"accuracy": float(acc)}

# ---------------------------
# Helper to start client (callable)
# ---------------------------
def start_client_main(server_address: str = FLOWER_SERVER_ADDRESS):
    """Start Flower NumPyClient using this FlowerClient implementation."""

    # 🔹 START HEARTBEAT THREAD HERE
    # import threading
    # threading.Thread(
    #     target=heartbeat_loop,
    #     daemon=True
    # ).start()

    client = FlowerClient()
    logger.info("Starting Flower NumPyClient (FedProx + update-level DP)...")
    fl.client.start_numpy_client(server_address=server_address, client=client)


# ---------------------------
# Run client when executed as script
# ---------------------------
if __name__ == "__main__":
    print("🚀 Starting Flower Federated Client (FedProx + update-level DP)...")
    start_client_main()