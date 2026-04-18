from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app import db


class Synthesizer(db.Model):
    __tablename__ = "synthesizers"
    id = Column(Integer, primary_key=True)
    model_name = Column(String(32), unique=True, nullable=False, index=True)
    users = relationship("Student", back_populates="source")
