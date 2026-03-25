import requests
import threading
from typing import Callable


URL = "http://127.0.0.1:5000/api/v1/"
USERS = "users"
STUDENTS = "students"


def create_user(payload, callback: Callable[[dict], None]):
    def request():
        response = requests.post(URL + "users", json=payload)
        response.raise_for_status()
        print(response.status_code)
        callback(response.json())

    thread = threading.Thread(target=request, daemon=True)
    thread.start()


def get_users(callback: Callable[[list[dict]], None]):
    def request():
        response = requests.get(f"{URL}{USERS}")
        response.raise_for_status()
        print(response.status_code)
        callback(response.json())

    thread = threading.Thread(target=request, daemon=True)
    thread.start()


def get_exercise(user_id: int, callback: Callable[[dict], None]):
    def request():
        response = requests.get(f"{URL}{STUDENTS}/{user_id}/recommend")
        response.raise_for_status()
        print(response.status_code)
        callback(response.json())

    thread = threading.Thread(target=request, daemon=True)
    thread.start()


def log_problem(user_id: int, payload: dict, callback: Callable[[dict], None]):
    def request():
        response = requests.post(f"{URL}{STUDENTS}/{user_id}/log", json=payload)
        response.raise_for_status()
        print(response.status_code)
        callback(response.json())

    thread = threading.Thread(target=request, daemon=True)
    thread.start()


def get_visualization(user_id: int, callback: Callable[[bytes], None]):
    def request():
        response = requests.get(f"{URL}{STUDENTS}/{user_id}/visualize")
        response.raise_for_status()
        print(response.status_code)
        callback(response.content)

    thread = threading.Thread(target=request, daemon=True)
    thread.start()
