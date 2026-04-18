from __future__ import annotations

from abc import ABC, abstractmethod

from models import Question, Skill


class QuestionGenerator(ABC):
    family_id: str
    version: str
    skill_names: list[str]

    max_seed: int

    @abstractmethod
    def generate(self, seed: int) -> Question:
        "Generate a question."

    @classmethod
    def get_question_id(cls, seed) -> str:
        """Construct a question ID from the family ID, version and seed."""
        return f"{cls.family_id}:{cls.version}:{seed}"

    @classmethod
    def get_or_create_skill(cls, skill_name: str):
        obj = Skill.query.filter_by(name=skill_name).first()
        if obj is None:
            obj = Skill(name=skill_name)  # type: ignore
            Skill.query.session.add(obj)
            Skill.query.session.commit()
        return obj

    @classmethod
    def get_or_create_skills(cls, skill_names: list[str]):
        return [cls.get_or_create_skill(skill_name) for skill_name in skill_names]

    @classmethod
    def parse_seed(cls, seed, operand_max, num_operands) -> list[int]:
        operands = []
        for _ in range(num_operands):
            operands.append(seed % operand_max)
            seed //= operand_max

        assert len(operands) == num_operands
        return operands
