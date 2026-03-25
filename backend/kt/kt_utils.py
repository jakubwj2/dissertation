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
    from matplotlib.lines import Line2D
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
    df["concept_id"] = df["concept_id"].astype(int)
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
    ax = sns.scatterplot(
        df,
        x=df.index,
        y="probabilities",
        hue="actual_responses",
        palette={True: "lime", False: "red"},
        marker="o",
        s=75,
        legend=False,
    )

    handle_config = {
        "xdata": [],
        "ydata": [],
        "marker": "o",
        "linestyle": "None",
        "markersize": 10,
    }
    leg1 = ax.legend(
        handles=[
            Line2D(color="lime", label="Correct", **handle_config),
            Line2D(color="red", label="Incorrect", **handle_config),
        ],
        loc="lower right",
        title="Responses",
        title_fontsize=20,
        fontsize=12,
        bbox_to_anchor=(0.85, 0),
    )
    ax.add_artist(leg1)

    num_concepts = len(concept_ids)
    sns.lineplot(
        x=[-num_concepts * 0.025, num_concepts * 1.025],
        y=[0.5, 0.5],
        color="gray",
        linestyle="--",
    )

    plt.axis(ymin=0, ymax=1, xmin=-num_concepts * 0.05, xmax=num_concepts * 1.05)
    plt.xlabel("Attempt Index", fontsize=20)
    plt.ylabel("Predicted Mastery", fontsize=20)
    plt.legend(loc="lower right", title="Topic ID", title_fontsize=20, fontsize=12, ncol=2)
    plt.title("SAKT Predicted Mastery for One Student", size=35)
