# federated/server.py
import os
import sys

# -----------------------------------------------------------
# FIX PYTHON PATH (PROJECT ROOT)
# -----------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import logging
import time
import torch
import flwr as fl
import numpy as np
from sklearn.metrics import confusion_matrix
from torch.utils.data import DataLoader, random_split
import pandas as pd
from flwr.common import parameters_to_ndarrays

from src.models.neurofusion_model import NeuroFusionNet
from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset

from federated.config import (
    NUM_ROUNDS,
    FLOWER_SERVER_ADDRESS,
    TOTAL_CLIENTS,
    CLIENTS_PER_ROUND,
    DELTA,
    TEST_CSV,
    CACHE_DIR,
    BATCH_SIZE,
)

from federated.accountant import (
    compute_eps_fullparticipation,
    compute_eps_poisson_subsampled,
)

# -----------------------------------------------------------
# DEVICE
# -----------------------------------------------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

NUM_CLASSES = 6   # ✅ matches NeuroFusionDualStreamDataset

# -----------------------------------------------------------
# GLOBAL MODEL
# -----------------------------------------------------------
global_model = NeuroFusionNet(
    in_channels=20,
    num_classes=NUM_CLASSES
).to(DEVICE)

# -----------------------------------------------------------
# LOGGER
# -----------------------------------------------------------
logger = logging.getLogger("fed_server")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(handler)

# -----------------------------------------------------------
# GLOBAL TEST LOADER
# -----------------------------------------------------------
def create_global_test_loader():
    df = pd.read_csv(TEST_CSV)
    test_dataset = NeuroFusionDualStreamDataset(
        csv_df=df,
        cache_dir=CACHE_DIR
    )

    logger.info(f"Global Test EEGs = {len(test_dataset)}")

    return DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        drop_last=False,
        pin_memory=(DEVICE.type == "cuda"),
    )



GLOBAL_TEST_LOADER = create_global_test_loader()


# -----------------------------------------------------------
# CHECKPOINTS
# -----------------------------------------------------------
CHECKPOINT_DIR = "checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# ===========================================================
# FEDAVG STRATEGY
# ===========================================================
class DashboardFedAvg(fl.server.strategy.FedAvg):

    def __init__(self, *args, total_clients, clients_per_round, delta, **kwargs):
        super().__init__(*args, **kwargs)
        self.rounds_completed = 0
        self.total_clients = total_clients
        self.clients_per_round = clients_per_round
        self.delta = delta
        self._round_start_time = None

    #  FIXED SIGNATURE (Flower expects server_round)
    def configure_fit(self, server_round, parameters, client_manager):
        self._round_start_time = time.time()
        try:
            import requests

            requests.post(
                "http://127.0.0.1:5000/api/fl/round_update",
                json={
                    "round": server_round,
                    "round_running": True,
                    "training_progress": {
                        "current": 0,
                        "total": self.clients_per_round
                    }
                },
                timeout=2
            )
        except Exception as e:
            logger.error(f"[notify_round_start] {e}")

        return super().configure_fit(server_round, parameters, client_manager)

    #  REQUIRED for DP metrics
    def _infer_sigma(self, results):
        for _, fit_res in results:
            metrics = getattr(fit_res, "metrics", {})
            if isinstance(metrics, dict) and "sigma" in metrics:
                return float(metrics["sigma"])
        try:
            from federated.config import UPDATE_NOISE_MULTIPLIER
            return float(UPDATE_NOISE_MULTIPLIER)
        except Exception:
            return None

    def aggregate_fit(self, server_round, results, failures):
        aggregated = super().aggregate_fit(server_round, results, failures)
        if aggregated is None:
            logger.error(
                f"[ROUND {server_round}] Aggregation failed "
                f"(results={len(results)}, failures={len(failures)})"
            )
            return None

        self.rounds_completed += 1
        r = self.rounds_completed
        round_time = time.time() - self._round_start_time

        sigma = self._infer_sigma(results)
        if sigma is None:
            return aggregated

        eps_full, _ = compute_eps_fullparticipation(
            clip_norm=1.0,
            sigma_multiplier=sigma,
            rounds=r,
            delta=self.delta,
        )

        q = self.clients_per_round / self.total_clients
        eps_sampled, _ = compute_eps_poisson_subsampled(sigma, q, r, self.delta)

        from flwr.common import parameters_to_ndarrays

        # aggregated is (Parameters, metrics)
        flwr_params = aggregated[0]

        # Convert Flower Parameters → list of numpy arrays
        params_ndarrays = parameters_to_ndarrays(flwr_params)

        # Load safely into model
        state_dict = global_model.state_dict()
        new_state_dict = {}

        for key, w in zip(state_dict.keys(), params_ndarrays):
            new_state_dict[key] = torch.tensor(w, device=DEVICE)

        global_model.load_state_dict(new_state_dict, strict=True)

        # Evaluate
        try:
            accuracy, loss, confusion = evaluate_global_model(
                global_model, GLOBAL_TEST_LOADER, DEVICE
            )
        except Exception as e:
            logger.error(f"[Evaluation Error] {e}")
            accuracy, loss, confusion = None, None, None

        # Notify dashboard
        try:
            import requests

            requests.post(
                "http://127.0.0.1:5000/api/fl/round_update",
                json={
                    "round": r,
                    "round_running": False,
                    "metrics": {
                        "accuracy": accuracy,
                        "loss": loss,
                        "epsilon_full": eps_full,
                        "epsilon_sampled": eps_sampled,
                        "sigma": sigma,
                        "q": q,
                        "round_time": round_time,
                    }
                },
                timeout=2
            )

        except Exception as e:
            logger.error(f"[notify_round_complete] {e}")

        return aggregated


