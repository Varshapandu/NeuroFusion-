# import os
# import numpy as np
# import torch
# from torch.utils.data import Dataset
# import torch.nn.functional as F
# import json
#
# # ---------- Configuration ----------
# TARGET_T_WAVE = 1000   # waveform time length
# TARGET_F_SPEC = 64     # spectrogram freq bins
# TARGET_T_SPEC = 32     # spectrogram time frames
# TARGET_CHANNELS = 20   # expected channel count
#
# # ---------- Helpers ----------
# def to_channels_time_waveform(x: torch.Tensor) -> torch.Tensor:
#     """
#     Ensure waveform tensor is (channels, time).
#     Accepts (time, channels) or (channels, time).
#     """
#     if x.ndim != 2:
#         raise ValueError("waveform must be 2D at this stage")
#     a, b = x.shape
#     # If already channels x time
#     if a == TARGET_CHANNELS:
#         return x
#     # If second dim equals channels -> likely (time, channels)
#     if b == TARGET_CHANNELS:
#         return x.permute(1, 0)
#     # If one dim is clearly the time dimension (larger), assume it's time
#     if a > b:
#         # a is time, b is channels? permute to (channels, time)
#         return x.permute(1, 0)
#     # fallback: if b > a (time in second dim), keep as (channels,time) by permuting
#     return x.permute(1, 0)
#
#
# def to_channels_freq_time_spectrogram(x: torch.Tensor) -> torch.Tensor:
#     """
#     Ensure spectrogram tensor is (channels, freq, time).
#     Accepts common permutations and uses heuristics.
#     """
#     if x.ndim != 3:
#         raise ValueError("spectrogram must be 3D at this stage")
#     c, f, t = x.shape
#
#     # Common case: already (channels, freq, time)
#     if c == TARGET_CHANNELS:
#         return x
#
#     # Maybe (time, channels, freq) or (freq, channels, time) etc.
#     # Check if second dim equals channels -> shape could be (freq, channels, time)
#     if f == TARGET_CHANNELS:
#         # permute (freq, channels, time) -> (channels, freq, time)
#         return x.permute(1, 0, 2)
#     if t == TARGET_CHANNELS:
#         # rare: (freq, time, channels) -> permute
#         return x.permute(2, 0, 1)
#
#     # If none match, use heuristic: the dimension with largest size is probably time, the smallest is channels
#     dims = [(0, c), (1, f), (2, t)]
#     sorted_dims = sorted(dims, key=lambda x: x[1])
#     # assume smallest is channels
#     ch_idx = sorted_dims[0][0]
#     # assume next smallest is freq, largest is time
#     freq_idx = sorted_dims[1][0]
#     time_idx = sorted_dims[2][0]
#     perm = (ch_idx, freq_idx, time_idx)
#     return x.permute(perm)
#
#
# def pad_channels(tensor: torch.Tensor, target_channels: int) -> torch.Tensor:
#     """
#     Pad or trim the channel dimension (dim=0) to target_channels.
#     tensor shape: (C, ...)
#     """
#     c = tensor.shape[0]
#     if c == target_channels:
#         return tensor
#     if c > target_channels:
#         return tensor[:target_channels, ...]
#     # c < target: pad with zeros for missing channels
#     pad_shape = (target_channels - c,) + tensor.shape[1:]
#     pad_tensor = torch.zeros(pad_shape, dtype=tensor.dtype)
#     return torch.cat([tensor, pad_tensor], dim=0)
#
#
# def pad_time_waveform(waveform: torch.Tensor, target_t: int) -> torch.Tensor:
#     """
#     waveform: (C, T)
#     Pads or trims the time dimension to target_t.
#     """
#     C, T = waveform.shape
#     if T == target_t:
#         return waveform
#     if T < target_t:
#         pad_len = target_t - T
#         # F.pad expects (pad_left, pad_right) for 1D last dim
#         return F.pad(waveform, (0, pad_len))
#     return waveform[:, :target_t]
#
#
# def pad_freq_time_spectrogram(spec: torch.Tensor, target_f: int, target_t: int) -> torch.Tensor:
#     """
#     spec: (C, F, T)
#     Pad/trim freq and time dims. Channel padding handled separately.
#     """
#     C, Fdim, Tdim = spec.shape
#
#     # Time (last dim)
#     if Tdim < target_t:
#         spec = F.pad(spec, (0, target_t - Tdim))  # pads last dim
#     elif Tdim > target_t:
#         spec = spec[..., :target_t]
#
#     # Frequency (middle dim) - F.pad will use (pad_T_left,pad_T_right, pad_F_left,pad_F_right)
#     # We have already handled T; for freq padding we create a pad on dim 1 by using F.pad with two dims
#     # F.pad requires specifying both T and F pads if padding 2 dims, so re-evaluate:
#     _, Fdim, _ = spec.shape
#     if Fdim < target_f:
#         pad_f = target_f - Fdim
#         # pad on freq dimension: (T_left, T_right, F_left, F_right)
#         spec = F.pad(spec, (0, 0, 0, pad_f))
#     elif Fdim > target_f:
#         spec = spec[:, :target_f, :]
#
#     return spec
#
#
# # ---------- Dataset ----------
# class NeuroFusionDualStreamDataset(Dataset):
#     """
#     Dual-stream dataset for EEG classification.
#     Loads waveform + spectrogram from cache and standardizes all shapes/dtypes.
#     """
#
#     def __init__(self, csv_df, cache_dir, transform=None):
#         self.df = csv_df.reset_index(drop=True)
#         self.cache_dir = cache_dir
#         self.transform = transform
#
#         # Map textual labels to integers
#         self.label_map = {
#             "Seizure": 0,
#             "GPD": 1,
#             "LRDA": 2,
#             "Other": 3,
#             "GRDA": 4,
#             "LPD": 5
#         }
#
#         # Filter only cached EEG IDs
#         available = {os.path.splitext(f)[0] for f in os.listdir(cache_dir) if f.endswith(".npz")}
#         self.df = self.df[self.df["eeg_id"].astype(str).isin(available)].reset_index(drop=True)
#         print(f" Dataset initialized with {len(self.df)} EEGs from cache.")
#
#     def __len__(self):
#         return len(self.df)
#
#     def __getitem__(self, idx):
#         row = self.df.iloc[idx]
#         eeg_id = str(row["eeg_id"])
#         text_label = row["expert_consensus"]
#         label = self.label_map.get(text_label, -1)
#         if label == -1:
#             # fallback if unknown label
#             label = 0
#
#         npz_path = os.path.join(self.cache_dir, f"{eeg_id}.npz")
#         data = np.load(npz_path)
#
#         # load arrays and convert to torch tensors
#         waveform_all = torch.tensor(data["waveform"], dtype=torch.float32)  # common: (windows, time, channels) or (windows, channels, time)
#         spec_all = torch.tensor(data["spec"], dtype=torch.float32)         # common: (windows, channels, freq, time)
#
#         # --- Select one random window if first dimension is windows ---
#         # If 3D/4D respectively, first dim is windows
#         if waveform_all.ndim == 3:
#             # waveform_all could be (windows, time, channels) or (windows, channels, time)
#             w = waveform_all[torch.randint(0, waveform_all.shape[0], (1,)).item()]
#         elif waveform_all.ndim == 2:
#             w = waveform_all
#         else:
#             # unexpected dims -> try to squeeze
#             w = waveform_all.reshape(-1, waveform_all.shape[-1])
#
#         if spec_all.ndim == 4:
#             s = spec_all[torch.randint(0, spec_all.shape[0], (1,)).item()]
#         elif spec_all.ndim == 3:
#             s = spec_all
#         else:
#             # unexpected dims -> try to reshape if possible
#             raise ValueError(f"Unexpected spectrogram dims: {spec_all.shape}")
#
#         # --- Normalize shapes: convert to (C, T) and (C, F, T) ---
#         # Waveform heuristics
#         # If w is (time, channels) or (channels, time) -> ensure (channels, time)
#         if w.ndim != 2:
#             raise ValueError(f"Unexpected waveform dims after selection: {w.shape}")
#         # Heuristic convert
#         wav = to_channels_time_waveform(w)
#
#         # Spectrogram heuristics
#         if s.ndim != 3:
#             raise ValueError(f"Unexpected spectrogram dims after selection: {s.shape}")
#         spec = to_channels_freq_time_spectrogram(s)
#
#         # --- Ensure channel count is TARGET_CHANNELS (pad or trim) ---
#         wav = pad_channels(wav, TARGET_CHANNELS)             # (C, T)
#         spec = pad_channels(spec, TARGET_CHANNELS)           # (C, F, T)
#
#         # --- Ensure time/freq dimensions ---
#         wav = pad_time_waveform(wav, TARGET_T_WAVE)          # (C, TARGET_T_WAVE)
#         spec = pad_freq_time_spectrogram(spec, TARGET_F_SPEC, TARGET_T_SPEC)  # (C, TARGET_F_SPEC, TARGET_T_SPEC)
#
#         # --- Per-channel normalization for waveform; global normalization for spectrogram ---
#         wav_mean = wav.mean(dim=1, keepdim=True)
#         wav_std = wav.std(dim=1, keepdim=True)
#         wav_std[wav_std < 1e-6] = 1e-6  # avoid divide-by-zero
#         wav = (wav - wav_mean) / wav_std
#
#         spec_mean = spec.mean()
#         spec_std = spec.std()
#         if spec_std < 1e-6:
#             spec_std = 1e-6
#         spec = (spec - spec_mean) / spec_std
#
#         # --- Clean NaN / Inf values ---
#         wav = torch.nan_to_num(wav, nan=0.0, posinf=1.0, neginf=-1.0)
#         spec = torch.nan_to_num(spec, nan=0.0, posinf=1.0, neginf=-1.0)
#
#         # Convert label to tensor
#         label_t = torch.tensor(label, dtype=torch.long)
#
#         return wav.contiguous(), spec.contiguous(), label_t
#
#
# # ---------- Test mode ----------
# if __name__ == "__main__":
#     import pandas as pd
#     csv_path = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\train.csv"
#     cache_dir = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\cache"
#
#     df = pd.read_csv(csv_path)
#     dataset = NeuroFusionDualStreamDataset(df, cache_dir)
#
#     print(f"Total samples: {len(dataset)}")
#     waveform, spectrogram, label = dataset[0]
#     print("Waveform shape:", waveform.shape)     # (C, T)
#     print("Spectrogram shape:", spectrogram.shape)  # (C, F, T)
#     print("Label:", label)

