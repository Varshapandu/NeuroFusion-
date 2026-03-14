import os
import numpy as np
from tqdm import tqdm

cache_dir = r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\cache"

total_files = 0
corrupted = 0

for file in tqdm(os.listdir(cache_dir)):
    if file.endswith(".npz"):
        total_files += 1
        path = os.path.join(cache_dir, file)
        try:
            data = np.load(path)
            _ = data["waveform"]
            _ = data["spec"]
        except Exception as e:
            corrupted += 1
            print(f" Corrupted file: {file} ({e})")

print(f"\nTotal valid files: {total_files - corrupted}")
print(f" Corrupted files: {corrupted}")
