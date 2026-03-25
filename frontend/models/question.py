from typing import Any


class Question:
    def __init__(self, id: int, text:str, answer: float):
        self.id = id
        self.text = text
        self.answer = answer

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Question":
        return Question(data["skill_id"], data["text"], data["answer"])


    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "answer": self.answer,
        }