import os
import numpy as np
import torch
from torch.utils.data import Dataset
import torch.nn.functional as F

# ---------- Configuration ----------
TARGET_T_WAVE = 1000
TARGET_F_SPEC = 64
TARGET_T_SPEC = 32
TARGET_CHANNELS = 20

# ---------- Helpers ----------
def to_channels_time_waveform(x: torch.Tensor) -> torch.Tensor:
    if x.ndim != 2:
        raise ValueError("waveform must be 2D")
    a, b = x.shape
    if a == TARGET_CHANNELS:
        return x
    return x.permute(1, 0)


def to_channels_freq_time_spectrogram(x: torch.Tensor) -> torch.Tensor:
    if x.ndim != 3:
        raise ValueError("spectrogram must be 3D")
    c, f, t = x.shape
    if c == TARGET_CHANNELS:
        return x
    if f == TARGET_CHANNELS:
        return x.permute(1, 0, 2)
    if t == TARGET_CHANNELS:
        return x.permute(2, 0, 1)
    dims = sorted([(0, c), (1, f), (2, t)], key=lambda x: x[1])
    return x.permute(dims[0][0], dims[1][0], dims[2][0])


def pad_channels(x, target):
    if x.shape[0] > target:
        return x[:target]
    if x.shape[0] < target:
        pad = torch.zeros(target - x.shape[0], *x.shape[1:])
        return torch.cat([x, pad], dim=0)
    return x


