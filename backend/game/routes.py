from pathlib import Path

from flask import current_app, render_template, send_from_directory
from werkzeug.security import safe_join

from . import game_bp


@game_bp.route("/")
def game():
    return render_template("game/index.html")


@game_bp.route("/Assests/<path:path>")
def static_proxy(path):
    root = current_app.config["UNITY_ROOT"]
    full_path = safe_join(str(root), path)
    if full_path is None or not Path(full_path).exists():
        return {"message": f'Game file "{path}" not found'}, 404
    response = send_from_directory(root, path)
    if path.endswith(".br"):
        response.headers["Content-Encoding"] = "br"
    return response
