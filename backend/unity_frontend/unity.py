from pathlib import Path

from flask import Blueprint, send_from_directory

unity_bp = Blueprint("unity", __name__, url_prefix="/game")
ROOT = Path(__file__).resolve().parent


@unity_bp.route("/")
def game():
    return send_from_directory(ROOT, "index.html")


@unity_bp.route("/<path:path>")
def static_proxy(path):
    response = send_from_directory(ROOT, path)
    if path.endswith(".br"):
        response.headers["Content-Encoding"] = "br"
    return response
