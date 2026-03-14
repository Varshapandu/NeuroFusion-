import os
import pandas as pd

# ============================================================
# PATH CONFIG
# ============================================================
BASE_DIR = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset"

ORIGINAL_CSV = os.path.join(BASE_DIR, "train.csv")

SPLIT_DIRS = {
    "train": os.path.join(BASE_DIR, "splits", "train"),
    "val":   os.path.join(BASE_DIR, "splits", "val"),
    "test":  os.path.join(BASE_DIR, "splits", "test"),
}

OUT_CSVS = {
    "train": os.path.join(BASE_DIR, "train_split.csv"),
    "val":   os.path.join(BASE_DIR, "val_split.csv"),
    "test":  os.path.join(BASE_DIR, "test_split.csv"),
}

# ============================================================
# LOAD ORIGINAL CSV
# ============================================================
print("📥 Loading original train.csv ...")
df = pd.read_csv(ORIGINAL_CSV)

required_cols = {"eeg_id", "expert_consensus"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing columns in train.csv: {missing}")

df["eeg_id"] = df["eeg_id"].astype(str)

print(f"✔ Raw rows: {len(df)}")

# ============================================================
# COLLAPSE → ONE ROW PER EEG_ID (CRITICAL FIX)
# ============================================================
print("🧠 Collapsing to one row per eeg_id...")

df_unique = (
    df.groupby("eeg_id", as_index=False)
      .agg({
          "expert_consensus": "first"   # safe: dataset uses single label
      })
)

print(f"✔ Unique EEGs: {len(df_unique)}")

# ============================================================
# HELPER
# ============================================================
def get_eeg_ids(folder):
    return {
        os.path.splitext(f)[0]
        for f in os.listdir(folder)
        if f.endswith(".npz")
    }

# ============================================================
# BUILD SPLIT CSVs
# ============================================================
split_ids = {}
split_dfs = {}

for split, path in SPLIT_DIRS.items():
    ids = get_eeg_ids(path)
    split_ids[split] = ids

    split_df = df_unique[df_unique["eeg_id"].isin(ids)].copy()
    split_dfs[split] = split_df

    print(
        f"📂 {split.upper():5s} | cache files: {len(ids):6d} | csv rows: {len(split_df):6d}"
    )

# ============================================================
# SAFETY CHECKS
# ============================================================
print("\n🔒 Integrity checks...")

assert len(split_ids["train"] & split_ids["val"]) == 0
assert len(split_ids["train"] & split_ids["test"]) == 0
assert len(split_ids["val"]   & split_ids["test"]) == 0

for split in ["train", "val", "test"]:
    assert len(split_dfs[split]) == len(split_ids[split]), \
        f"Mismatch in {split}"

print("✅ Cache ↔ CSV perfectly aligned")

# ============================================================
# SAVE
# ============================================================
for split in ["train", "val", "test"]:
    split_dfs[split].to_csv(OUT_CSVS[split], index=False)
    print(f"💾 Saved {OUT_CSVS[split]}")

print("\n🎉 DONE — split CSVs generated correctly")
