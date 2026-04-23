from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import torch

from .constants import DATASET_DIR
from .types import CnfDict


@dataclass
class Checkpoint:
    path: Path
    config: CnfDict
    state: OrderedDict
    keyid2idx: CnfDict
    question_concepts_lookup: CnfDict

    @classmethod
    def from_dir(cls, dir_path: Path) -> Checkpoint:
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Checkpoint directory {dir_path} does not exist")

        ckpt_files = sorted(dir_path.glob("*.ckpt"))
        cnf_files = sorted(dir_path.glob("*.json"))

        if len(ckpt_files) != 1 or len(cnf_files) != 1:
            raise ValueError(
                f"Checkpoint directory {dir_path} does not contain checkpoint or config"
            )

        with ckpt_files[0].open("rb") as fin:
            checkpoint = torch.load(fin, map_location="cpu")

        with cnf_files[0].open("r", encoding="utf-8") as fin:
            config = json.load(fin)

        params = config.get("params")
        req_params = ["dataset_name", "model_name"]
        if params is None or not all(req_param in params for req_param in req_params):
            raise ValueError(
                f"Checkpoint directory {dir_path} does not contain correct config params"
            )

        dataset_name = params["dataset_name"]
        keyid2idx_path = DATASET_DIR / dataset_name / "keyid2idx.json"
        if not keyid2idx_path.exists():
            raise ValueError(f"Keyid2idx file {keyid2idx_path} does not exist")

        with keyid2idx_path.open("r", encoding="utf-8") as fin:
            keyid2idx = json.load(fin)

        question_concept_path = DATASET_DIR / dataset_name / "question_concepts.json"

        if not question_concept_path.exists():
            question_concepts = Checkpoint.create_question_concepts(
                dataset_name, keyid2idx
            )
        else:
            with question_concept_path.open("r", encoding="utf-8") as fin:
                question_concepts = json.load(fin)

        return Checkpoint(dir_path, config, checkpoint, keyid2idx, question_concepts)

    @classmethod
    def create_ckpt_name(cls, model_name: str, dataset_name: str) -> str:
        return model_name + "_" + dataset_name

    @property
    def dataset_name(self) -> str:
        return self.config["params"]["dataset_name"]

    @property
    def model_name(self) -> str:
        return self.config["params"]["model_name"]

    @property
    def name(self) -> str:
        return Checkpoint.create_ckpt_name(self.model_name, self.dataset_name)

    def get_seq_len(self) -> int:
        seq_len = self.config["train_config"]["seq_len"]
        if "maxlen" in self.config["data_config"]:
            seq_len = self.config["data_config"]["maxlen"]
        return seq_len

    @classmethod
    def create_question_concepts(
        cls, dataset_name: Path, keyid2idx: CnfDict
    ) -> CnfDict:
        dataset_path = DATASET_DIR / dataset_name / "data.txt"
        concept_map: CnfDict | None = keyid2idx.get("concepts")
        question_map: CnfDict | None = keyid2idx.get("questions")

        if concept_map is None or question_map is None:
            raise ValueError("Concepts or questions not found in keyid2idx.")

        questions_concepts = {}
        with dataset_path.open("r", encoding="utf-8") as fin:
            lines = fin.readlines()

            for i in range(0, len(lines), 6):
                student_concepts = lines[i + 2].strip().split(",")
                student_questions = lines[i + 1].strip().split(",")

                for q, c in zip(student_questions, student_concepts):
                    q_idx = question_map.get(q)
                    c_idx = concept_map.get(c)

                    if q_idx is None:
                        raise Exception(f"Question {q} not found in keyid2idx.")

                    if c_idx is None:
                        raise Exception(f"Concept {c} not found in keyid2idx.")

                    if q_idx not in questions_concepts:
                        questions_concepts[q_idx] = [c_idx]
                    else:
                        questions_concepts[q_idx].append(c_idx)

        return questions_concepts
