from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from app import db


class Skill(db.Model):
    __tablename__ = "skills"
    skill_id = Column(Integer, primary_key=True)
    questions = relationship(
        "Question", secondary="questions_skills", back_populates="skills"
    )

    def __repr__(self):
        return f"<skill skill_id={self.skill_id}>"
