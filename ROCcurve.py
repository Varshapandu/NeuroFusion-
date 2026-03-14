import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
import numpy as np

# -----------------------------------------
# CLASS NAMES (match your labels order)
# -----------------------------------------
CLASS_NAMES = ["Seizure", "LPD", "GPD", "LRDA", "GRDA", "Other"]
NUM_CLASSES = len(CLASS_NAMES)

# -----------------------------------------
# BINARIZE TRUE LABELS
# y_true  -> list of class indices
# y_scores -> shape (N, num_classes)
# -----------------------------------------
y_true_bin = label_binarize(y_true, classes=list(range(NUM_CLASSES)))

# -----------------------------------------
# PLOT ROC CURVES
# -----------------------------------------
plt.figure(figsize=(7, 6))

for i, class_name in enumerate(CLASS_NAMES):
    fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_scores[:, i])
    roc_auc = auc(fpr, tpr)

    plt.plot(
        fpr,
        tpr,
        lw=2,
        label=f"{class_name} (AUC = {roc_auc:.2f})"
    )

# Diagonal baseline
plt.plot([0, 1], [0, 1], "k--", lw=2)

# -----------------------------------------
# FIGURE STYLING (matches paper style)
# -----------------------------------------
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Testing ROC Curve")
plt.legend(loc="lower right")
plt.grid(alpha=0.3)
plt.tight_layout()

plt.show()
