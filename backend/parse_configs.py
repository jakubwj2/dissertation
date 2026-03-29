from dataclasses import dataclass, field
from io import TextIOWrapper
import os
from typing import Any
import json

META_ARGS = [
    "model_name",
    "dataset_name",
    "emb_type",
    "save_dir",
    "fold",
    "seed",
    "weight_decay",
    "use_wandb",
    "learning_rate",
    "add_uuid",
    "l2",
]

PARSE_DIR = "./pykt-toolkit/examples/"
OUTPUT_FILE = "model_configs.json"

MODELS_WITH_SEQ_LEN = [
    "saint",
    "saint++",
    "sakt",
    "atdkt",
    "simplekt",
    "stablekt",
    "datakt",
    "folibikt",
]


@dataclass
class Model:
    model_name: str
    model_config: dict[str, Any] = field(default_factory=dict)
    meta_args: dict[str, Any] = field(default_factory=dict)

    def add_argument(self, arg_name: str, arg_value: Any):
        if arg_name in META_ARGS:
            self.meta_args[arg_name] = arg_value
        else:
            self.model_config[arg_name] = arg_value


def parse_file(file_name: str, fin: TextIOWrapper, models: list[Model]):
    data = fin.read()
    # data = data.split("parser = argparse.ArgumentParser()")[1]
    # data = data.split("args = parser.parse_args()")[0]

    file_name = file_name.removeprefix("wandb_").removesuffix("_train.py")
    model = Model(file_name)
    for line in data.split("\n"):
        line = line.strip()

        #  remove comments
        line = line.split("#")[0]

        if line.startswith("parser.add_argument("):
            line = line.removeprefix("parser.add_argument(").removesuffix(")")
            args = line.split(",")
            arg_name = args[0] if len(args) >= 1 else None
            arg_type = args[1] if len(args) >= 2 else None
            default_value = args[2] if len(args) >= 3 else None

            if arg_name is None or arg_type is None:
                print(arg_name, arg_type)
                continue

            arg_name = arg_name.removeprefix('"--').removesuffix('"')
            arg_name = arg_name.removeprefix("'--").removesuffix("'")
            arg_type = arg_type.strip().removeprefix("type=").strip()

            if default_value is not None:
                default_value = default_value.strip().removeprefix("default=").strip()
                default_value = default_value.strip("'").strip('"').strip()

            has_default_value = default_value is not None

            if arg_type == "str2bool":
                default_value = False if default_value is None else bool(default_value)
            elif arg_type == "int":
                default_value = 0 if default_value is None else int(default_value)
            elif arg_type == "float":
                default_value = 0 if default_value is None else float(default_value)
            else:
                default_value = "" if default_value is None else default_value

            if not has_default_value:
                print(
                    f"Warning, {file_name}.{arg_name} doesn't have a default value. "
                    f"Auto setting to: {default_value}"
                )

            model.add_argument(arg_name, default_value)

    if (
        model.model_config.get("seq_len") is None
        and model.model_name in MODELS_WITH_SEQ_LEN
    ):
        # from pykt-toolkit/kt_config["train_config"]
        model.model_config["seq_len"] = 200
    models.append(model)


if __name__ == "__main__":
    models: list[Model] = []

    for file in os.listdir(PARSE_DIR):
        if (
            file.startswith("wandb_")
            and file.endswith("train.py")
            and file != "wandb_train.py"
        ):
            with open(PARSE_DIR + file, "r") as fin:
                parse_file(file, fin, models)

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as file:
            json_data = json.load(file)
    else:
        json_data = {}

    for model in models:
        found = False
        for data_model in json_data:
            if data_model == model.model_name:
                found = True
                json_data[data_model]["model_config"] = model.model_config
                # json_data[data_model]["meta_args"] = model.meta_args

        if not found:
            json_data[model.model_name] = {
                "model_config": model.model_config,
                # "meta_args": model.meta_args,
            }

    with open(OUTPUT_FILE, "w") as file:
        json.dump(json_data, file, indent=4)
