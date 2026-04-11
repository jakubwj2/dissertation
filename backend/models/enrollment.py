from sqlalchemy import Column, DateTime, ForeignKey, Integer, func

from app import db

# Association table linking students to courses (many-to-many)
enrollments = db.Table(
    "enrollments",
    db.metadata,
    Column("student_id", Integer, ForeignKey("students.user_id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.course_id"), primary_key=True),
    Column("enrolled_at", DateTime(timezone=True), nullable=False, default=func.now),
)
