import argparse
import copy
import os

import matplotlib.pyplot as plt
from pykt.datasets.data_loader import KTDataset
from shared.visualisation import visualize_predictions

from config import DATASET_DIR, Checkpoint, Settings
from kt.kt_service import KTService
from kt.sequence import Sequence

FIGURE_DIR = "/mnt/c/Users/jakub/Pictures/kt_figures/"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-index", type=int, default=0)
    return parser.parse_args()


def validate_args(args: argparse.Namespace):
    if args.sequence_index < 0:
        raise ValueError(f"Invalid sequence index: {args.sequence_index}")


def single_sequence_demo(dataset: KTDataset, service: KTService, sequence_idx: int):
    sequence_raw = Sequence.from_dict(dataset[sequence_idx])  # type: ignore

    sequence = copy.deepcopy(sequence_raw)
    for k, v in sequence.items():
        sequence[k] = v.unsqueeze(0)

    next_concept = service.suggest_next(sequence)
    next_concept = service.keyid2idx["concepts"][next_concept]
    sequence.insert_next_entry(c=next_concept, r=1)
    sequence.insert_next_entry(c=next_concept, r=1)
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

    os.makedirs(FIGURE_DIR, exist_ok=True)
    id = len(os.listdir(FIGURE_DIR))

    fig.tight_layout()
    plt.savefig(f"{FIGURE_DIR}fig_{id}.png")
    plt.show(block=True)


if __name__ == "__main__":
    args = parse_args()
    validate_args(args)

    settings = Settings.load()
    ckpt_name = Checkpoint.create_ckpt_name("simplekt", "smart_tutor")
    ckpt = settings.checkpoints[ckpt_name]

    dataset_name: str = ckpt.config["params"]["dataset_name"]
    test_file: str = ckpt.config["data_config"]["test_file"]

    test_file_path = DATASET_DIR / dataset_name / test_file
    if not test_file_path.exists():
        raise ValueError(
            f"Model initialization failed. Test file {test_file_path} not found."
        )

    dataset = KTDataset(str(test_file_path), ["concepts"], [-1])
    kt_service = KTService.create_from_ckpt(settings)

    single_sequence_demo(dataset, kt_service, args.sequence_index)
