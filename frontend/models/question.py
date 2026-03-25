from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass
class Question:
    id: int
    text: str
    answer: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Question:
        return cls(
            id=int(data["skill_id"]),
            text=str(data["text"]),
            answer=float(data["answer"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "answer": self.answer,
        }
