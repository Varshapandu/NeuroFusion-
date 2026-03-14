import os
import numpy as np
from tqdm import tqdm

# === Update this to your actual cache folder path ===
cache_dir = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\cache"

wave_shapes = []
spec_shapes = []
total_size_gb = 0
sample_count = 0

for file in tqdm(os.listdir(cache_dir)):
    if file.endswith(".npz"):
        path = os.path.join(cache_dir, file)
        try:
            data = np.load(path)
            waveform = data["waveform"]
            spec = data["spec"]

            # Record shapes
            wave_shapes.append(waveform.shape)
            spec_shapes.append(spec.shape)

            # File size in GB
            total_size_gb += os.path.getsize(path) / (1024**3)
            sample_count += 1

        except Exception as e:
            print(f"❌ Error reading {file}: {e}")

# === Summarize results ===
print("\n========== CACHE SUMMARY ==========")
print(f" Total cached files: {sample_count}")
if wave_shapes:
    print(f"Example waveform shape: {wave_shapes[0]}")
    print(f"Example spectrogram shape: {spec_shapes[0]}")

    # Find unique shapes (sometimes small EEGs may differ slightly)
    unique_wave = set(wave_shapes)
    unique_spec = set(spec_shapes)
    print(f" Unique waveform shapes: {len(unique_wave)}")
    print(f" Unique spectrogram shapes: {len(unique_spec)}")

print(f" Total cache size: {total_size_gb:.2f} GB")
print("===================================\n")
