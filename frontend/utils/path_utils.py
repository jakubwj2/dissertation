import sys
import os

APP_NAME = "SmartTutor"


def get_config_path(file: str = "config.json") -> str:
    system = sys.platform

    if system == "win32":  # Windows
        base = os.path.expanduser("%APPDATA%")
    elif system == "darwin":  # macOS
        base = os.path.expanduser("~/Library/Application Support")
    else:  # Linux
        base = os.path.expanduser("~/.config")

    return os.path.join(base, APP_NAME, file)
