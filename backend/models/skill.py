from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app import db


class Skill(db.Model):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, nullable=False, index=True)
    questions = relationship(
        "Question", secondary="questions_skills", back_populates="skills"
    )

    def __repr__(self):
        return f"<skill name={self.name}>"
