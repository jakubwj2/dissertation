from app import db
from sqlalchemy import Column, Integer, ForeignKey, DateTime, func


# Association table linking students to courses (many-to-many)
enrollments = db.Table(
    "enrollments",
    db.metadata,
    Column("student_id", Integer, ForeignKey("students.user_id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.course_id"), primary_key=True),
    Column("enrolled_at", DateTime(timezone=True), nullable=False, default=func.now),
)
