from app import create_app, db

if __name__ == '__main__':
    with create_app().app_context():
        db.create_all()