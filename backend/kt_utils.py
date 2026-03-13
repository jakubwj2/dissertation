import torch
import numpy as np

from numpy.typing import ArrayLike
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score


def insert_entry(
    sequence: "dict[str, torch.Tensor]", entry_idx: int, **kwargs
) -> "dict[str, torch.Tensor]":
    shiftable_columns = ["q", "c", "r", "t", "ut"]

    for column in shiftable_columns:
        if column in kwargs.keys():
            key = column + "seqs"
            sequence[key][0][entry_idx] = sequence["shft_" + key][0][entry_idx - 1]
            sequence["shft_" + key][0][entry_idx] = kwargs[column]

    sequence["masks"][0][entry_idx] = True
    sequence["smasks"][0][entry_idx] = True

    return sequence


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


def visualize_predictions(
    sequence: dict[str, torch.Tensor], probabilities: np.ndarray
) -> None:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    mask = sequence["masks"].cpu().numpy()

    actual_responses = sequence["shft_rseqs"].cpu().numpy()[mask]
    concept_ids = sequence["shft_cseqs"].cpu().numpy()[mask]
    probabilities = probabilities[mask]

    df = pd.DataFrame(
        {
            "concept_id": concept_ids,
            "actual_responses": actual_responses,
            "probabilities": probabilities,
        }
    )
    sorted_concepts = sorted(df["concept_id"].unique(), key=lambda x: int(x))

    plt.figure(figsize=(16, 10))
    sns.lineplot(
        df,
        x=df.index,
        y="probabilities",
        hue="concept_id",
        hue_order=sorted_concepts,
        palette="tab10",
    )
    sns.scatterplot(
        df,
        x=df.index,
        y="probabilities",
        hue="actual_responses",
        palette={True: "lime", False: "red"},
        marker="o",
        s=50,
        legend=False,
    )
    plt.xlabel("Attempt Index")
    plt.ylabel("Predicted Probability of Correctness")

    num_concepts = len(concept_ids)
    sns.lineplot(
        x=[-num_concepts * 0.1, num_concepts * 1.1],
        y=[0.5, 0.5],
        color="gray",
        linestyle="--",
    )

    plt.axis(ymin=0, ymax=1)
    plt.legend(loc="lower right")
    plt.title("Probabilities for One Example")
    plt.show()
