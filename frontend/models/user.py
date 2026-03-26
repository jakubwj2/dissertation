from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from shared.user_type import UserType, user_type_parser
from utils.path_utils import get_config_path


@dataclass
class User:
    id: int
    username: str
    user_type: UserType

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        return User(
            id=int(data["id"]),
            username=str(data["username"]),
            user_type=user_type_parser(data["user_type"]),
        )

    @classmethod
    def from_config(cls, path: Optional[str] = None) -> Optional[User]:
        if path is None:
            path = get_config_path()

        if not os.path.exists(path):
            return None

        try:
            with open(path, "r") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            return None

        user_data = data.get("user")
        if not isinstance(user_data, dict):
            return None

        return cls.from_dict(user_data)

    def to_config(self, path: Optional[str] = None) -> None:
        if path is None:
            path = get_config_path()

        config_dir = os.path.dirname(path)
        os.makedirs(config_dir, exist_ok=True)

        with open(path, "w") as file:
            json.dump({"user": self.to_dict()}, file)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "user_type": self.user_type.value,
        }
