from __future__ import annotations

from typing import NotRequired, TypedDict, Unpack

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from numpy.typing import ArrayLike
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from torch import Tensor


class ShiftableColumnsKwargs(TypedDict):
    q: NotRequired[int]
    c: NotRequired[int]
    r: NotRequired[float]
    t: NotRequired[int]
    ut: NotRequired[int]


Sequence = dict[str, Tensor]


QUE_TYPE_MODELS = ["iekt", "qdkt"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


SEQ_LEN_MODELS = [
    "saint",
    "saint++",
    "sakt",
    "atdkt",
    "simplekt",
    "stablekt",
    "datakt",
    "folibikt",
]


def insert_next_entry(
    sequence: Sequence, **kwargs: Unpack[ShiftableColumnsKwargs]
) -> Sequence:
    shiftable_columns = ["q", "c", "r", "t", "ut"]
    entry_idx = sequence["masks"].cpu().numpy().sum()
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
    responses: np.ndarray,
    ids: np.ndarray,
    probabilities: np.ndarray,
    mask: np.ndarray,
    dataset_name: str,
    model_name: str,
) -> Figure:
    assert responses.shape == ids.shape == probabilities.shape == mask.shape, (
        "Shapes don't match"
    )

    responses = responses[mask]
    ids = ids[mask]
    probabilities = probabilities[mask]

    df = pd.DataFrame(
        {"ids": ids, "responses": responses, "probabilities": probabilities}
    )
    df["ids"] = df["ids"].astype(int)
    sorted_concepts = sorted(df["ids"].unique(), key=lambda x: int(x))

    fig, ax = plt.subplots(figsize=(16, 10))

    # knowledge tracing lines
    sns.lineplot(
        data=df,
        x=df.index,
        y="probabilities",
        hue="ids",
        hue_order=sorted_concepts,
        palette="tab10",
        ax=ax,
        legend=False,
    )

    colors = sns.color_palette("tab10", len(sorted_concepts))
    handles = [
        Line2D([], [], color=color, linewidth=1.5, label=concept)
        for color, concept in zip(colors, sorted_concepts)
    ]

    leg1 = ax.legend(
        handles=handles,
        labels=sorted_concepts,
        loc="lower right",
        title="Topic ID",
        title_fontsize=20,
        fontsize=12,
        ncol=2,
    )
    ax.add_artist(leg1)

    # response markers
    sns.scatterplot(
        data=df,
        x=df.index,
        y="probabilities",
        hue="responses",
        palette={True: "lime", False: "red"},
        marker="o",
        s=75,
        legend=False,
        ax=ax,
    )

    handle_config = {
        "xdata": [],
        "ydata": [],
        "marker": "o",
        "linestyle": "None",
        "markersize": 10,
    }

    leg2 = ax.legend(
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
    # ax.add_artist(leg1)
    ax.add_artist(leg2)

    # mastery threshold line
    num_concepts = len(ids)
    sns.lineplot(
        x=[-num_concepts * 0.025, num_concepts * 1.025],
        y=[0.5, 0.5],
        color="gray",
        linestyle="--",
        ax=ax,
    )

    ax.set_ylim(0, 1)
    ax.set_xlim(-num_concepts * 0.05, num_concepts * 1.05)
    ax.set_ylabel("Predicted Mastery", fontsize=20)
    ax.set_xlabel("Attempt Index", fontsize=20)
    ax.set_title(
        f"Mastery for One Student ({model_name.upper()}, {dataset_name.upper()})",
        size=35,
    )

    return fig


def get_seq_len(ckpt_cnf):
    seq_len = ckpt_cnf["train_config"]["seq_len"]
    if "maxlen" in ckpt_cnf["data_config"]:
        seq_len = ckpt_cnf["data_config"]["maxlen"]
    return seq_len
