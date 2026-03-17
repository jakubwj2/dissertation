from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

    db.init_app(app)

    from resources import api_bp
    app.register_blueprint(api_bp)
    
    return app


if __name__ == "__main__":
    load_dotenv()
    app = create_app()
    app.run(debug=True)
