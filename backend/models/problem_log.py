from app import db
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime


class ProblemLog(db.Model):
    __tablename__ = "problem_logs"

    # user_id,log_id,sequence_id,correct
    log_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.user_id"), nullable=False)
    correct = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=True, default=datetime.now)
    response_time = Column(Float, nullable=True)
    skill_id = Column(Integer, nullable=True)

    # sequence_id
    student = relationship("Student", back_populates="problem_logs")
