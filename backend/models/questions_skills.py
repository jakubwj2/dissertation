from sqlalchemy import Column, ForeignKey, Integer

from app import db

questions_skills = db.Table(
    "questions_skills",
    db.metadata,
    Column(
        "question_id", Integer, ForeignKey("questions.question_id"), primary_key=True
    ),
    Column("skill_id", Integer, ForeignKey("skills.skill_id"), primary_key=True),
)
