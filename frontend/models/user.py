from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.user_type import UserType, user_type_parser


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "user_type": self.user_type.value,
        }
