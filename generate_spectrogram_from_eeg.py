import numpy as np
import pandas as pd
from scipy.signal import spectrogram

# ---------------- Load EEG ----------------
eeg = pd.read_parquet("Dataset/test_eegs/chb01_04_converted.parquet")
eeg_np = eeg.values.astype(np.float32)   # (10000, 20)

# ---------------- Spectrogram params ----------------
FS = 256
NPERSEG = 128
NOVERLAP = 112
NFFT = 600

spec_list = []

for ch in range(eeg_np.shape[1]):
    f, t, Sxx = spectrogram(
        eeg_np[:, ch],
        fs=FS,
        nperseg=NPERSEG,
        noverlap=NOVERLAP,
        nfft=NFFT,
        scaling="density",
        mode="magnitude"
    )
    spec_list.append(Sxx)

# ---------------- Aggregate channels ----------------
spec_avg = np.mean(spec_list, axis=0)

# ---------------- Log compression ----------------
spec_avg = np.log1p(spec_avg)

# ---------------- Force exact shape ----------------
TARGET_FREQ = 300
TARGET_TIME = 401

spec_avg = spec_avg[:TARGET_FREQ, :TARGET_TIME]

freq_pad = TARGET_FREQ - spec_avg.shape[0]
time_pad = TARGET_TIME - spec_avg.shape[1]

if freq_pad > 0 or time_pad > 0:
    spec_avg = np.pad(
        spec_avg,
        ((0, max(0, freq_pad)), (0, max(0, time_pad))),
        mode="constant"
    )

assert spec_avg.shape == (300, 401)

# ---------------- Save ----------------
out_path = "Dataset/test_spectrograms/chb01_04_spectrogram.parquet"
pd.DataFrame(spec_avg.astype(np.float32)).to_parquet(out_path)

print("✅ Spectrogram generated successfully")
print("Final shape:", spec_avg.shape)
