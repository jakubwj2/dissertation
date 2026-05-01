from flask import Blueprint

game_bp = Blueprint(
    "game", __name__, template_folder="templates"
)  # , url_prefix="/game")

from . import routes as _routes  # noqa: E402, F401
