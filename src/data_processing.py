import os
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
import torch.nn.functional as F
import scipy.signal as signal
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def _process_wrapper(args):
    """Wrapper for multiprocessing to avoid lambda pickling errors."""
    return process_single_eeg(*args)


# ---------------- DEVICE ----------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using device: {device}")
# Enable cuDNN autotuning and clear memory before starting
torch.backends.cudnn.benchmark = True
torch.cuda.empty_cache()


# ---------------- FAST FILE LOADING ----------------
def load_eeg_parquet(eeg_path):
    """Loads EEG parquet file and converts to NumPy array safely for all PyArrow versions."""
    table = pq.read_table(eeg_path)
    # Convert to pandas DataFrame and then to numpy (safe and version-independent)
    df = table.to_pandas()
    X = df.to_numpy(dtype=np.float32)
    return X

import scipy.signal as signal

def bandpass_filtfilt_np(X, low=0.5, high=45.0, fs=200.0, order=4):
    """
    CPU-based Butterworth bandpass filter using scipy.signal.filtfilt.
    Safe and memory-efficient version for large EEG arrays.
    Args:
        X: numpy array [samples, channels]
        low: low cutoff frequency (Hz)
        high: high cutoff frequency (Hz)
        fs: sampling frequency (Hz)
        order: filter order
    Returns:
        Filtered numpy array of same shape.
    """
    nyquist = fs / 2
    b, a = signal.butter(order, [low / nyquist, high / nyquist], btype='band')
    # Apply filter to each EEG channel independently
    X_filtered = np.zeros_like(X, dtype=np.float32)
    for i in range(X.shape[1]):
        X_filtered[:, i] = signal.filtfilt(b, a, X[:, i])
    return X_filtered

def gpu_robust_zscore(X):
    """Compute z-score normalization using median and MAD on GPU."""
    median = torch.median(X, dim=0).values
    mad = torch.median(torch.abs(X - median), dim=0).values + 1e-6
    return (X - median) / mad

def gpu_segment_windows(X, window, step):
    """Vectorized segmentation using PyTorch striding on GPU."""
    num_windows = (X.size(0) - window) // step + 1
    shape = (num_windows, window, X.size(1))
    stride = (X.stride(0) * step, X.stride(0), X.stride(1))
    return X.as_strided(shape, stride).contiguous()

def compute_stft_batch_gpu(W, fs=200.0, n_fft=128, hop_length=32):
    """Compute batched STFT for all windows on GPU."""
    # W: (num_windows, window_length, channels)
    W = W.permute(0, 2, 1)  # (num_windows, channels, length)
    window_fn = torch.hann_window(n_fft, device=device)
    specs = []
    for ch in range(W.shape[1]):
        S = torch.stft(W[:, ch, :], n_fft=n_fft, hop_length=hop_length,
                       window=window_fn, return_complex=True)
        S = torch.log1p(torch.abs(S))
        S = (S - S.amin(dim=(-2, -1), keepdim=True)) / (S.amax(dim=(-2, -1), keepdim=True) - S.amin(dim=(-2, -1), keepdim=True) + 1e-8)
        specs.append(S)
    return torch.stack(specs, dim=1)  # (num_windows, channels, freq, time)

# ---------------- PROCESS SINGLE EEG ----------------
def process_single_eeg(row, eeg_dir, cache_dir, params):
    eeg_id = int(row.eeg_id)
    cache_path = os.path.join(cache_dir, f"{eeg_id}.npz")
    if os.path.exists(cache_path):
        return eeg_id

    eeg_path = os.path.join(eeg_dir, f"{eeg_id}.parquet")
    if not os.path.exists(eeg_path):
        print(f" Missing file: {eeg_path}")
        return None

    X = load_eeg_parquet(eeg_path)
    X = torch.tensor(X, device=device)

    # Interpolate/fill NaNs safely per channel
    if torch.isnan(X).any():
        col_mean = torch.nanmean(X, dim=0)
        inds = torch.where(torch.isnan(X))
        X[inds] = col_mean[inds[1]]

    # Bandpass filtering on CPU (safe)
    X_cpu = X.detach().cpu().numpy()
    X_cpu = bandpass_filtfilt_np(X_cpu, params["lowcut"], params["highcut"], params["fs"], params["order"])
    X = torch.tensor(X_cpu, device=device)

    # Normalization and segmentation
    X = gpu_robust_zscore(X)
    W = gpu_segment_windows(X, params["window"], params["step"])
    St = compute_stft_batch_gpu(W, fs=params["fs"],
                                n_fft=params["n_fft"],
                                hop_length=params["hop_length"])

    np.savez_compressed(cache_path, waveform=W.cpu().numpy(), spec=St.cpu().numpy())

    # Free GPU memory after each file
    if device.type == "cuda":
        torch.cuda.empty_cache()

    return eeg_id



