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
    skill_id = Column(Integer, nullable=False)
    submission_time = Column(DateTime, nullable=False, default=datetime.now)
    response_time = Column(Float, nullable=False)
    question_id = Column(Integer, nullable=False)

    # sequence_id
    student = relationship("Student", back_populates="problem_logs")

    def __init__(
        self,
        student_id: int,
        correct: int,
        skill_id: int,
        response_time: float,
        question_id: int,
    ):
        self.student_id = student_id
        self.correct = correct
        self.skill_id = skill_id
        self.response_time = response_time
        self.question_id = question_id
