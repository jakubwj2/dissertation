from sqlalchemy import Column, ForeignKey, Integer

from app import db

questions_skills = db.Table(
    "questions_skills",
    db.metadata,
    Column("question_id", Integer, ForeignKey("questions.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
)
