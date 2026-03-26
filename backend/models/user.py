from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app import db
from .enrollment import enrollments
from shared.user_type import UserType


class User(db.Model):
    """An abstract user of the system.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        user_type (UserType): User type.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    user_type = Column(Enum(UserType), nullable=False)

    __mapper_args__ = {"polymorphic_on": user_type}

    def __init__(self, *args, **kwargs):
        if type(self) is User:
            raise TypeError("User is an abstract base; use Student or Teacher.")
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<User id={self.id!r} username={self.username!r} user_type={self.user_type!r}>"


class Student(User):
    """A student user of the system.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        user_type (UserType): Polymorphic identity
        courses (List[Course], [Many-to-many]): Courses the student is enrolled in.
        problem_logs (List[ProblemLog], [Many-to-one]): Problem logs for the student.
    """

    __tablename__ = "students"
    __mapper_args__ = {"polymorphic_identity": UserType.STUDENT}

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    courses = relationship("Course", secondary=enrollments, back_populates="students")
    problem_logs = relationship("ProblemLog", back_populates="student")

    def __repr__(self):
        return f"<Student id={self.id!r} username={self.username!r}>"


class Teacher(User):
    """A teacher user of the system.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        user_type (UserType): Polymorphic identity
        courses (List[Course], [Many-to-one]): Courses the teacher teaches.
    """

    __tablename__ = "teachers"
    __mapper_args__ = {"polymorphic_identity": UserType.TEACHER}

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    courses = relationship("Course", back_populates="teacher")

    def __repr__(self):
        return f"<Teacher id={self.id!r} username={self.username!r}>"
