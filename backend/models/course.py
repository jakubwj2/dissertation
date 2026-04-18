from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app import db


class Course(db.Model):
    """A taught course.

    Attributes:
        id (int): Primary key.
        teacher_id (int): Foreign key to Teacher.id.
        teacher (Teacher, [Many-to-one]): The course teacher.
        students (List[Student], [Many-to-many]): Enrolled students.
    """

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    students = relationship(
        "Student", secondary="enrollments", back_populates="courses"
    )
    teacher = relationship("Teacher", back_populates="courses")

    def __repr__(self):
        return f"<Course teacher_id={self.teacher_id!r}>"
