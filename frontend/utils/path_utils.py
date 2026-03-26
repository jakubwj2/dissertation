import sys
import os

APP_NAME = "SmartTutor"


def get_config_path(file: str = "config.json") -> str:
    system = sys.platform

    if system.startswith("win"):  # Windows
        base = os.path.expanduser(r"%APPDATA%")
    elif system == "darwin":  # macOS
        base = os.path.expanduser("~/Library/Application Support")
    else:  # Linux
        base = os.path.expanduser("~/.config")

    return os.path.join(base, APP_NAME, file)
