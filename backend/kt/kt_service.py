from __future__ import annotations

import copy

import numpy as np
import torch
from pykt.models import init_model
from pykt.models.akt import AKT
from pykt.models.atdkt import ATDKT
from pykt.models.atkt import ATKT
from pykt.models.cskt import CSKT
from pykt.models.datakt import BAKTTime
from pykt.models.deep_irt import DeepIRT
from pykt.models.dimkt import DIMKT
from pykt.models.dkt import DKT
from pykt.models.dkt_forget import DKTForget
from pykt.models.dkt_plus import DKTPlus
from pykt.models.dkvmn import DKVMN
from pykt.models.dtransformer import DTransformer
from pykt.models.extrakt import extraKT
from pykt.models.folibikt import folibiKT
from pykt.models.gkt import GKT
from pykt.models.hawkes import HawkesKT
from pykt.models.hcgkt import HCGKT
from pykt.models.iekt import IEKT
from pykt.models.kqn import KQN
from pykt.models.lefokt_akt import LEFOKT_AKT
from pykt.models.lpkt import LPKT
from pykt.models.qdkt import QDKT
from pykt.models.qikt import QIKT
from pykt.models.rekt import ReKT
from pykt.models.rkt import RKT
from pykt.models.robustkt import Robustkt
from pykt.models.saint import SAINT
from pykt.models.sakt import SAKT
from pykt.models.simplekt import simpleKT
from pykt.models.skvmn import SKVMN
from pykt.models.sparsekt import sparseKT
from pykt.models.stablekt import stableKT
from pykt.models.ukt import UKT
from torch.nn import Module
from torch.nn.functional import one_hot

from config import Checkpoint, CnfDict, Settings
from kt.constants import DEVICE, SEQ_LEN_MODELS
from kt.sequence import Sequence
from models.problem_log import ProblemLog

DEFAULT_CHECKPOINT = "simplekt_smart_tutor"


