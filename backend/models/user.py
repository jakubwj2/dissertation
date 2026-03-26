from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app import db
from .enrollment import enrollments
from .user_type import UserType
from .course import Course
from .problem_log import ProblemLog


class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_type = Column(Enum(UserType), nullable=False)
    username = Column(String(80), unique=True, nullable=False)

    def __init__(self, username):
        self.username = username

    __mapper_args__ = {"polymorphic_on": user_type}


class Student(User):
    __tablename__ = "students"
    __mapper_args__ = {"polymorphic_identity": UserType.STUDENT}

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    courses = db.relationship(Course, secondary=enrollments, back_populates="student")
    problem_logs = relationship(ProblemLog, back_populates="student")


class Teacher(User):
    __tablename__ = "teachers"
    __mapper_args__ = {"polymorphic_identity": UserType.TEACHER}

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    courses = db.relationship(Course, back_populates="teacher")
