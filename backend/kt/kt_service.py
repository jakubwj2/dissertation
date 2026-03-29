import torch
import json
import copy
import numpy as np
from pykt.models import init_model


from kt.kt_utils import insert_next_entry, Sequence
from models.problem_log import ProblemLog


CONFIG_PATH = "config.json"
MODEL_CONFIG_PATH = "model_configs.json"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

DATA_CONFIG_PATH = "./pykt-toolkit/configs/data_config.json"
# TODO: move this to the config file
ADDITIONS = 3


class KTService:
    def __init__(self, config_path: str, device: str):
        self.device = device
        self.config = json.load(open(config_path))
        self.data_config = json.load(open(DATA_CONFIG_PATH))
        model_configs = json.load(open(MODEL_CONFIG_PATH))

        emb_type = self.config["emb_type"]
        model_name = self.config["model_name"]
        dataset_name = self.config["dataset_name"]

        model_config = model_configs[model_name]["model_config"]

        ckpt_path = self.config["check_point_path"][model_name + "_" + dataset_name]

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
            if "maxlen" in self.data_config[dataset_name]:
                model_config["seq_len"] = self.data_config[dataset_name]["maxlen"]

        self.model = init_model(
            model_name, model_config, self.data_config[dataset_name], emb_type
        )
        if self.model is None:
            raise ValueError("Model initialization failed.")
        self.model.load_state_dict(torch.load(ckpt_path))
        self.model.to(self.device)
        self.model.eval()

    def predict_sequence(self, sequence: Sequence) -> np.ndarray:
        """Get the predictions for the sequence

        Arguments:
            sequence {Sequence} -- User KT sequence

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

    def preprocess_data(self, problem_logs: list[ProblemLog]) -> Sequence:
        """preprocesses data from the backend

        Returns:
            Sequence -- fold,uid,concepts,responses,selectmasks,cidxs
        """
        # TODO https://github.com/pykt-team/pykt-toolkit/blob/main/docs/source/contribute.md

        # self.log_id,
        # self.student_id,
        # self.correct,
        # self.skill_id,
        # self.submission_time,
        # self.response_time,
        # self.question_id,

        # q: question, c: concept, r: response, t: timestaps

        # shifted sequences for next interaction prediction, shape is seqlen-1
        # m: mask, sm_mask: select_mask

        dataset_name = self.config["dataset_name"]
        seq_len = self.data_config[dataset_name]["maxlen"]

        members = {
            "qseqs": [log.question_id for log in problem_logs],
            "cseqs": [log.skill_id for log in problem_logs],
            "rseqs": [log.correct for log in problem_logs],
            "tseqs": [log.response_time for log in problem_logs],
        }

        def to_tensor(
            value: list | np.ndarray, device: str, padding: list | np.ndarray
        ):
            return torch.tensor(np.concat([value, padding])).unsqueeze(0).to(device)

        result: Sequence = {}
        current_len = max(0, len(problem_logs) - 1)
        padding = -np.zeros(seq_len - current_len)
        for key, value in members.items():
            result[key] = to_tensor(value[:-1], self.device, padding)
            result["shft_" + key] = to_tensor(value[1:], self.device, padding)

        result["masks"] = to_tensor(np.ones(current_len), self.device, padding).bool()
        result["smasks"] = to_tensor(np.ones(current_len), self.device, padding).bool()

        return result

    def suggest_next(self, sequence: Sequence) -> int:
        """Suggest the next concept based on the concepts and responses in the sequence

        Arguments:
            sequence {Sequence} -- User KT sequence

        Returns:
            int Suggestion concept ID
        """

        id_of_next = sequence["masks"].cpu().numpy().sum()

        scores = []
        num_concepts = self.data_config[self.config["dataset_name"]]["num_c"]
        for concept in range(num_concepts):
            test_sequence = copy.deepcopy(sequence)
            for k in range(ADDITIONS):
                insert_next_entry(test_sequence, c=concept, r=1)

            probabilities = self.predict_sequence(test_sequence)[0]
            score = (
                probabilities[id_of_next + ADDITIONS] - probabilities[id_of_next]
            ) * np.prod(probabilities[id_of_next : id_of_next + ADDITIONS])
            scores.append((concept, score))

        question_id = max(scores, key=lambda x: x[1])[0]
        return question_id
