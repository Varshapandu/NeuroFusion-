import os
import time
import torch
from src.data_processing import precompute_all
from src.utils.path_config import get_paths



# ---------------- SETUP DEVICE ----------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f" Using device: {device}")

# ---------------- MAIN FUNCTION ----------------
def main():
    print(" Starting EEG + Spectrogram preprocessing...")

    # ---- Load Paths ----
    paths = get_paths()

    # ---- Parameter Configurations ----
    params = {
        "use_gpu": True,           # Use GPU for STFT and normalization
        "num_workers": 0,          # Keep 0 for GPU safety (avoid CUDA context duplication)
        "gpu_chunk_size": 64,      # Reduced to prevent VRAM overflow
        "window": 500,             # Reduced from 1000 for speed
        "step": 250,               # Reduced from 500
        "n_fft": 64,               # Smaller FFT for faster frequency calc
        "hop_length": 16,          # Time step for STFT
        "fs": 200.0,               # Sampling frequency
        "lowcut": 0.5,             # Bandpass filter low frequency
        "highcut": 45.0,           # Bandpass filter high frequency
        "order": 4                 # Butterworth filter order
    }

    # ---- Create cache directory if not exists ----
    os.makedirs(paths["cache_dir"], exist_ok=True)

    print(f" Starting GPU-accelerated preprocessing on {len(open(paths['csv_train']).readlines()) - 1} EEGs...")

    start_time = time.time()

    # ---- Precompute (EEG -> cache npz) ----
    precompute_all(
        csv_path=paths["csv_train"],
        eeg_dir=paths["eeg_dir"],
        cache_dir=paths["cache_dir"],
        params=params
    )

    end_time = time.time()
    print(f" All EEGs preprocessed and cached in {end_time - start_time:.2f} seconds.")

# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    main()
