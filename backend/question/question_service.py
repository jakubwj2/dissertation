import random

from app import db
from models.question import Question

from .generators import (
    AdditionGenerator,
    DivisionGenerator,
    MultiplicationGenerator,
    QuestionGenerator,
    SubtractionGenerator,
)

DECIMAL_PLACES = 2


class QuestionService:
    def __init__(self):
        self.generator_classes: list[type[QuestionGenerator]] = [
            AdditionGenerator,
            SubtractionGenerator,
            MultiplicationGenerator,
            DivisionGenerator,
        ]

        self.generators: dict[str, dict[str, QuestionGenerator]] = {}
        for generator_class in self.generator_classes:
            generator = generator_class()
            if generator.family_id not in self.generators:
                self.generators[generator.family_id] = {}

            if generator.version in self.generators[generator.family_id]:
                raise ValueError(
                    f"Duplicate Generator with family ID {generator.family_id} and version {generator.version}."
                )

            self.generators[generator.family_id][generator.version] = generator

    def generate_question(self, question_id: str) -> Question:
        question = db.session.query(Question).filter_by(external_id=question_id).first()
        if question is not None:
            return question
        generator, seed = self.get_generator_and_seed(question_id)
        question = generator.generate(seed)
        db.session.add(question)
        db.session.commit()
        return question

    def get_generator_and_seed(self, question_id: str) -> tuple[QuestionGenerator, int]:
        identifier = question_id.split(":")
        if len(identifier) != 3:
            raise ValueError(f"Invalid question ID: {question_id}")

        family_id = identifier[0]
        version = identifier[1]
        seed = int(identifier[2])

        if family_id not in self.generators:
            raise ValueError(f"Unknown family ID: {family_id}")

        if version not in self.generators[family_id]:
            raise ValueError(f"Unknown version: {version}")

        generator = self.generators[family_id][version]

        if seed < 0:
            raise ValueError(f"Seed too small {seed}")
        if seed > generator.max_seed:
            raise ValueError(
                f"Invalid seed: {seed} for generator {family_id}:{version} "
            )

        return generator, seed

    def generate_random_question(self) -> Question:
        generator = random.choice(self.generator_classes)
        question_id = f"{generator.family_id}:{generator.version}:{random.randint(0, generator.max_seed)}"
        return self.generate_question(question_id)

    def generate_coverage_questions(self) -> list[str]:
        candidates = set(
            generator.get_question_id(seed)
            for generator in self.generator_classes
            for seed in range(generator.max_seed + 1)
        )
        existing_external_ids = {
            row[0]
            for row in db.session.query(Question.external_id)  # type: ignore
            .filter(Question.external_id.in_(candidates))  # type: ignore
            .all()
        }

        return list(candidates - existing_external_ids)

    def populate_skill_table(self):
        for generator in self.generators.values():
            for version in generator.values():
                version.get_or_create_skills(version.skill_names)
