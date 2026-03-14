import os
import sys

# Get absolute path to project root
CURRENT_DIR = os.path.dirname(__file__)                       # backend/services
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

# Add project root to Python path
sys.path.insert(0, PROJECT_ROOT)

from src.features.run_eeg_analysis import run_full_pipeline

def process_eeg_file(filepath):
    print("[INFO] Running Pipeline for:", filepath)

    results = run_full_pipeline(filepath)

    # Convert all relative paths to absolute
    for key, value in results.items():
        if isinstance(value, str) and os.path.exists(value):
            results[key] = os.path.abspath(value)

    return results
