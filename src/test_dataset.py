from torch.utils.data import DataLoader
from src.NeuroFusionDualStreamDataset import NeuroFusionDualStreamDataset

dataset = NeuroFusionDualStreamDataset()
loader = DataLoader(dataset, batch_size=2, shuffle=True)

for waveform, spec, votes, label in loader:
    print("Waveform batch:", waveform.shape)
    print("Spectrogram batch:", spec.shape)
    print("Votes batch:", votes.shape)
    print("Label batch:", label.shape)
    break
