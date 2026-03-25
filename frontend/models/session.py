import io
import tkinter as tk
from PIL import Image


from utils.timer import Timer
from models.user import User
from models.user_type import UserType
from api.api_client import create_user, get_exercise, log_problem, get_visualization


class Session:
    def __init__(self, user: User | None, skill_id: int | None, exercise_timer: Timer):
        self.user = user
        self.skill_id = skill_id
        self.exercise_timer = exercise_timer

    @classmethod
    def create(cls) -> "Session":
        return Session(User.from_config(), None, Timer())

    def set_user(self, new_user: dict):
        print(f"Setting user id to {new_user}")
        self.user = User.from_dict(new_user)
        self.user.to_config()
        self.get_recommended_exercise()

    def on_debug_create_user(self):
        import random

        random_id = random.randint(0, 1000)
        payload = {
            "username": f"alfred{random_id}",
            "email": f"alfred{random_id}@batman.com",
            "user_type": "student",
        }
        create_user(payload, self.set_user)

    def login(self, username: str, password: str, user_type: UserType):
        pass

    def on_get_user(self) -> User | None:
        if self.user is None:
            print("Please create a user first")
            return

        print(self.user.to_dict())
        return self.user

    def set_skill(self, question: dict) -> None:
        self.skill_id = question["skill_id"]

    def get_recommended_exercise(self):
        if self.user is None:
            print("Please create a user first")
            return

        def start_exercise(exercise: dict):
            self.set_skill(exercise)
            self.exercise_timer.start_timer()

        get_exercise(self.user.id, start_exercise)

    def process_answer(self, answer: tk.StringVar) -> None:
        if self.user is None or self.skill_id is None:
            print("Please create a user first")
            return

        correct = True
        self.exercise_timer.stop_timer()

        payload = {
            "correct": correct,
            "response_time": self.exercise_timer.get_time(),
            "skill_id": self.skill_id,
        }

        def on_problem_logged(logged_problem: dict):
            print(logged_problem)
            self.get_recommended_exercise()

        log_problem(self.user.id, payload, on_problem_logged)

    def on_visualize(self):
        def display_png(response: bytes):
            img = Image.open(io.BytesIO(response))
            img.show()

        if self.user is not None:
            get_visualization(self.user.id, display_png)
        else:
            print("Please create a user first")
