from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any
import torch
from collections import OrderedDict

CONFIG_NAME = "config.json"
CONFIG_PATH = Path(__file__).with_name(CONFIG_NAME)


@dataclass
class Checkpoint:
    name: str
    path: Path
    config: dict[str, Any]
    state: OrderedDict

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

        try:
            dataset_name = config["params"]["dataset_name"]
            model_name = config["params"]["model_name"]
            name = model_name + "_" + dataset_name
        except KeyError:
            raise ValueError(
                f"Checkpoint directory {dir_path} does not contain correct config params"
            )
    
        checkpoint_dir = Checkpoint(name, dir_path, config, checkpoint)

        return checkpoint_dir


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
