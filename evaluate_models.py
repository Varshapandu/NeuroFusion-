import os
import pandas as pd
import torch
from torch.utils.data import DataLoader
from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset
from src.models.neurofusion_model import NeuroFusionNet

# ---------------- CONFIG ----------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CSV_PATH = r"Dataset/test.csv"          # or train.csv if test.csv not present
CACHE_DIR = r"Dataset/cache"

MODEL_PATHS = {
    "best": "models/neurofusion_best.pt",
    "best_fast": "models/neurofusion_best_fast.pt",
    "final_fast": "models/neurofusion_final_fast.pt",
    "baseline": "models/neurofusion_all_data_baseline.pt",
}

BATCH_SIZE = 16
NUM_CLASSES = 6
# --------------------------------------


def evaluate(model, loader):
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for wav, spec, labels in loader:
            wav = wav.to(DEVICE)
            spec = spec.to(DEVICE)
            labels = labels.to(DEVICE)

            out = model(wav.unsqueeze(0) if wav.dim() == 3 else wav,
                        spec.unsqueeze(0) if spec.dim() == 3 else spec)

            preds = torch.argmax(out, dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

    return correct / total


def main():
    print("📂 Loading dataset...")
    df = pd.read_csv(CSV_PATH)

    dataset = NeuroFusionDualStreamDataset(df, CACHE_DIR)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)

    print(f"✅ Samples: {len(dataset)}")

    for name, path in MODEL_PATHS.items():
        if not os.path.exists(path):
            print(f"❌ Missing model: {path}")
            continue

        print(f"\n🧠 Evaluating: {name}")
        model = NeuroFusionNet(num_classes=NUM_CLASSES).to(DEVICE)

        state = torch.load(path, map_location=DEVICE)
        model.load_state_dict(state)

        acc = evaluate(model, loader)
        print(f"🎯 Accuracy: {acc*100:.2f}%")


if __name__ == "__main__":
    main()
