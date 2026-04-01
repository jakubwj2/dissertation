from pykt.datasets.data_loader import KTDataset
import matplotlib.pyplot as plt
import argparse
import copy
import os
import json

from kt.kt_service import KTService, CONFIG_PATH
from kt.kt_utils import visualize_predictions, insert_next_entry, Sequence


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-index", type=int, default=2)
    return parser.parse_args()


def validate_args(args: argparse.Namespace):
    if args.sequence_index < 0:
        raise ValueError(f"Invalid sequence index: {args.sequence_index}")


def single_sequence_demo(dataset: KTDataset, service: KTService, sequence_idx: int):
    sequence_raw: Sequence = dataset[sequence_idx]  # type: ignore

    sequence = copy.deepcopy(sequence_raw)
    for k, v in sequence.items():
        sequence[k] = v.unsqueeze(0)

    next_concept = service.suggest_next(sequence)
    insert_next_entry(sequence, c=next_concept, r=1)
    insert_next_entry(sequence, c=next_concept, r=1)
    print("next concept:", next_concept)

    probabilities = service.predict_sequence(sequence)
    mask = sequence["masks"].cpu().numpy()
    responses = sequence["shft_rseqs"].cpu().numpy()
    ids = sequence["shft_cseqs"].cpu().numpy()

    dataset_name = kt_service.dataset_name
    model_name = kt_service.model_name
    fig = visualize_predictions(
        responses, ids, probabilities, mask, dataset_name, model_name
    )

    dir = "/mnt/c/Users/jakub/Pictures/kt_figures/"
    os.makedirs(dir, exist_ok=True)
    id = len(os.listdir(dir))

    fig.tight_layout()
    plt.savefig(f"{dir}fig_{id}.png")
    plt.show(block=True)


def get_test_file_from_config() -> str:
    """Get test file path from main config

    Raises:
        ValueError: main config file not found
        ValueError: checkpoint directory not found
        ValueError: checkpoint config file not found

    Returns:
        str -- test dataset file path
    """
    if not os.path.exists(CONFIG_PATH):
        raise ValueError("Model initialization failed. No service config found.")
    main_cnf = json.load(open(CONFIG_PATH, "r"))
    ckpt_dir = main_cnf["default_ckpt_dir"]

    if not os.path.exists(ckpt_dir):
        raise ValueError("Model initialization failed. No checkpoint found.")

    ckpt_cnf: dict | None = None
    for file in os.listdir(ckpt_dir):
        if file.endswith(".json"):
            cnf_path = os.path.join(ckpt_dir, file)
            ckpt_cnf = json.load(open(cnf_path, "r"))

    if ckpt_cnf is None:
        raise ValueError("Model initialization failed. No config found.")

    dataset_name = ckpt_cnf["params"]["dataset_name"]
    test_file = ckpt_cnf["data_config"]["test_file"]

    test_file_path = os.path.join("./pykt-toolkit/data", dataset_name, test_file)
    return test_file_path


if __name__ == "__main__":
    args = parse_args()
    validate_args(args)

    dataset = KTDataset(get_test_file_from_config(), ["questions", "concepts"], [-1])
    kt_service = KTService.create_from_ckpt_dir()

    single_sequence_demo(dataset, kt_service, args.sequence_index)
