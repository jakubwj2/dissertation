from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

CONFIG_PATH = Path(__file__).with_name("config.json")
DATASET_DIR = Path("./pykt-toolkit/data")

CnfDict = dict[str, Any]


@dataclass
class Checkpoint:
    path: Path
    config: dict[str, Any]
    state: OrderedDict
    keyid2idx: dict[str, Any]

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

        keyid2idx_path = DATASET_DIR / params["dataset_name"] / "keyid2idx.json"
        if not keyid2idx_path.exists():
            raise ValueError(f"Keyid2idx file {keyid2idx_path} does not exist")

        with keyid2idx_path.open("r", encoding="utf-8") as fin:
            keyid2idx = json.load(fin)

        return Checkpoint(dir_path, config, checkpoint, keyid2idx)

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


@dataclass
class Settings:
    service_config: dict[str, Any]
    models_dir: Path
    checkpoints: dict[str, Checkpoint]

    @classmethod
    def from_config(cls, config_path: Path) -> Settings:
        with config_path.open() as f:
            data = json.load(f)

        service_config = data["service_config"]
        models_dir = Path(data["models_dir"])

        models: dict[str, Checkpoint] = {}
        for model_dir in models_dir.iterdir():
            if not model_dir.is_dir():
                continue
            ckpt_dir = Checkpoint.from_dir(model_dir)
            if ckpt_dir.name in models:
                raise ValueError(f"Duplicate model key: {ckpt_dir.name}")
            models[ckpt_dir.name] = ckpt_dir
        return Settings(service_config, models_dir, models)


def load_settings(config_path: Path = CONFIG_PATH) -> Settings:
    return Settings.from_config(config_path)


if __name__ == "__main__":
    settings = load_settings()
    for model_name in settings.checkpoints:
        print(model_name)
