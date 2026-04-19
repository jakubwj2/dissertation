from app import create_app, db
from question.question_service import QuestionService

if __name__ == "__main__":
    with create_app().app_context():
        db.drop_all()
        db.create_all()

        question_service = QuestionService()
        question_service.populate_skill_table()
