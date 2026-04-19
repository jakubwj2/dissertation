from shared.user_type import UserType
from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model):
    """An abstract user of the system.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        user_type (UserType): User type.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, nullable=False)
    user_type = Column(Enum(UserType), nullable=False)
    password_hash = Column(String(255), nullable=False)

    __mapper_args__ = {"polymorphic_on": user_type}

    def __init__(self, *args, **kwargs):
        if type(self) is User:
            raise TypeError("User is an abstract base; use Student or Teacher.")
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<User id={self.id!r} username={self.username!r} user_type={self.user_type!r}>"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password_hash, password)  # type: ignore


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

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    synthesizer_id = Column(Integer, ForeignKey("synthesizers.id"), nullable=True)

    source = relationship("Synthesizer", back_populates="users")
    courses = relationship("Course", secondary="enrollments", back_populates="students")
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

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    courses = relationship("Course", back_populates="teacher")

    def __repr__(self):
        return f"<Teacher id={self.id!r} username={self.username!r}>"
