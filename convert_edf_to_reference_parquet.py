import mne
import numpy as np
import pandas as pd

edf_path = r"edf/chb01_04.edf"
output_path = "Dataset/test_eegs/chb01_04_converted.parquet"

TARGET_TIMESTEPS = 10000

CHANNEL_MAP = {
    "Fp1": "FP1-F3",
    "F3":  "F3-C3",
    "C3":  "C3-P3",
    "P3":  "P3-O1",
    "F7":  "FP1-F7",
    "T3":  "F7-T7",
    "T5":  "T7-P7",
    "O1":  "P7-O1",

    "Fz":  "FZ-CZ",
    "Cz":  "FZ-CZ",
    "Pz":  "CZ-PZ",

    "Fp2": "FP2-F4",
    "F4":  "F4-C4",
    "C4":  "C4-P4",
    "P4":  "P4-O2",
    "F8":  "FP2-F8",
    "T4":  "F8-T8",
    "T6":  "T8-P8-0",
    "O2":  "P8-O2",

    "EKG": None   # not available
}

# Load EDF
raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)

data = {}

for target, source in CHANNEL_MAP.items():
    if source is not None and source in raw.ch_names:
        data[target] = raw.get_data(picks=[source])[0]
    else:
        # Fill missing channels with zeros
        data[target] = np.zeros(raw.n_times, dtype=np.float32)

df = pd.DataFrame(data)

# Fix time length
if df.shape[0] > TARGET_TIMESTEPS:
    df = df.iloc[:TARGET_TIMESTEPS]
else:
    pad = TARGET_TIMESTEPS - df.shape[0]
    df = pd.concat(
        [df, pd.DataFrame(np.zeros((pad, df.shape[1])), columns=df.columns)],
        ignore_index=True
    )

# Normalize per channel
df = (df - df.mean()) / (df.std() + 1e-6)

# Match dtype
df = df.astype("float32")

# Final validation
assert df.shape == (10000, 20)

df.to_parquet(output_path)

print("✅ EDF successfully converted to EXACT reference EEG format")
print("Saved at:", output_path)
