import torch
import os
import json
import copy
import numpy as np


from pykt.models.sakt import SAKT
from pykt.models import init_model
from pykt.datasets.data_loader import KTDataset
from torch.utils.data import DataLoader
from typing import Tuple

from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score


class SAKTService:
    def __init__(self, ckpt_path, device="cpu"):
        self.device = device
        config = json.load(open("config.json"))
        data_config = json.load(open("./pykt-toolkit/configs/data_config.json"))

        emb_type = config["emb_type"]
        model_name = config["model_name"]
        dataset_name = config["dataset_name"]
        model_config = copy.deepcopy(config)

        for key in [
            "model_name",
            "dataset_name",
            "emb_type",
            "save_dir",
            "fold",
            "seed",
        ]:
            del model_config[key]

        print(f"model_config: {model_config}")
        print(f"data_config: {data_config[dataset_name]}")
        if model_name in ["dimkt"]:
            # del model_config['num_epochs']
            del model_config["weight_decay"]

        for remove_item in ["use_wandb", "learning_rate", "add_uuid", "l2"]:
            if remove_item in model_config:
                del model_config[remove_item]

        if model_name in [
            "saint",
            "saint++",
            "sakt",
            "atdkt",
            "simplekt",
            "stablekt",
            "datakt",
            "folibikt",
        ]:
            if "maxlen" in data_config[dataset_name]:
                model_config["seq_len"] = data_config[dataset_name]["maxlen"]

        self.model = init_model(
            model_name, model_config, data_config[dataset_name], emb_type
        )
        if self.model is None:
            raise ValueError("Model initialization failed.")
        self.model.load_state_dict(torch.load(ckpt_path))
        self.model.to(self.device)
        self.model.eval()

    def predict_data(self, sequence) -> np.ndarray:
        # q: question, c: concept, r: response, t: timestaps
        q, c, r, t = (
            sequence["qseqs"],
            sequence["cseqs"],
            sequence["rseqs"],
            sequence["tseqs"],
        )

        # shifted sequences for next interaction prediction, shape is seqlen-1
        qshft, cshft, rshft, tshft = (
            sequence["shft_qseqs"],
            sequence["shft_cseqs"],
            sequence["shft_rseqs"],
            sequence["shft_tseqs"],
        )
        # m: mask, sm_mask: select_mask
        m, sm = sequence["masks"], sequence["smasks"]

        if self.model is None:
            raise ValueError("Model is not initialized.")
        with torch.no_grad():
            predictions = self.model(c.long(), r.long(), cshft.long())

        return predictions.cpu().numpy()

    def visualize_predictions(self, concept_ids, correctness, probabilities):
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd

        df = pd.DataFrame(
            {
                "concept_id": concept_ids,
                "correct": correctness,
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
            hue="correct",
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

    def get_ckpt_path(self, ckpt_path, emb_type):
        return os.path.join(ckpt_path, emb_type + "_model.ckpt")


def print_stats(y_true, y_prob):
    assert len(y_true) == len(y_prob), "Length of y_true and y_pred should be the same."
    y_pred = [1 if prob > 0.5 else 0 for prob in y_prob]

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, normalize="all").ravel()
    print(f"Total: {len(y_true)} (correct: {tp + fn}, incorrect: {fp + tn})")

    print(f"TP: {tp:.4f}, FP: {fp:.4f}\n" + f"TN: {tn:.4f}, FN: {fn:.4f}")

    print(classification_report(y_true, y_pred, digits=4))
    print(f"ROC AUC Score: {roc_auc_score(y_true, y_prob):.4f}")


def predict_data(
    service: SAKTService, dataloader: DataLoader, display_sequences: tuple
) -> tuple:
    y_true, y_prob = [], []
    counter = 0
    for sequence in dataloader:
        counter += 1

        should_display = display_sequences[0] < counter <= display_sequences[1]
        probabilities, correctness = predict_sequence(
            service, sequence, visualize=should_display
        )

        y_true.extend(correctness.tolist())
        y_prob.extend(probabilities.tolist())
    return y_true, y_prob


def predict_sequence(
    service: SAKTService, sequence: "dict[str, torch.Tensor]", visualize: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    mask = sequence["masks"].cpu().numpy()
    probabilities = service.predict_data(sequence)[mask]
    actual_responses = sequence["shft_rseqs"].cpu().numpy()[mask]

    if visualize:
        concept_ids = sequence["shft_cseqs"].cpu().numpy()[mask]
        # print(probabilities)
        # print(concept_ids)
        service.visualize_predictions(concept_ids, actual_responses, probabilities)

    return probabilities, actual_responses


def suggest_next(service: SAKTService, sequence: "dict[str, torch.Tensor]") -> float:
    # This uses concepts ids to suggest the next question
    concepts: np.ndarray = sequence["cseqs"].cpu().numpy()
    unique_concepts = np.unique(concepts[concepts != 0])

    mask = sequence["masks"].cpu().numpy()
    id_of_next = mask.sum()

    test_sequence = copy.deepcopy(sequence)

    scores = []
    for concept in unique_concepts:
        additions = 3
        for k in range(additions):
            insert_entry(test_sequence, id_of_next + k, c=concept, r=1)

        probabilities = service.predict_data(test_sequence)[0]
        score = (probabilities[id_of_next + additions] - probabilities[id_of_next]) * np.prod(probabilities[id_of_next:id_of_next + additions])
        scores.append((concept, score))

    for concept, score in scores:
        print(f"{concept}: {score:.3f}", end=", ")
    print()
    return max(scores, key=lambda x: x[1])[0]



def insert_entry(
    sequence: "dict[str, torch.Tensor]", entry_idx: int, **kwargs
) -> "dict[str, torch.Tensor]":
    shiftable_columns = ["q", "c", "r", "t", "ut"]

    for column in shiftable_columns:
        if column in kwargs.keys():
            insert_in_sequence(sequence, entry_idx, column + "seqs", kwargs[column])

    sequence["masks"][0][entry_idx] = True
    sequence["smasks"][0][entry_idx] = True

    return sequence


def insert_in_sequence(
    sequence: "dict[str, torch.Tensor]", entry_idx: int, key, new_value
):
    sequence[key][0][entry_idx] = sequence["shft_" + key][0][entry_idx - 1]
    sequence["shft_" + key][0][entry_idx] = new_value


if __name__ == "__main__":
    ckpt_path = "./pykt-toolkit/examples/saved_model/assist2015_sakt_qid_saved_model_42_0_0.2_256_0.001_2_1_0_0/qid_model.ckpt"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    service = SAKTService(ckpt_path, device)

    dataset = KTDataset(
        file_path="./pykt-toolkit/data/assist2015/test_sequences.csv",
        input_type="qid",
        folds=[-1],
    )
    dataloader = DataLoader(dataset, 1)

    # display_sequences = (60, 65)
    # y_true, y_prob = predict_data(service, dataloader, display_sequences)

    # print_stats(y_true, y_prob)

    counter = 0
    for sequence in dataloader:
        counter += 1
        if counter < 4:
            continue

        mask = sequence["masks"].cpu().numpy()[0]
        for key, value in sequence.items():
            value = value.cpu().numpy()[0]
            # print(key)
            # if len(value) > 0:
            #     print(value)
        next_concept = suggest_next(service, sequence)
        insert_entry(sequence, mask.sum(), c=next_concept, r=1)
        insert_entry(sequence, mask.sum()+1, c=next_concept, r=1)

        print("next concept:", next_concept)
        predict_sequence(service, sequence, True)
        break
