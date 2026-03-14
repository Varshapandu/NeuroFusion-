"""
===========================================================
 Dataset Summary Report - Harmful Brain Activity Project
Author: Varsha R
Description: This script analyzes the EEG dataset to produce
             a clear and detailed summary for reports/presentation.
===========================================================
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# 1️ PATH CONFIGURATION
# -----------------------------
CSV_TRAIN = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\train.csv"
EEG_DIR = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\train_eegs"
CACHE_DIR = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\cache"

# -----------------------------
# 2️ LOAD DATA
# -----------------------------
print(" Loading dataset...")
df = pd.read_csv(CSV_TRAIN)

print("\n Dataset loaded successfully!")
print(f"Total rows in train.csv: {len(df)}")
print(f"Unique EEG files: {df['eeg_id'].nunique()}")
print(f"Number of cached EEGs: {len([f for f in os.listdir(CACHE_DIR) if f.endswith('.npz')])}")

# -----------------------------
# 3 BASIC STRUCTURE
# -----------------------------
print("\n=== Dataset Info ===")
print(df.info())
print("\nFirst 5 rows:")
print(df.head())

# -----------------------------
# 4 CHECK FOR MISSING VALUES
# -----------------------------
missing = df.isnull().sum()
print("\n=== Missing Values ===")
print(missing[missing > 0] if missing.sum() > 0 else "No missing values ")

# -----------------------------
#  LABEL DISTRIBUTION
# -----------------------------
if 'expert_consensus' in df.columns:
    label_counts = df['expert_consensus'].value_counts()
    label_percent = (label_counts / len(df) * 100).round(2)
    label_df = pd.DataFrame({'Count': label_counts, 'Percentage': label_percent})
    print("\n=== Label Distribution (Expert Consensus) ===")
    print(label_df)

    # Visualization
    plt.figure(figsize=(8,5))
    sns.barplot(x=label_df.index, y='Count', data=label_df, palette='viridis')
    plt.title("Distribution of Brain Activity Classes")
    plt.xlabel("Brain Activity Type")
    plt.ylabel("Number of EEG Segments")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("class_distribution.png")
    print("\n Saved plot: class_distribution.png")

# -----------------------------
# EEG FILE CHECK
# -----------------------------
csv_ids = set(df['eeg_id'].astype(str))
cached_ids = {os.path.splitext(f)[0] for f in os.listdir(CACHE_DIR) if f.endswith('.npz')}
missing_eegs = csv_ids - cached_ids
print(f"\n Total EEGs referenced in CSV: {len(csv_ids)}")
print(f" Cached EEGs available: {len(cached_ids)}")
print(f" Missing EEGs in cache: {len(missing_eegs)}")

# -----------------------------
#  EXAMPLE EEG SHAPE CHECK
# -----------------------------
try:
    sample_npz = np.load(os.path.join(CACHE_DIR, os.listdir(CACHE_DIR)[0]))
    print("\n=== Example Cached EEG Shape ===")
    print(f"Waveform shape: {sample_npz['waveform'].shape}")
    print(f"Spectrogram shape: {sample_npz['spec'].shape}")
except Exception as e:
    print(f" Could not load example cache file: {e}")

# -----------------------------
#  SUMMARY REPORT
# -----------------------------
print("\n SUMMARY REPORT")
print(f"• Total EEG recordings: {df['eeg_id'].nunique()}")
print(f"• Total segments (rows): {len(df)}")
print(f"• Brain activity classes: {len(df['expert_consensus'].unique())}")
print(f"• Class labels: {list(df['expert_consensus'].unique())}")
print(f"• Missing EEGs: {len(missing_eegs)}")
print("\n Dataset verified and ready for model training.")

