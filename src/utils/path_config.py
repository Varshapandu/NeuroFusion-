import os

def get_paths():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    dataset_dir = os.path.join(BASE_DIR, "Dataset")

    paths = {
        "csv_train": os.path.join(dataset_dir, "train.csv"),
        "csv_test": os.path.join(dataset_dir, "test.csv"),
        "eeg_dir": os.path.join(dataset_dir, "train_eegs"),
        "cache_dir": os.path.join(dataset_dir, "cache"),
    }
    return paths