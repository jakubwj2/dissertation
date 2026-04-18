from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app import db


class ProblemLog(db.Model):
    """Stores a single student's answer to a question.

    Attributes:
        id (int): Primary key.
        student_id (int): Foreign key to Student.id.
        correct (bool): Whether the student's response was correct.
        submission_time (DateTime): Time of submission.
        response_time (float): Time taken to respond.
        question_id (int): #TODO.
    """

    __tablename__ = "problem_logs"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    correct = Column(Boolean, nullable=False)
    submission_time = Column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    response_time = Column(Float, nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    student = relationship("Student", back_populates="problem_logs")
    question = relationship("Question")

    def __init__(
        self,
        student_id: int,
        correct: bool,
        response_time: float,
        question_id: int,
    ):
        self.student_id = student_id
        self.correct = correct
        self.response_time = response_time
        self.question_id = question_id

    def __repr__(self):
        return (
            f"<ProblemLog id={self.id} student_id={self.student_id} "
            f"correct={self.correct} submission_time={self.submission_time} "
            f"response_time={self.response_time} question_id={self.question_id}>"
        )
