from app import db
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, Float, func
from sqlalchemy.orm import relationship


class ProblemLog(db.Model):
    """Stores a single student's answer to a question.

    Attributes:
        log_id (int): Primary key.
        student_id (int): Foreign key to Student.user_id.
        correct (bool): Whether the student's response was correct.
        skill_id (int): #TODO.
        submission_time (DateTime): Time of submission.
        response_time (float): Time taken to respond.
        question_id (int): #TODO.
    """

    __tablename__ = "problem_logs"

    # user_id,log_id,sequence_id,correct
    log_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.user_id"), nullable=False)
    correct = Column(Boolean, nullable=False)
    skill_id = Column(Integer, nullable=False)
    submission_time = Column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    response_time = Column(Float, nullable=False)
    question_id = Column(Integer, nullable=False)

    # sequence_id
    student = relationship("Student", back_populates="problem_logs")

    def __init__(
        self,
        student_id: int,
        correct: bool,
        skill_id: int,
        response_time: float,
        question_id: int,
    ):
        self.student_id = student_id
        self.correct = correct
        self.skill_id = skill_id
        self.response_time = response_time
        self.question_id = question_id

    def __repr__(self):
        return (
            f"<ProblemLog log_id={self.log_id} student_id={self.student_id} "
            f"correct={self.correct} skill_id={self.skill_id} "
            f"submission_time={self.submission_time} response_time={self.response_time} "
            f"question_id={self.question_id}>"
        )