def pad_time_waveform(wav, target):
    if wav.shape[1] < target:
        return F.pad(wav, (0, target - wav.shape[1]))
    return wav[:, :target]


def pad_freq_time_spectrogram(spec, target_f, target_t):
    if spec.shape[2] < target_t:
        spec = F.pad(spec, (0, target_t - spec.shape[2]))
    spec = spec[:, :, :target_t]

    if spec.shape[1] < target_f:
        spec = F.pad(spec, (0, 0, 0, target_f - spec.shape[1]))
    spec = spec[:, :target_f, :]
    return spec


# ---------- EEG-safe augmentation ----------
def add_gaussian_noise(x, std=0.01):
    return x + std * torch.randn_like(x)


def channel_dropout(x, p=0.1):
    mask = (torch.rand(x.shape[0]) > p).float().unsqueeze(1)
    return x * mask


# ---------- Dataset ----------
class NeuroFusionDualStreamDataset(Dataset):
    def __init__(self, csv_df, cache_dir, train=True):
        self.df = csv_df.reset_index(drop=True)
        self.cache_dir = cache_dir
        self.train = train

        self.label_map = {
            "Seizure": 0,
            "GPD": 1,
            "LRDA": 2,
            "Other": 3,
            "GRDA": 4,
            "LPD": 5
        }

        available = {os.path.splitext(f)[0] for f in os.listdir(cache_dir) if f.endswith(".npz")}
        self.df = self.df[self.df["eeg_id"].astype(str).isin(available)].reset_index(drop=True)
        print(f" Dataset initialized with {len(self.df)} EEGs from cache.")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        eeg_id = str(row["eeg_id"])
        label = self.label_map.get(row["expert_consensus"], 0)

        data = np.load(os.path.join(self.cache_dir, f"{eeg_id}.npz"))

        waveform_all = torch.tensor(data["waveform"], dtype=torch.float32)
        spec_all = torch.tensor(data["spec"], dtype=torch.float32)

        # Random window selection (unchanged)
        w = waveform_all[torch.randint(0, waveform_all.shape[0], (1,)).item()] \
            if waveform_all.ndim == 3 else waveform_all
        s = spec_all[torch.randint(0, spec_all.shape[0], (1,)).item()] \
            if spec_all.ndim == 4 else spec_all

        wav = to_channels_time_waveform(w)
        spec = to_channels_freq_time_spectrogram(s)

        wav = pad_channels(wav, TARGET_CHANNELS)
        spec = pad_channels(spec, TARGET_CHANNELS)

        wav = pad_time_waveform(wav, TARGET_T_WAVE)
        spec = pad_freq_time_spectrogram(spec, TARGET_F_SPEC, TARGET_T_SPEC)

        # Normalization
        wav = (wav - wav.mean(dim=1, keepdim=True)) / (wav.std(dim=1, keepdim=True) + 1e-6)
        spec = (spec - spec.mean()) / (spec.std() + 1e-6)

        # ---------- TRAIN-ONLY AUGMENTATION ----------
        if self.train:
            if torch.rand(1).item() < 0.5:
                wav = add_gaussian_noise(wav)
            if torch.rand(1).item() < 0.3:
                wav = channel_dropout(wav)

        wav = torch.nan_to_num(wav)
        spec = torch.nan_to_num(spec)

        return wav.contiguous(), spec.contiguous(), torch.tensor(label, dtype=torch.long)
