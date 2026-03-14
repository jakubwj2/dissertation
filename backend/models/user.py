from app import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .enrollment import enrollments


class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_type = Column(String(50), nullable=False)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)

    __mapper_args__ = {'polymorphic_on': user_type}


class Student(User):
    __tablename__ = "students"
    __mapper_args__ = {"polymorphic_identity": "student"}

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    courses = db.relationship("Course", secondary=enrollments, back_populates="student")
    problem_logs = relationship("ProblemLog", back_populates="student")


class Teacher(User):
    __tablename__ = "teachers"
    __mapper_args__ = {"polymorphic_identity": "teacher"}

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    courses = db.relationship("Course", back_populates="teacher")
