from typing import override

from models.question import Question

from .question_generator import QuestionGenerator

OPERAND_MAX = 10
NUM_OPERANDS = 2


class AdditionGenerator(QuestionGenerator):
    family_id = "ADD"
    version = "v1"
    max_seed = OPERAND_MAX**2 - 1

    @override
    def generate(self, seed: int) -> Question:
        a, b = self.parse_seed(seed, OPERAND_MAX, NUM_OPERANDS)

        return Question(
            external_id=self.get_question_id(seed),
            question_text=f"{a} + {b}",
            answer=a + b,
            skills=self.get_or_create_skills(["Addition"]),
        )


class SubtractionGenerator(QuestionGenerator):
    family_id = "SUB"
    version = "v1"

    max_seed = OPERAND_MAX**2 - 1

    @override
    def generate(self, seed: int) -> Question:
        a, b = self.parse_seed(seed, OPERAND_MAX, NUM_OPERANDS)

        return Question(
            external_id=self.get_question_id(seed),
            question_text=f"{a} - {b}",
            answer=a - b,
            skills=self.get_or_create_skills(["Subtraction"]),
        )


class MultiplicationGenerator(QuestionGenerator):
    family_id = "MUL"
    version = "v1"

    max_seed = OPERAND_MAX**2 - 1

    @override
    def generate(self, seed: int) -> Question:
        a, b = self.parse_seed(seed, OPERAND_MAX, NUM_OPERANDS)

        return Question(
            external_id=self.get_question_id(seed),
            question_text=f"{a} * {b}",
            answer=a * b,
            skills=self.get_or_create_skills(["Multiplication"]),
        )


class DivisionGenerator(QuestionGenerator):
    family_id = "DIV"
    version = "v1"

    max_seed = OPERAND_MAX**2 - 1 - OPERAND_MAX  # no division by zero

    @override
    def generate(self, seed: int) -> Question:
        a, b = self.parse_seed(seed, OPERAND_MAX, NUM_OPERANDS)
        b += 1  # no division by zero

        return Question(
            external_id=self.get_question_id(seed),
            question_text=f"{a} / {b}",
            answer=a / b,
            skills=self.get_or_create_skills(["Division"]),
        )
