from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app import db


class Question(db.Model):
    __tablename__ = "questions"
    question_id = Column(Integer, primary_key=True)
    question_text = Column(String(200), nullable=False)
    answer = Column(Float, nullable=False)
    skills = relationship(
        "Skill", secondary="questions_skills", back_populates="questions"
    )

    def __repr__(self):
        return f"<Question question_id={self.question_id} question_text={self.question_text} answer={self.answer}>"
