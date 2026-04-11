import numpy as np
from numpy.typing import ArrayLike
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score


def print_stats(y_true: ArrayLike, y_prob: ArrayLike):
    assert np.size(y_true) == np.size(y_prob), (
        "Length of y_true and y_pred should be the same."
    )
    y_pred = np.round(np.asarray(y_prob))

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, normalize="all").ravel()
    print(f"Total: {np.size(y_true)} (correct: {tp + fn}, incorrect: {fp + tn})")

    print(f"TP: {tp:.4f}, FP: {fp:.4f}\n" + f"TN: {tn:.4f}, FN: {fn:.4f}")

    print(classification_report(y_true, y_pred, digits=4))
    print(f"ROC AUC Score: {roc_auc_score(y_true, y_prob):.4f}")
