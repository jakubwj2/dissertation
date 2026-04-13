from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Question:
    id: str
    text: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Question:
        return cls(
            id=str(data["question_id"]),
            text=str(data["text"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
        }
