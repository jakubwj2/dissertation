from app import db
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from datetime import datetime

enrollments = db.Table(
    "enrollments",
    db.metadata,
    Column("student_id", Integer, ForeignKey("students.user_id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.course_id"), primary_key=True),
    Column("entrolled_at", DateTime, default=datetime.now),
)
