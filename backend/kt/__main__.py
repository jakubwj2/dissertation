import torch
from pykt.datasets.data_loader import KTDataset
import matplotlib.pyplot as plt

from kt.kt_service import KTService, CONFIG_PATH, DEVICE
from kt.kt_utils import visualize_predictions, insert_entry


if __name__ == "__main__":
    service = KTService(CONFIG_PATH, DEVICE)

    dataset = KTDataset(
        file_path="./pykt-toolkit/data/assist2015/test_sequences.csv",
        input_type="qid",
        folds=[-1],
    )

    sequence: dict[str, torch.Tensor] = dataset[3]  # type: ignore
    
    # unsqeezing the sequence makes it into a batch of 1
    for keys in sequence.keys():
        sequence[keys] = sequence[keys].unsqueeze(0)

    mask = sequence["masks"].cpu().numpy()
    next_concept = service.suggest_next(sequence)
    insert_entry(sequence, mask.sum(), c=next_concept, r=1)
    insert_entry(sequence, mask.sum() + 1, c=next_concept, r=1)
    print("next concept:", next_concept)

    probabilities = service.predict_sequence(sequence)

    visualize_predictions(sequence, probabilities)
    plt.tight_layout()
    plt.show()
    # print_stats(sequence["rseqs"].cpu().numpy()[mask], probabilities[mask])
