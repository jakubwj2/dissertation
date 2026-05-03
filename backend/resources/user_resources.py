from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_restful import Resource, fields, marshal, marshal_with, reqparse
from shared.user_type import UserType, user_type_parser

from app import db, jwt_memory_blocklist
from models import Synthesizer
from models.user import Student, Teacher
from models.user import User as UserModel

user_args = reqparse.RequestParser()
user_args.add_argument("username", type=str, required=True, help="Name is required")
user_args.add_argument(
    "user_type",
    type=user_type_parser,
    required=True,
    help="User type is required (student or teacher)",
)
user_args.add_argument("synthesizer_id", type=int, required=False)
user_args.add_argument("password", type=str, required=True, help="Password is required")

user_fields = {
    "id": fields.Integer,
    "username": fields.String,
    "user_type": fields.String,
}

users_list_fields = {"users": fields.List(fields.Nested(user_fields))}


class Users(Resource):
    @marshal_with(users_list_fields)
    def get(self):
        users = UserModel.query.all()

        return {"users": users}


class GetFilteredUsers(Resource):
    @marshal_with(user_fields)
    def get(self, user_type):

        users = None
        if user_type == "student":
            users = Student.query.all()
        elif user_type == "teacher":
            users = Teacher.query.all()

        return users


class GetUser(Resource):
    method_decorators = [jwt_required()]

    @marshal_with(user_fields)
    def get(self):
        user_id = get_jwt_identity()
        user = UserModel.query.filter_by(id=user_id).first_or_404()
        return user


synthesizer_fields = {"id": fields.Integer, "model_name": fields.String}

synthesizer_args = reqparse.RequestParser()
synthesizer_args.add_argument(
    "model_name", type=str, required=True, help="Model Name is required"
)


class Synthesizers(Resource):
    @marshal_with(synthesizer_fields)
    def get(self):
        return Synthesizer.query.all()

    @marshal_with(synthesizer_fields)
    def post(self):
        args = synthesizer_args.parse_args()
        synthesizer = Synthesizer(model_name=args["model_name"])  # type: ignore
        db.session.add(synthesizer)
        db.session.commit()
        return synthesizer


login_args = reqparse.RequestParser()
login_args.add_argument("username", type=str, required=True, help="Name is required")
login_args.add_argument(
    "password", type=str, required=True, help="Password is required"
)


class Login(Resource):
    def post(self):
        args = login_args.parse_args()
        user = UserModel.query.filter_by(username=args["username"]).first()
        if not user or not user.check_password(args["password"]):
            return {"message": "Invalid credentials"}, 401

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"user_type": user.user_type},
        )
        return {"access_token": access_token}, 200


class Register(Resource):
    REQUIRED_USERNAME_LENGTH = 8
    REQUIRED_PASSWORD_LENGTH = 8

    def post(self):
        args = user_args.parse_args()

        existing_user = UserModel.query.filter_by(username=args["username"]).first()
        if existing_user is not None:
            return {"message": "User already exists"}, 409

        if len(args["username"]) < self.REQUIRED_USERNAME_LENGTH:
            return {
                "message": f"Username must be at least {self.REQUIRED_USERNAME_LENGTH} characters"
            }, 422

        if len(args["password"]) < self.REQUIRED_PASSWORD_LENGTH:
            return {
                "message": f"Password must be at least {self.REQUIRED_PASSWORD_LENGTH} characters"
            }, 422

        user = None
        if args["user_type"] == UserType.STUDENT:
            source = None
            if args["synthesizer_id"] is not None:
                source = Synthesizer.query.get_or_404(
                    args["synthesizer_id"], "Synthesizer not found!"
                )
            user = Student(username=args["username"], source=source)
        elif args["user_type"] == UserType.TEACHER:
            user = Teacher(username=args["username"])
        else:
            return {"message": "Type not yet supported"}, 500

        user.set_password(args["password"])
        db.session.add(user)
        db.session.commit()
        return marshal(user, user_fields), 201


class Logout(Resource):
    @jwt_required()
    def delete(self):
        jti = get_jwt()["jti"]
        jwt_memory_blocklist.add(jti)
        return {"message": "Successfully logged out"}, 200
