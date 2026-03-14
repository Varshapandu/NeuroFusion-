import matplotlib
matplotlib.use("Agg")  # safe backend

import sys
import os
import json
import numpy as np
import torch
import pandas as pd
import torch.nn.functional as F
import matplotlib.pyplot as plt

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(ROOT_DIR)

from src.data_processing import preprocess_single_eeg, preprocess_array_eeg
from src.features.eeg_feature_extractor import EEGFeatureExtractor
from src.models.neurofusion_model import NeuroFusionNet
from src.features.eeg_plots import plot_psd, plot_spectrogram
from src.features.gradcam import GradCAM

# CONSTANTS
TARGET_CHANNELS = 20
TARGET_T_WAVE = 1000
TARGET_F_SPEC = 64
TARGET_T_SPEC = 32

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n[INFO] Using device: {device}\n")


# ---------------- Utility ----------------
def downsample_for_ui(arr, max_points=2000):
    arr = np.asarray(arr)
    if arr.shape[0] <= max_points:
        return arr.tolist()
    idx = np.linspace(0, arr.shape[0] - 1, max_points).astype(int)
    return arr[idx].tolist()


# ---------------- Model Loader ----------------
def load_model(model_path):
    model = NeuroFusionNet(num_classes=6)

    # Build absolute model path from project root
    absolute_model_path = os.path.join(ROOT_DIR, model_path)

    print(f"[INFO] Loading model: {absolute_model_path}")

    state_dict = torch.load(
        absolute_model_path,
        map_location=device,
        weights_only=True
    )

    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    print("[INFO] Model loaded successfully.")
    return model


# ---------------- Prepare Waveform ----------------
def prepare_waveform_full(eeg_data):
    wav = torch.tensor(eeg_data, dtype=torch.float32)

    # pad channels
    if wav.shape[0] < TARGET_CHANNELS:
        pad = TARGET_CHANNELS - wav.shape[0]
        wav = torch.cat([wav, torch.zeros((pad, wav.shape[1]))], dim=0)
    else:
        wav = wav[:TARGET_CHANNELS]

    # pad time dimension
    T = wav.shape[1]
    if T < TARGET_T_WAVE:
        wav = F.pad(wav, (0, TARGET_T_WAVE - T))
    else:
        wav = wav[:, :TARGET_T_WAVE]

    # normalize channels
    mean = wav.mean(dim=1, keepdim=True)
    std = wav.std(dim=1, keepdim=True)
    std[std < 1e-6] = 1e-6

    wav = (wav - mean) / std
    return wav.unsqueeze(0).to(device)


# ---------------- Spectrogram ----------------
def create_spectrogram_full(eeg_data, n_fft=128, hop_length=32):
    eeg = torch.tensor(eeg_data, dtype=torch.float32).to(device)
    C = eeg.shape[0]

    window = torch.hann_window(n_fft, device=device)
    specs = []

    for ch in range(C):
        S = torch.stft(
            eeg[ch],
            n_fft=n_fft,
            hop_length=hop_length,
            window=window,
            return_complex=True
        )
        S = torch.log1p(torch.abs(S))
        S4 = S.unsqueeze(0).unsqueeze(0)

        S_resized = F.interpolate(
            S4,
            size=(TARGET_F_SPEC, TARGET_T_SPEC),
            mode="bilinear",
            align_corners=False
        ).squeeze(0).squeeze(0)

        specs.append(S_resized)

    spec = torch.stack(specs, dim=0)

    # pad channels if needed
    if spec.shape[0] < TARGET_CHANNELS:
        pad = TARGET_CHANNELS - spec.shape[0]
        spec = torch.cat([
            spec,
            torch.zeros((pad, TARGET_F_SPEC, TARGET_T_SPEC), device=device)
        ], dim=0)

    return (spec[:TARGET_CHANNELS] - spec.mean()) / (spec.std() + 1e-6)


# ---------------- Predict ----------------
def predict(model, waveform, spectrogram):
    with torch.no_grad():
        out = model(waveform, spectrogram)
        prob = torch.softmax(out, dim=1)
        conf, pred = torch.max(prob, dim=1)

    return int(pred.item()), float(conf.item())




