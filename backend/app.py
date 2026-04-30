import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

ACCESS_EXPIRES = timedelta(hours=1)

db = SQLAlchemy()
jwt = JWTManager()

cors = CORS(
    resources={
        r"/api/*": {
            "origins": [
                "https://jakubwj.com",
                "http://localhost:5000",
            ]
        }
    },
    supports_credentials=True,
)
load_dotenv()

jwt_memory_blocklist = set()


# Callback function to check if a JWT exists in the redis blocklist
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    return jti in jwt_memory_blocklist


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    from resources import api_bp
    from unity_frontend.unity import unity_bp

    app.register_blueprint(unity_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == "__main__":
    load_dotenv()
    app = create_app()
    app.run(debug=True)
