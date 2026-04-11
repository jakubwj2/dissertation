from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .checkpoint import Checkpoint
from .constants import CONFIG_PATH
from .types import CnfDict


@dataclass
class Settings:
    service_config: CnfDict
    models_dir: Path
    checkpoints: dict[str, Checkpoint]

    @classmethod
    def load(cls, config_path: Path = CONFIG_PATH) -> Settings:
        with config_path.open() as f:
            data = json.load(f)

        service_config = data["service_config"]
        models_dir = Path(data["models_dir"])

        models: dict[str, Checkpoint] = {}
        for model_dir in models_dir.iterdir():
            if not model_dir.is_dir():
                continue
            try:
                Checkpoint.from_dir(model_dir)
            except ValueError:
                continue
            ckpt_dir = Checkpoint.from_dir(model_dir)
            if ckpt_dir.name in models:
                raise ValueError(f"Duplicate model key: {ckpt_dir.name}")
            models[ckpt_dir.name] = ckpt_dir
        return Settings(service_config, models_dir, models)


if __name__ == "__main__":
    settings = Settings.load()
    for model_name in settings.checkpoints:
        print(model_name)
