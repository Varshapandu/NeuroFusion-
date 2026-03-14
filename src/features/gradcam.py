import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
import cv2
import os

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.model.eval()

        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        # Register hooks
        target_layer.register_forward_hook(self.forward_hook)
        target_layer.register_backward_hook(self.backward_hook)

    def forward_hook(self, module, input, output):
        self.activations = output.detach()

    def backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, input_waveform, input_spectrogram, class_idx=None):
        # Forward pass
        output = self.model(input_waveform, input_spectrogram)

        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        # Backward pass
        self.model.zero_grad()
        target = output[0, class_idx]
        target.backward()

        # Compute weights
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)

        # Weighted activation maps
        gradcam_map = (weights * self.activations).sum(dim=1)[0]

        # Apply ReLU
        gradcam_map = F.relu(gradcam_map)

        # Normalize
        gradcam_map -= gradcam_map.min()
        gradcam_map /= gradcam_map.max()

        return gradcam_map.cpu().numpy()
