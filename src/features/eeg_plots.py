import matplotlib
matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch

# ================================
# 1) POWER SPECTRAL DENSITY (PSD)
# ================================
def plot_psd(eeg_data, fs=200, save_path="psd.png"):
    """
    eeg_data: numpy array or torch tensor (C, samples)
    """
    if not isinstance(eeg_data, np.ndarray):
        eeg_data = eeg_data.cpu().numpy()

    channels = eeg_data.shape[0]
    plt.figure(figsize=(14, 6))

    for ch in range(channels):
        f, Pxx = welch(eeg_data[ch], fs=fs, nperseg=512)
        plt.semilogy(f, Pxx, label=f"Ch {ch+1}")

    plt.title("Power Spectral Density (PSD)", fontsize=14)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Power")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(save_path)
    plt.close()


# ================================
# 2) SPECTROGRAM (STFT)
# ================================
def plot_spectrogram(eeg_data, fs=200, save_path="spectrogram.png"):
    """
    eeg_data: numpy array or torch tensor (C, samples)
    Uses channel 1 for visualization.
    """
    if not isinstance(eeg_data, np.ndarray):
        eeg_data = eeg_data.cpu().numpy()

    ch1 = eeg_data[0]

    plt.figure(figsize=(14, 6))
    plt.specgram(ch1, Fs=fs, NFFT=256, noverlap=128, cmap="magma")
    plt.title("Spectrogram (Channel 1)", fontsize=14)
    plt.xlabel("Time (sec)")
    plt.ylabel("Frequency (Hz)")
    plt.colorbar(label="Intensity")
    plt.tight_layout()

    plt.savefig(save_path)
    plt.close()
