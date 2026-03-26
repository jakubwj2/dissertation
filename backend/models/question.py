from app import db
from sqlalchemy import Column, Integer, String, Float


class Question(db.Model):
    __tablename__ = "questions"
    question_id = Column(Integer, primary_key=True)
    question_text = Column(String(200), nullable=False)
    answer = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Question question_id={self.question_id} question_text={self.question_text} answer={self.answer}>"
