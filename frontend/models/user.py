import os
import json
from typing import Any

from models.user_type import UserType, user_type_parser
from utils.path_utils import get_config_path


class User:
    def __init__(self, id: int, username: str, email: str, user_type: UserType):
        self.id = id
        self.username = username
        self.email = email
        self.user_type = user_type

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        return User(
            data["id"],
            data["username"],
            data["email"],
            user_type_parser(data["user_type"]),
        )

    @classmethod
    def from_config(cls, path=None) -> "User | None":
        if path is None:
            path = get_config_path()

        if not os.path.exists(path):
            return None

        with open(path, "r") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return None

            if "user" not in data:
                return None

            return User.from_dict(data["user"])

    def to_config(self, path=None) -> None:
        if path is None:
            path = get_config_path()

        config_dir = os.path.dirname(path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        with open(path, "w") as file:
            json.dump({"user": self.to_dict()}, file)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "user_type": self.user_type.value,
        }
