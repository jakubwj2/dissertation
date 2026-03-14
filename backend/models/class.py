from app import db
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .enrollment import enrollments


class Course(db.Model):
    __tablename__ = "courses"

    class_id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("teachers.user_id"), nullable=False)

    student = relationship("Student", secondary=enrollments, back_populates="courses")
    teacher = relationship("Teacher", back_populates="courses")
