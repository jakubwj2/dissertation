from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app import db


class Question(db.Model):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    external_id = Column(String(32), unique=True, nullable=False, index=True)
    question_text = Column(String(256), nullable=False)
    answer = Column(Float, nullable=False)
    skills = relationship(
        "Skill", secondary="questions_skills", back_populates="questions"
    )

    def __init__(
        self, external_id: str, question_text: str, answer: float, skills: list
    ):
        self.external_id = external_id
        self.question_text = question_text
        self.answer = answer
        self.skills = skills

    def __repr__(self):
        return f"<Question external_id={self.external_id} question_text={self.question_text} answer={self.answer}>"
