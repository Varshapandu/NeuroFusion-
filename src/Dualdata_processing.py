import os
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
import torch.nn.functional as F
import scipy.signal as signal
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# ---------------- DEVICE ----------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using device: {device}")
torch.backends.cudnn.benchmark = True
torch.cuda.empty_cache()

# ---------------- FAST FILE LOADING ----------------
def load_parquet_file(path):
    """Safely load parquet and convert to float32 numpy."""
    table = pq.read_table(path)
    return table.to_pandas().to_numpy(dtype=np.float32)

# ---------------- FILTERING ----------------
def bandpass_filtfilt_np(X, low=0.5, high=45.0, fs=200.0, order=4):
    nyquist = fs / 2
    b, a = signal.butter(order, [low / nyquist, high / nyquist], btype='band')
    X_filtered = np.zeros_like(X, dtype=np.float32)
    for i in range(X.shape[1]):
        X_filtered[:, i] = signal.filtfilt(b, a, X[:, i])
    return X_filtered

# ---------------- GPU OPS ----------------
def gpu_robust_zscore(X):
    median = torch.median(X, dim=0).values
    mad = torch.median(torch.abs(X - median), dim=0).values + 1e-6
    return (X - median) / mad

def gpu_segment_windows(X, window, step):
    num_windows = (X.size(0) - window) // step + 1
    shape = (num_windows, window, X.size(1))
    stride = (X.stride(0) * step, X.stride(0), X.stride(1))
    return X.as_strided(shape, stride).contiguous()

def normalize_tensor(X):
    return (X - X.mean()) / (X.std() + 1e-6)

# ---------------- PROCESS SINGLE EEG ----------------
def process_single_eeg(row, eeg_dir, spec_dir, cache_dir, params):
    eeg_id = int(row.eeg_id)
    cache_path = os.path.join(cache_dir, f"{eeg_id}.npz")
    if os.path.exists(cache_path):
        return eeg_id

    eeg_path = os.path.join(eeg_dir, f"{eeg_id}.parquet")
    spec_path = os.path.join(spec_dir, f"{eeg_id}.parquet")

    if not os.path.exists(eeg_path):
        print(f"⚠️ Missing EEG file: {eeg_path}")
        return None
    if not os.path.exists(spec_path):
        print(f"⚠️ Missing spectrogram file: {spec_path}")
        return None

    # ---- Load EEG ----
    X = load_parquet_file(eeg_path)
    X = torch.tensor(X, device=device)

    # Handle NaNs
    if torch.isnan(X).any():
        col_mean = torch.nanmean(X, dim=0)
        inds = torch.where(torch.isnan(X))
        X[inds] = col_mean[inds[1]]

    # Bandpass filter (CPU) + normalization (GPU)
    X_cpu = X.detach().cpu().numpy()
    X_cpu = bandpass_filtfilt_np(X_cpu, params["lowcut"], params["highcut"], params["fs"], params["order"])
    X = torch.tensor(X_cpu, device=device)
    X = gpu_robust_zscore(X)

    # Segment EEG into windows
    W = gpu_segment_windows(X, params["window"], params["step"])
    W = normalize_tensor(W)

    # ---- Load Spectrogram ----
    S = load_parquet_file(spec_path)
    S = torch.tensor(S, dtype=torch.float32, device=device)

    # If spectrogram is 2D (freq x time), expand to match channels
    if S.ndim == 2:
        S = S.unsqueeze(0)
    S = normalize_tensor(S)

    # Adjust spectrogram to fixed size
    TARGET_F, TARGET_T = 64, 32
    C = S.shape[0]
    if S.shape[-2] < TARGET_F:
        S = F.pad(S, (0, 0, 0, TARGET_F - S.shape[-2]))
    else:
        S = S[..., :TARGET_F, :]
    if S.shape[-1] < TARGET_T:
        S = F.pad(S, (0, TARGET_T - S.shape[-1]))
    else:
        S = S[..., :TARGET_T]

    # Convert to numpy and save
    np.savez_compressed(cache_path, waveform=W.cpu().numpy(), spec=S.cpu().numpy())

    if device.type == "cuda":
        torch.cuda.empty_cache()

    return eeg_id

# ---------------- PRECOMPUTE ALL ----------------
def precompute_all(csv_path, eeg_dir, spec_dir, cache_dir, params):
    df = pd.read_csv(csv_path)
    os.makedirs(cache_dir, exist_ok=True)
    num_workers = min(4, cpu_count() // 2)
    print(f"🚀 Starting dual-stream preprocessing on {len(df)} EEGs (EEG + Spectrogram)...")

    args_list = [(row, eeg_dir, spec_dir, cache_dir, params) for _, row in df.iterrows()]
    with Pool(num_workers) as pool:
        for _ in tqdm(pool.imap_unordered(_process_wrapper, args_list), total=len(args_list)):
            pass
    print("✅ All EEG + Spectrogram data preprocessed and cached!")

def _process_wrapper(args):
    return process_single_eeg(*args)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    csv_path = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\train.csv"
    eeg_dir = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\train_eegs"
    spec_dir = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\train_spectrograms"
    cache_dir = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\cache"

    params = {
        "lowcut": 0.5,
        "highcut": 45.0,
        "fs": 200.0,
        "order": 4,
        "window": 1000,
        "step": 500,
        "n_fft": 128,
        "hop_length": 32,
    }

    precompute_all(csv_path, eeg_dir, spec_dir, cache_dir, params)
