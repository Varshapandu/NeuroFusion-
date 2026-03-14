import numpy as np
import scipy.signal as signal
from scipy.stats import kurtosis, entropy

class EEGFeatureExtractor:

    def __init__(self, fs=256):
        """
        fs = sampling frequency of the EEG (default 256 Hz)
        """
        self.fs = fs

        # Standard EEG frequency bands
        self.bands = {
            "delta": (0.5, 4),
            "theta": (4, 8),
            "alpha": (8, 13),
            "beta": (13, 30),
            "gamma": (30, 45)
        }

    # -------------------------------------------------------------
    # 1. Frequency Band Power Extraction
    # -------------------------------------------------------------
    def bandpower(self, signal_data, band):
        low, high = self.bands[band]
        freqs, psd = signal.welch(signal_data, self.fs, nperseg=256)
        idx = np.logical_and(freqs >= low, freqs <= high)
        return np.trapezoid(psd[idx], freqs[idx])

    def extract_bandpowers(self, eeg):
        """
        eeg shape: (channels, samples)
        """
        features = {}
        for channel_idx, ch_data in enumerate(eeg):
            ch_features = {}
            for band in self.bands:
                ch_features[band] = round(self.bandpower(ch_data, band), 4)
            features[f"channel_{channel_idx+1}"] = ch_features

        return features

    # -------------------------------------------------------------
    # 2. Spike / Sharp Wave Detection
    # -------------------------------------------------------------
    def detect_spikes(self, eeg, threshold=3.5):
        """
        Detects sharp spikes by amplitude thresholding.
        """
        spike_info = {}
        for idx, ch in enumerate(eeg):
            mean = np.mean(ch)
            std = np.std(ch)
            spikes = np.where(ch > mean + threshold * std)[0]
            spike_info[f"channel_{idx+1}"] = {
                "spike_count": len(spikes),
                "has_spikes": len(spikes) > 0
            }

        return spike_info

    # -------------------------------------------------------------
    # 3. Statistical Features (Mean, Variance, Kurtosis, Entropy)
    # -------------------------------------------------------------
    def statistical_features(self, eeg):
        stats = {}
        for idx, ch in enumerate(eeg):
            stats[f"channel_{idx+1}"] = {
                "mean": float(np.mean(ch)),
                "variance": float(np.var(ch)),
                "kurtosis": float(kurtosis(ch)),
                "entropy": float(entropy(np.abs(ch) + 1e-6))
            }
        return stats

    # -------------------------------------------------------------
    # 4. Spectrogram Summary (Peak frequency per channel)
    # -------------------------------------------------------------
    def spectrogram_features(self, eeg):
        spec_info = {}
        for idx, ch in enumerate(eeg):
            f, t, Sxx = signal.spectrogram(ch, self.fs)
            peak_freq = f[np.argmax(np.mean(Sxx, axis=1))]
            spec_info[f"channel_{idx+1}"] = {
                "peak_frequency": float(round(peak_freq, 2))
            }
        return spec_info

    # -------------------------------------------------------------
    # Master function that returns ALL FEATURES
    # -------------------------------------------------------------
    def extract_all_features(self, eeg):
        """
        Main function that extracts all features for LLM & XAI.
        eeg shape = (channels, samples)
        """
        return {
            "bandpowers": self.extract_bandpowers(eeg),
            "spikes": self.detect_spikes(eeg),
            "statistics": self.statistical_features(eeg),
            "spectrogram": self.spectrogram_features(eeg)
        }