class KTService:
    def __init__(
        self,
        device: str,
        ckpt_cnf: CnfDict,
        service_cnf: CnfDict,
        seq_len: int,
        keyid2idx: CnfDict,
        model: torch.nn.Module,
    ):
        self.device = device
        self.ckpt_cnf = ckpt_cnf
        self.service_cnf = service_cnf
        self.seq_len = seq_len
        self.keyid2idx = keyid2idx
        self.model = model

        self.dataset_name = ckpt_cnf["params"]["dataset_name"]
        self.model_name = ckpt_cnf["params"]["model_name"]
        self.num_concepts = ckpt_cnf["data_config"]["num_c"]
        self.additions = service_cnf["num_additions"]

    @classmethod
    def create(cls, device: str, ckpt: Checkpoint, service_cnf: CnfDict) -> KTService:
        model_name = ckpt.config["params"]["model_name"]
        model_config = ckpt.config["model_config"]

        # Parse model_config, this fixes an issue with pykt
        seq_len = ckpt.get_seq_len()
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
        return KTService(
            device, ckpt.config, service_cnf, seq_len, ckpt.keyid2idx, model
        )

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

        if self.model is None:
            raise ValueError("Model is not initialized.")

        for k in sequence:
            sequence[k].to(self.device)

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

        model = self.model
        dcur = sequence  # TODO: this is a temporary fix, adjust the model forward function to take in the sequence directly

        with torch.no_grad():
            ## Copied from pykt/models/train_model.py and adjusted
            ys: torch.Tensor | None = None
            cq = torch.cat((q[:, 0:1], qshft), dim=1)
            cc = torch.cat((c[:, 0:1], cshft), dim=1)
            cr = torch.cat((r[:, 0:1], rshft), dim=1)

            if isinstance(model, RKT):
                raise NotImplementedError("RKT prediction is not implemented yet.")
            elif isinstance(model, ATDKT):
                y = model(dcur, train=False)
                if (
                    model.emb_type.find("bkt") == -1
                    and model.emb_type.find("addcshft") == -1
                ):
                    y = (y * one_hot(cshft.long(), model.num_c)).sum(-1)
                ys = y
            elif isinstance(model, sparseKT):
                y, _ = model(dcur, train=False)
                ys = y[:, 1:]
            elif isinstance(model, (simpleKT, stableKT, CSKT)):
                y = model(dcur, train=False)
                ys = y[:, 1:]
            elif isinstance(model, ReKT):
                y = model(dcur, train=False)
                ys = y
            elif isinstance(model, UKT):
                y = model(dcur, train=False)
                ys = y
            elif isinstance(model, HCGKT):
                raise NotImplementedError("HCGKT prediction is not implemented yet.")
            elif isinstance(model, BAKTTime):
                raise NotImplementedError("BAKTTime prediction is not implemented yet.")
            elif isinstance(model, DKT):
                y = model(c.long(), r.long())
                y = (y * one_hot(cshft.long(), model.num_c)).sum(-1)
                ys = y
            elif isinstance(model, DKTPlus):
                y = model(c.long(), r.long())
                ys = y
            elif isinstance(model, DKTForget):
                raise NotImplementedError(
                    "DKTForget prediction is not implemented yet."
                )
            elif isinstance(model, (DKVMN, DeepIRT, SKVMN)):
                y = model(cc.long(), cr.long())
                ys = y[:, 1:]
            elif isinstance(model, (KQN, SAKT)):
                y = model(c.long(), r.long(), cshft.long())
                ys = y
            elif isinstance(model, SAINT):
                y = model(cq.long(), cc.long(), r.long())
                ys = y[:, 1:]
            elif isinstance(
                model,
                # ["akt_vector", "akt_norasch", "akt_mono", "akt_attn", "aktattn_pos", "aktmono_pos", "akt_raschx", "akt_raschy", "aktvec_raschx", "fluckt"]:
                (AKT, extraKT, folibiKT, Robustkt, LEFOKT_AKT, DTransformer),
            ):
                y, reg_loss = model(cc.long(), cr.long(), cq.long())
                ys = y[:, 1:]
            elif isinstance(model, (ATKT)):  # both ATKT and ATKTfix
                y, features = model(c.long(), r.long())
                y = (y * one_hot(cshft.long(), model.num_c)).sum(-1)
                ys = y
            elif isinstance(model, GKT):
                y = model(cc.long(), cr.long())
                ys = y
            elif isinstance(model, LPKT):
                cit = torch.cat((dcur["itseqs"][:, 0:1], dcur["shft_itseqs"]), dim=1)
                y = model(cq.long(), cr.long(), cit.long())
                ys = y[:, 1:]
            elif isinstance(model, HawkesKT):
                ct = torch.cat((t[:, 0:1], tshft), dim=1)
                y = model(cc.long(), cq.long(), ct.long(), cr.long())
                ys = y[:, 1:]
            elif isinstance(model, (IEKT, QDKT, QIKT)):
                y, loss = model.train_one_step(dcur)
                ys = y[:, 1:]
            elif isinstance(model, DIMKT):
                raise NotImplementedError("DIMKT prediction is not implemented yet.")
            if ys is None or not isinstance(ys, torch.Tensor):
                raise ValueError("Model output is not a tensor.", type(ys))
            return ys.cpu().numpy()

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
            "tseqs": [
                int(log.submission_time.timestamp() * 1000) for log in problem_logs
            ],
            "utseqs": [int(log.response_time * 1000) for log in problem_logs],  # type: ignore
        }

        questions = self.keyid2idx.get("questions")
        if questions is not None:
            members["qseqs"] = [questions.get(str(q), 0) for q in members["qseqs"]]

        concepts = self.keyid2idx.get("concepts")
        if concepts is not None:
            members["cseqs"] = [concepts.get(str(c), 0) for c in members["cseqs"]]

        def to_tensor(
            value: np.ndarray | list,
            device: str,
            padding: np.ndarray,
            dtype: torch.dtype,
        ):
            seq = np.concatenate([value, padding])
            return torch.from_numpy(seq).to(device, dtype=dtype).unsqueeze(0)

        result = Sequence()
        current_len = min(max(0, len(problem_logs) - 1), self.seq_len - 1)
        padding = -np.zeros(self.seq_len - current_len - 1)  # -1 for the last response
        for key, value in members.items():
            dtype = torch.float32 if key in ["rseqs"] else torch.long
            result[key] = to_tensor(value[:-1], self.device, padding, dtype)
            result["shft_" + key] = to_tensor(value[1:], self.device, padding, dtype)

        mask = np.ones(current_len, dtype=bool)
        result["masks"] = to_tensor(mask, self.device, padding, torch.bool)
        result["smasks"] = to_tensor(mask, self.device, padding, torch.bool)

        return result

    def suggest_next(self, sequence: Sequence) -> str:
        """Suggest the next concept based on the concepts and responses in the sequence

        Arguments:
            sequence {Sequence} -- User KT sequence

        Returns:
            str Suggestion concept ID
        """

        id_of_next = sequence["masks"].cpu().numpy().sum()

        scores = []

        concepts = self.keyid2idx.get("concepts")
        if concepts is None:
            raise ValueError("Concepts not found in keyid2idx.")

        # TODO: Select only relevant concepts to improve performance
        for concept_key, concept_value in concepts.items():
            test_sequence = copy.deepcopy(sequence)
            for _ in range(self.additions):
                test_sequence.insert_next_entry(c=concept_value, r=1)

            probabilities = self.predict_sequence(test_sequence)[0]
            score = (
                probabilities[id_of_next + self.additions] - probabilities[id_of_next]
            ) * np.prod(probabilities[id_of_next : id_of_next + self.additions])
            scores.append((concept_key, score))

        question_id = max(scores, key=lambda x: x[1])[0]

        return str(question_id)
