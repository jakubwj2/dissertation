from flask_restful import Resource, fields, marshal_with, reqparse
from shared.user_type import UserType, user_type_parser

from app import db
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

    @marshal_with(user_fields)
    def post(self):
        args = user_args.parse_args()

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

        if user is None:
            return [], 400
        db.session.add(user)
        db.session.commit()
        return user, 201


class GetFilteredUsers(Resource):
    @marshal_with(user_fields)
    def get(self, user_type):

        users = None
        if user_type == "student":
            users = Student.query.all()
        elif user_type == "teacher":
            users = Teacher.query.all()

        if users is None or len(users) == 0:
            return [], 404
        return users


class GetUser(Resource):
    @marshal_with(user_fields)
    def get(self, user_id):
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
