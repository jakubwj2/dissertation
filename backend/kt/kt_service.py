from __future__ import annotations

import copy

import numpy as np
import torch
from pykt.models import init_model

from kt.kt_utils import Sequence, CnfDict, insert_next_entry, get_seq_len
from models.problem_log import ProblemLog

CONFIG_PATH = "config.json"
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


class KTService:
    def __init__(
        self,
        device: str,
        ckpt_cnf: CnfDict,
        service_cnf: CnfDict,
        model: torch.nn.Module,
    ):
        self.device = device
        self.ckpt_cnf = ckpt_cnf
        self.service_cnf = service_cnf
        self.model = model

        self.seq_len = get_seq_len(ckpt_cnf)
        self.dataset_name = ckpt_cnf["params"]["dataset_name"]
        self.num_concepts = ckpt_cnf["data_config"]["num_c"]
        self.additions = service_cnf["num_additions"]

    @classmethod
    def create(
        cls, device: str, ckpt_cnf: CnfDict, ckpt_path: str, service_cnf: CnfDict
    ) -> KTService:
        model_name = ckpt_cnf["params"]["model_name"]
        model_config = ckpt_cnf["model_config"]

        # Parse model_config, this fixes an issue with pykt
        seq_len = get_seq_len(ckpt_cnf)
        for remove_item in ["use_wandb", "learning_rate", "add_uuid", "l2"]:
            if remove_item in model_config:
                del model_config[remove_item]
        if model_name in SEQ_LEN_MODELS:
            model_config["seq_len"] = seq_len
        if model_name in ["dimkt"]:
            del model_config["weight_decay"]

        emb_type = ckpt_cnf["params"]["emb_type"]
        data_cnf = ckpt_cnf["data_config"]
        model = init_model(model_name, model_config, data_cnf, emb_type)

        if model is None:
            raise ValueError("Model initialization failed.")
        model.load_state_dict(torch.load(ckpt_path))
        model.to(device)
        model.eval()
        return KTService(device, ckpt_cnf, service_cnf, model)

    @classmethod
    def create_from_ckpt_dir(cls, device: str = DEVICE) -> KTService:
        import os
        import json

        if not os.path.exists(CONFIG_PATH):
            raise ValueError("Model initialization failed. No service config found.")
        main_cnf = json.load(open(CONFIG_PATH, "r"))
        service_cnf = main_cnf["service_config"]
        ckpt_dir = main_cnf["default_ckpt_dir"]

        if not os.path.exists(ckpt_dir):
            raise ValueError("Model initialization failed. No checkpoint found.")

        ckpt_path: str | None = None
        ckpt_cnf: dict | None = None
        for file in os.listdir(ckpt_dir):
            if file.endswith(".ckpt"):
                ckpt_path = os.path.join(ckpt_dir, file)

            if file.endswith(".json"):
                cnf_path = os.path.join(ckpt_dir, file)
                ckpt_cnf = json.load(open(cnf_path, "r"))

            if ckpt_path is not None and ckpt_cnf is not None:
                break

        if ckpt_path is None or ckpt_cnf is None:
            raise ValueError(
                "Model initialization failed. No checkpoint or config found."
            )

        return KTService.create(device, ckpt_cnf, ckpt_path, service_cnf)

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

        # log_id,student_id,correct,skill_id,submission_time,response_time,question_id,

        # q: question, c: concept, r: response, t: timestaps

        # shifted sequences for next interaction prediction, shape is seqlen-1
        # m: mask, sm_mask: select_mask

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
        padding = -np.zeros(self.seq_len - current_len)
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
        for concept in range(self.num_concepts):
            test_sequence = copy.deepcopy(sequence)
            for k in range(self.additions):
                insert_next_entry(test_sequence, c=concept, r=1)

            probabilities = self.predict_sequence(test_sequence)[0]
            score = (
                probabilities[id_of_next + self.additions] - probabilities[id_of_next]
            ) * np.prod(probabilities[id_of_next : id_of_next + self.additions])
            scores.append((concept, score))

        question_id = max(scores, key=lambda x: x[1])[0]
        return question_id
