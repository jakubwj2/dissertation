from __future__ import annotations

import copy

import numpy as np
import torch
from pykt.models import init_model
from torch.nn import Module
from torch.nn.functional import one_hot

from config import Checkpoint, Settings
from kt.kt_utils import (
    DEVICE,
    QUE_TYPE_MODELS,
    SEQ_LEN_MODELS,
    CnfDict,
    Sequence,
    get_seq_len,
    insert_next_entry,
)
from models.problem_log import ProblemLog

DEFAULT_CHECKPOINT = "sakt_assist2015"


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
        self.model_name = ckpt_cnf["params"]["model_name"]
        self.num_concepts = ckpt_cnf["data_config"]["num_c"]
        self.additions = service_cnf["num_additions"]

    @classmethod
    def create(cls, device: str, ckpt: Checkpoint, service_cnf: CnfDict) -> KTService:
        model_name = ckpt.config["params"]["model_name"]
        model_config = ckpt.config["model_config"]

        # Parse model_config, this fixes an issue with pykt
        seq_len = get_seq_len(ckpt.config)
        for remove_item in ["use_wandb", "learning_rate", "add_uuid", "l2"]:
            if remove_item in model_config:
                del model_config[remove_item]
        if model_name in SEQ_LEN_MODELS:
            model_config["seq_len"] = seq_len
        if model_name in ["dimkt"]:
            del model_config["weight_decay"]

        emb_type = ckpt.config["params"]["emb_type"]
        data_cnf = ckpt.config["data_config"]
        model: Module = init_model(model_name, model_config, data_cnf, emb_type)

        if model is None:
            raise ValueError("Model initialization failed.")
        model.load_state_dict(ckpt.state)
        model.to(device)
        model.eval()
        return KTService(device, ckpt.config, service_cnf, model)

    @classmethod
    def create_from_ckpt(
        cls,
        settings: Settings,
        device: str = DEVICE,
        ckpt_name: str = DEFAULT_CHECKPOINT,
    ) -> KTService:
        ckpt = settings.checkpoints.get(ckpt_name)
        if ckpt is None:
            raise ValueError(f"Checkpoint {ckpt_name} not found!")

        return KTService.create(device, ckpt, settings.service_config)

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
            ## Copied from pykt/models/train_model.py and adjusted
            cq = torch.cat((q[:, 0:1], qshft), dim=1)
            cc = torch.cat((c[:, 0:1], cshft), dim=1)
            cr = torch.cat((r[:, 0:1], rshft), dim=1)
            if self.model_name in ["dkt"]:
                y = self.model(c.long(), r.long())
                y = (y * one_hot(cshft.long(), self.num_concepts)).sum(-1)
            elif self.model_name == "dkt+":
                y = self.model(c.long(), r.long())
            # elif self.model_name in ["dkt_forget"]:
            #     y = self.model(c.long(), r.long(), dgaps)
            #     y = (y * one_hot(cshft.long(), self.num_concepts)).sum(-1)
            elif self.model_name in ["dkvmn", "deep_irt", "skvmn"]:
                y = self.model(cc.long(), cr.long())[:, 1:]
            elif self.model_name in ["kqn", "sakt"]:
                y = self.model(c.long(), r.long(), cshft.long())
            elif self.model_name in ["saint"]:
                y = self.model(cq.long(), cc.long(), r.long())
            elif self.model_name in ["simplekt", "stablekt", "sparsekt", "cskt"]:
                y = self.model(sequence, train=False)
                y = y[:, 1:]
                # return np.array([y[:,1:], y2, y3])
            elif self.model_name in [
                "akt",
                "akt_vector",
                "akt_norasch",
                "akt_mono",
                "akt_attn",
                "aktattn_pos",
                "aktmono_pos",
                "akt_raschx",
                "akt_raschy",
                "aktvec_raschx",
            ]:
                y, reg_loss = self.model(cc.long(), cr.long(), cq.long())
            elif self.model_name in ["atkt", "atktfix"]:
                y, features = self.model(c.long(), r.long())
                y = (y * one_hot(cshft.long(), self.num_concepts)).sum(-1)
            elif self.model_name == "gkt":
                y = self.model(cc.long(), cr.long())
            # elif self.model_name == "lpkt":
            #     cit = torch.cat((dcur["itseqs"][:,0:1], dcur["shft_itseqs"]), dim=1)
            #     y = self.model(cq.long(), cr.long(), cit.long())
            elif self.model_name == "hawkes":
                ct = torch.cat((t[:, 0:1], tshft), dim=1)
                y = self.model(cc.long(), cq.long(), ct.long(), cr.long())
            elif self.model_name in QUE_TYPE_MODELS:
                from pykt.models.iekt import IEKT
                from pykt.models.qdkt import QDKT

                if not isinstance(self.model, (IEKT, QDKT)):
                    raise ValueError(f"Model {self.model_name} is not supported.")
                y, loss = self.model.train_one_step(sequence)  # this might not work
            else:
                raise ValueError(f"Model {self.model_name} is not supported.")
            return y.cpu().numpy()

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
        padding = -np.zeros(self.seq_len - current_len - 1)  # -1 for the last response
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
