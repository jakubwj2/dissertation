from app import create_app, db


if __name__ == '__main__':
    with create_app().app_context():
        from models.user import User, Student, Teacher
        from models.course import Course
        from models.problem_log import ProblemLog 
        from models.enrollment import enrollments
        from models.question import Question 
        db.drop_all()
        db.create_all()
        