# ===========================================================
# EVALUATION
# ===========================================================
def evaluate_global_model(model, test_loader, device):
    model.eval()
    y_true, y_pred = [], []
    loss_sum = 0.0
    criterion = torch.nn.CrossEntropyLoss()

    with torch.no_grad():
        for waveform, spectrogram, labels in test_loader:
            waveform = waveform.to(device)
            spectrogram = spectrogram.to(device)
            labels = labels.to(device)

            outputs = model(waveform, spectrogram)
            loss = criterion(outputs, labels)

            loss_sum += loss.item()
            preds = torch.argmax(outputs, dim=1)

            y_true.extend(labels.cpu().numpy())
            y_pred.extend(preds.cpu().numpy())

    acc = (np.array(y_true) == np.array(y_pred)).mean()
    avg_loss = loss_sum / len(test_loader)
    cm = confusion_matrix(y_true, y_pred)

    return float(acc), float(avg_loss), cm.tolist()

# ===========================================================
# SERVER ENTRY
# ===========================================================
def start_fl_server(num_rounds=None, server_address=None):
    """
    Start the Flower FL server.
    
    Args:
        num_rounds (int, optional): Number of training rounds. Defaults to config value.
        server_address (str, optional): Server address. Defaults to config value.
    """
    # Use provided values or fall back to config
    rounds = num_rounds if num_rounds is not None else NUM_ROUNDS
    addr = server_address if server_address is not None else FLOWER_SERVER_ADDRESS
    
    print(f"\n{'='*60}")
    print(f"📊 Server Configuration:")
    print(f"  Rounds: {rounds}")
    print(f"  Address: {addr}")
    print(f"  Clients per round: {CLIENTS_PER_ROUND}")
    print(f"{'='*60}\n")
    
    # strategy = DashboardFedAvg(
    #     fraction_fit=CLIENTS_PER_ROUND / TOTAL_CLIENTS,
    #     min_fit_clients=CLIENTS_PER_ROUND,
    #     min_available_clients=TOTAL_CLIENTS,
    #     total_clients=TOTAL_CLIENTS,
    #     clients_per_round=CLIENTS_PER_ROUND,
    #     delta=DELTA,
    # )
    strategy = DashboardFedAvg(
        fraction_fit=1.0,  # use the single available client
        min_fit_clients=1,  #  allow 1 client
        min_available_clients=1,  #  allow server to start
        total_clients=1,  # match reality
        clients_per_round=1,  # match reality
        delta=DELTA,
    )

    fl.server.start_server(
        server_address=addr,
        config=fl.server.ServerConfig(num_rounds=rounds),
        strategy=strategy,
    )

if __name__ == "__main__":
    start_fl_server()
