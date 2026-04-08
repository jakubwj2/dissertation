from flask import Blueprint
from flask_restful import Api

from .kt_resources import (
    GetCurrentModel,
    KTVisualization,
    LogInteraction,
    Models,
    RecommendExercise,
)
from .user_resources import GetFilteredUsers, GetUser, Users

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(api_bp)

api.add_resource(Users, "/users")
api.add_resource(GetFilteredUsers, "/users/<string:user_type>s")
api.add_resource(GetUser, "/users/<int:user_id>")
api.add_resource(RecommendExercise, "/students/<int:student_id>/recommend")
api.add_resource(LogInteraction, "/students/<int:student_id>/log")
api.add_resource(KTVisualization, "/students/<int:student_id>/visualize")
api.add_resource(Models, "/models")
api.add_resource(GetCurrentModel, "/models/current")
