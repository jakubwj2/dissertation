from pykt.datasets.data_loader import KTDataset
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
import copy
import os

from kt.kt_service import KTService
from kt.kt_utils import visualize_predictions, insert_next_entry, Sequence


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-path", default="./pykt-toolkit/data/assist2015/test_sequences.csv"
    )
    parser.add_argument("--sequence-index", type=int, default=3)
    return parser.parse_args()


def validate_args(args: argparse.Namespace):
    if not Path(args.data_path).is_file():
        raise ValueError(f"Dataset file not found: {args.data_path}")

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


if __name__ == "__main__":
    args = parse_args()
    validate_args(args)

    kt_service = KTService.create_from_ckpt_dir()

    dataset = KTDataset(file_path=args.data_path, input_type="qid", folds=[-1])

    single_sequence_demo(dataset, kt_service, args.sequence_index)
