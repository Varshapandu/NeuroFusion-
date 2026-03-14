import os
import mne
import pandas as pd

# ---------------- PATHS ----------------
EDF_DIR = "edf"   # folder where your .edf files are

OUT_DIR = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\test_eegs"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------- CHANNELS ----------------
TARGET_CHANNELS = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
    "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
    "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
    "FZ-CZ", "CZ-PZ", "P7-T7", "P8-T8"
]

def normalize_name(ch):
    return ch.replace(" ", "").upper()

# ---------------- CONVERSION ----------------
for fname in os.listdir(EDF_DIR):
    if not fname.lower().endswith(".edf"):
        continue

    print(f"\n▶ Processing {fname}")

    edf_path = os.path.join(EDF_DIR, fname)

    raw = mne.io.read_raw_edf(
        edf_path,
        preload=True,
        verbose=False
    )

    available = {normalize_name(ch): ch for ch in raw.ch_names}

    selected = []
    for tgt in TARGET_CHANNELS:
        key = normalize_name(tgt)
        if key in available:
            selected.append(available[key])

    if len(selected) < 20:
        print(f"⚠ Warning: only {len(selected)} / 20 channels found")

    raw.pick_channels(selected)

    data = raw.get_data().T  # (time, channels)

    df = pd.DataFrame(data, columns=raw.ch_names)

    out_path = os.path.join(
        OUT_DIR,
        fname.replace(".edf", ".parquet")
    )

    df.to_parquet(out_path, engine="pyarrow")

    print(f"✅ Saved to: {out_path}")
    print(f"   Shape: {df.shape}")

print("\n🎉 All EDF files converted and saved to test_eegs folder.")
