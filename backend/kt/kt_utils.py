from __future__ import annotations

from typing import NotRequired, TypedDict, Unpack

import numpy as np
import torch
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


def get_seq_len(ckpt_cnf):
    seq_len = ckpt_cnf["train_config"]["seq_len"]
    if "maxlen" in ckpt_cnf["data_config"]:
        seq_len = ckpt_cnf["data_config"]["maxlen"]
    return seq_len