# ---------------- MAIN ANALYSIS FUNCTION ----------------
def analyze_eeg(eeg_path, model_path):
    print("\n================ EEG ANALYSIS STARTED ================\n")

    model = load_model(model_path)
    ext = os.path.splitext(eeg_path)[1].lower()

    # ------ Load EEG ------
    if ext == ".parquet":
        print("[INFO] Detected Parquet EEG. Loading...")
        df = pd.read_parquet(eeg_path)
        df = df.select_dtypes(include=["number"])
        eeg_raw = df.to_numpy(dtype=np.float32).T

        eeg = preprocess_array_eeg(
            eeg_raw,
            fs=200,
            lowcut=0.5,
            highcut=45.0,
            order=4
        )
    else:
        print("[INFO] Preprocessing EEG...")
        eeg = preprocess_single_eeg(eeg_path, fs=200, lowcut=0.5, highcut=45)
        eeg_raw = eeg.copy()

    print("[INFO] Preprocessing complete.")

    waveform = prepare_waveform_full(eeg)
    spectrogram = create_spectrogram_full(eeg)
    spectrogram_batch = spectrogram.unsqueeze(0)

    # ------ Run Model ------
    print("[INFO] Running inference...")
    pred, conf = predict(model, waveform, spectrogram_batch.to(device))
    conf_pct = round(conf * 100, 2)

    print(f"[RESULT] Predicted Class: {pred}")
    print(f"[RESULT] Confidence: {conf_pct}%")

    # ------ Features ------
    features = EEGFeatureExtractor(fs=200).extract_all_features(eeg)

    # ------ Save PSD + Spectrogram ------
    base = os.path.basename(eeg_path)
    os.makedirs("outputs/plots", exist_ok=True)

    psd_path = f"outputs/plots/{base}_psd.png"
    spec_path = f"outputs/plots/{base}_spectrogram.png"

    try:
        plot_psd(eeg, fs=200, save_path=psd_path)
        plot_spectrogram(eeg, fs=200, save_path=spec_path)
    except Exception as e:
        print("[WARN] Plot saving failed:", e)

    # ------ GradCAM ------
    gradcam_path = f"outputs/gradcam/{base}_gradcam.png"
    os.makedirs("outputs/gradcam", exist_ok=True)

    try:
        target_layer = [m for m in model.spectro_encoder.modules() if isinstance(m, torch.nn.Conv2d)][-1]
        cam = GradCAM(model, target_layer)

        heatmap = cam.generate(waveform, spectrogram_batch.to(device), class_idx=pred)
        heatmap_plot = np.mean(heatmap, axis=0)

        plt.figure(figsize=(6, 4))
        plt.imshow(heatmap_plot, cmap="jet", aspect="auto")
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(gradcam_path)
        plt.close()

        print(f"[INFO] Grad-CAM saved: {gradcam_path}")

    except Exception as e:
        print("[WARN] GradCAM failed:", e)
        gradcam_path = None

    # ------ UI Friendly Data ------
    MAX_UI = 2000
    times = downsample_for_ui(np.arange(eeg.shape[1]), MAX_UI)

    cleaned = [downsample_for_ui(eeg[ch], MAX_UI) for ch in range(eeg.shape[0])]
    raw = [downsample_for_ui(eeg_raw[ch], MAX_UI) for ch in range(eeg_raw.shape[0])]

    # Convert spectrogram channels to lists
    try:
        spec_np = spectrogram.cpu().numpy().astype(float)
        spec_list = [spec_np[ch].tolist() for ch in range(spec_np.shape[0])]
    except Exception:
        spec_list = None

    # ------ Build Summary ------
    summary = {
        "predicted_class": pred,
        "confidence": conf_pct,
        "features": features,
        "file_paths": {
            "psd": psd_path,
            "spectrogram": spec_path,
            "gradcam": gradcam_path
        },
        "preprocessed": {
            "times": times,
            "cleaned": cleaned,
            "raw": raw
        },
        "spectrograms": spec_list
    }

    # Save summary JSON
    os.makedirs("outputs/summaries", exist_ok=True)
    summary_path = f"outputs/summaries/{base}_summary.json"

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[INFO] Summary saved:", summary_path)

    return summary


# ---------------- WRAPPER FOR BACKEND ROUTE ----------------
def run_full_pipeline(eeg_path):
    model_path = "models/neurofusion_best_fast.pt"
    summary = analyze_eeg(eeg_path, model_path)

    base = os.path.basename(eeg_path)

    return {
        "prediction": summary["predicted_class"],
        "confidence": summary["confidence"],
        "labels": ["normal" if summary["predicted_class"] == 0 else "seizure-like"],
        "file_paths": summary["file_paths"],
        "summary_path": f"outputs/summaries/{base}_summary.json",
        "report_html": None,  # optional
        "detailed": {
            "preprocessed": summary["preprocessed"],
            "spectrograms": summary["spectrograms"]
        }
    }


if __name__ == "__main__":
    TEST = r"Dataset/test_eegs/3911565283.parquet"
    analyze_eeg(TEST, "models/neurofusion_best.pt")
