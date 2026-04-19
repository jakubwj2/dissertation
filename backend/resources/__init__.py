from flask import Blueprint
from flask_restful import Api

from .kt_resources import (
    GetCurrentModel,
    KTPredictions,
    LogInteraction,
    Models,
    RecommendExercise,
    Skills,
)
from .user_resources import (
    GetFilteredUsers,
    GetUser,
    Login,
    Logout,
    Register,
    Synthesizers,
    Users,
)

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(api_bp)

api.add_resource(Users, "/users")
api.add_resource(Login, "/login")
api.add_resource(Logout, "/logout")
api.add_resource(Register, "/register")
api.add_resource(GetFilteredUsers, "/users/<string:user_type>s")
api.add_resource(GetUser, "/whoami/")
api.add_resource(RecommendExercise, "/recommend")
api.add_resource(LogInteraction, "/log")
api.add_resource(KTPredictions, "/kt-predictions")
api.add_resource(Models, "/models")
api.add_resource(GetCurrentModel, "/models/current")
api.add_resource(Skills, "/skills")
api.add_resource(Synthesizers, "/synthesizers")
