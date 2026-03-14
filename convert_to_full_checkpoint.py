import torch
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

OLD_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "neurofusion_best_fast.pt")
NEW_CKPT_PATH  = os.path.join(PROJECT_ROOT, "checkpoints", "neurofusion_fast_resume.pt")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

from src.models.neurofusion_model import NeuroFusionNet

model = NeuroFusionNet(num_classes=6).to(device)

# Load old weights
model.load_state_dict(torch.load(OLD_MODEL_PATH, map_location=device))

# Save as proper checkpoint
torch.save({
    "epoch": 20,           # last epoch you trained
    "model": model.state_dict(),
    "optimizer": None,
    "scaler": None,
    "best_acc": 0.5999
}, NEW_CKPT_PATH)

print("✅ Converted to full checkpoint format.")