# ---------------- PRECOMPUTE ALL ----------------
def precompute_all(csv_path, eeg_dir, cache_dir, params):
    df = pd.read_csv(csv_path)
    os.makedirs(cache_dir, exist_ok=True)
    num_workers = min(4, cpu_count() // 2)  # Limit CPU side I/O
    print(f" Starting GPU-accelerated preprocessing on {len(df)} EEGs...")

    args_list = [(row, eeg_dir, cache_dir, params) for _, row in df.iterrows()]
    with Pool(num_workers) as pool:
        for _ in tqdm(pool.imap_unordered(_process_wrapper, args_list),
                      total=len(args_list)):
            pass
    print(" All EEGs preprocessed and cached.")

def preprocess_array_eeg(eeg_array, fs, lowcut, highcut, order):
    """
    EEG preprocessing for already-loaded numpy arrays.
    Mirrors preprocess_single_eeg() but skips file loading.
    """
    from scipy.signal import butter, filtfilt

    # Ensure 2D
    if eeg_array.ndim != 2:
        raise ValueError("EEG array must be shape (channels, samples).")

    channels, samples = eeg_array.shape
    print(f"[INFO] Raw EEG array → {channels} channels, {samples} samples")

    # Band-pass filter
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq

    b, a = butter(order, [low, high], btype="band")

    filtered = filtfilt(b, a, eeg_array, axis=1)

    # Replace NaN/Inf
    filtered = np.nan_to_num(filtered)

    return filtered


# -------------------------------------------------------------
#   PREPROCESS A SINGLE EEG FILE (for inference + reporting)
# -------------------------------------------------------------
def preprocess_single_eeg(eeg_path, fs=200.0, lowcut=0.5, highcut=45.0, order=4):
    """
    Lightweight preprocessing for inference:
    - supports .parquet or .edf
    - applies bandpass filter
    - z-score normalization
    - returns EEG as (channels, samples)
    """

    print(f"[INFO] Loading EEG: {eeg_path}")

    # -----------------------------------------------------
    # 1. LOAD EEG (PARQUET or EDF)
    # -----------------------------------------------------
    if eeg_path.endswith(".parquet"):
        # load EEG from parquet (training-style)
        X = load_eeg_parquet(eeg_path)    # shape (samples, channels)
        X = X.astype(np.float32)
        X = X.T                            # → (channels, samples)

    elif eeg_path.endswith(".edf"):
        import mne
        raw = mne.io.read_raw_edf(eeg_path, preload=True, verbose=False)
        X = raw.get_data()                 # already (channels, samples)

    else:
        raise ValueError("Unsupported EEG format. Use .edf or .parquet")

    # -----------------------------------------------------
    # 2. BANDPASS FILTER (Same config as training path)
    # -----------------------------------------------------
    nyquist = fs / 2
    b, a = signal.butter(order, [lowcut / nyquist, highcut / nyquist], btype='band')

    X_filt = np.zeros_like(X, dtype=np.float32)
    for ch in range(X.shape[0]):
        X_filt[ch] = signal.filtfilt(b, a, X[ch])

    # -----------------------------------------------------
    # 3. Z-SCORE NORMALIZATION
    # -----------------------------------------------------
    for ch in range(X_filt.shape[0]):
        mean = X_filt[ch].mean()
        std = X_filt[ch].std() + 1e-6
        X_filt[ch] = (X_filt[ch] - mean) / std

    print("[INFO] Single EEG preprocessing complete.")

    return X_filt.astype(np.float32)

