from models.user import Student, Teacher, User as UserModel
from flask_restful import Resource, reqparse, fields, marshal_with


from app import db
from models.user_type import user_type_parser, UserType

user_args = reqparse.RequestParser()
user_args.add_argument("username", type=str, required=True, help="Name is required")
user_args.add_argument(
    "user_type",
    type=user_type_parser,
    required=True,
    help="User type is required (student or teacher)",
)

userFields = {
    "id": fields.Integer,
    "username": fields.String,
    "user_type": fields.String,
}


class Users(Resource):
    @marshal_with(userFields)
    def get(self):
        users = UserModel.query.all()

        if users is None:
            return [], 404
        return users

    @marshal_with(userFields)
    def post(self):
        args = user_args.parse_args()

        user = None
        if args["user_type"] == UserType.STUDENT:
            user = Student(username=args["username"])
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
    @marshal_with(userFields)
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
    @marshal_with(userFields)
    def get(self, user_id):
        user = UserModel.query.filter_by(id=user_id).first_or_404()
        return user
