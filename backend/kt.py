import torch
import json
import copy
import numpy as np
from pykt.models import init_model
from pykt.datasets.data_loader import KTDataset


from kt_utils import visualize_predictions, insert_entry


CONFIG_PATH = "config.json"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class KTService:
    def __init__(self, config_path, device):
        self.device = device
        config = json.load(open(config_path))

        data_config = json.load(open("./pykt-toolkit/configs/data_config.json"))

        emb_type = config["emb_type"]
        model_name = config["model_name"]
        dataset_name = config["dataset_name"]
        model_config = copy.deepcopy(config)
        # TODO: check that file exists and train one if not
        ckpt_path = config["check_point_path"][model_name + "_" + dataset_name]

        # TODO: this could be a whitelist, although this requires checking all kt models
        for key in [
            "model_name",
            "dataset_name",
            "emb_type",
            "save_dir",
            "fold",
            "seed",
            "check_point_path",
        ]:
            del model_config[key]

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

    def predict_sequence(self, sequence: dict[str, torch.Tensor]) -> np.ndarray:
        """Get the predictions for the sequence

        Arguments:
            sequence {dict[str, torch.Tensor]} -- User KT sequence

        Raises:
            ValueError: Raises value error when the model is not initialized

        Returns:
            np.ndarray -- A seqlen array of predictions
        """
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

    def suggest_next(self, sequence: dict[str, torch.Tensor]) -> int:
        """Suggest the next concept based on the concepts and responses in the sequence

        Arguments:
            sequence {dict[str, torch.Tensor]} -- User KT sequence 

        Returns:
            int Suggestion concept ID
        """            
        
        concepts = sequence["cseqs"].cpu().numpy()
        unique_concepts = np.unique(concepts[concepts != 0])

        mask = sequence["masks"].cpu().numpy()
        id_of_next = mask.sum()

        test_sequence = copy.deepcopy(sequence)

        scores = []
        for concept in unique_concepts:
            additions = 3
            for k in range(additions):
                insert_entry(test_sequence, id_of_next + k, c=concept, r=1)

            probabilities = self.predict_sequence(test_sequence)[0]
            score = (
                probabilities[id_of_next + additions] - probabilities[id_of_next]
            ) * np.prod(probabilities[id_of_next : id_of_next + additions])
            scores.append((concept, score))

        for concept, score in scores:
            print(f"{concept}: {score:.3f}", end=", ")
        print()
        return max(scores, key=lambda x: x[1])[0]


if __name__ == "__main__":
    service = KTService(CONFIG_PATH, DEVICE)

    dataset = KTDataset(
        file_path="./pykt-toolkit/data/assist2015/test_sequences.csv",
        input_type="qid",
        folds=[-1],
    )
    
    sequence: dict[str, torch.Tensor] = dataset[3] # type: ignore
    # data is usually trained on batches
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
    # print_stats(sequence["rseqs"].cpu().numpy()[mask], probabilities[mask])
