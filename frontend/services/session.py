from __future__ import annotations

import io
from PIL import Image
from typing import Callable, Optional
import logging


from utils.timer import Timer
from models.user import User
from shared.user_type import UserType
from models.question import Question
from api.api_client import APIClient

logger = logging.getLogger(__name__)


class Session:
    def __init__(
        self,
        user: Optional[User],
        question: Optional[Question],
        exercise_timer: Timer,
        api_client: APIClient,
        warning_handler: Optional[Callable[[str], None]],
    ):
        self.user = user
        self.question = question
        self.exercise_timer = exercise_timer
        self.client = api_client
        self.warning_handler = warning_handler

    @classmethod
    def create(cls, warning_handler: Optional[Callable[[str], None]] = None) -> Session:
        return Session(User.from_config(), None, Timer(), APIClient(), warning_handler)

    def set_user(self, new_user: User, on_start_question: Callable[[Question], None]):
        self.user = new_user
        self.log_user()
        self.user.to_config()
        self.get_recommended_exercise(on_start_question)

    def on_debug_create_user(self, on_start_question: Callable[[Question], None]):
        import random

        random_id = random.randint(0, 1000)
        user_dict = {
            "username": f"alfred{random_id}",
            "user_type": "student",
        }

        def on_create_user(response: dict):
            self.set_user(User.from_dict(response), on_start_question)

        self.client.create_user(user_dict, on_create_user)

    def login(self, username: str, password: str, user_type: UserType):
        raise NotImplementedError()

    def logout(self):
        raise NotImplementedError()

    def on_get_user(self) -> Optional[User]:
        if self.user is None:
            self.warn_no_user()
            return

        self.log_user()
        return self.user

    def get_recommended_exercise(self, on_start_question: Callable[[Question], None]):
        if self.user is None:
            self.warn_no_user()
            return

        def start_exercise(response: dict):
            self.question = Question.from_dict(response["question"])
            self.exercise_timer.start_timer()
            on_start_question(self.question)

        self.client.get_exercise(self.user.id, start_exercise)

    def process_answer(
        self,
        answer: float,
        on_answered: Callable[[bool, float], None],
        on_start_question: Callable[[Question], None],
    ) -> None:
        if self.user is None:
            self.warn_no_user()
            return
        if self.question is None:
            logger.error("User logged in but no question, this should not happen")
            self.warn("Something went wrong. Please restart the application.")
            return

        correct = answer == self.question.answer
        self.exercise_timer.stop_timer()

        payload = {
            "correct": correct,
            "response_time": self.exercise_timer.get_time(),
            "skill_id": self.question.id,
        }

        def on_problem_logged(logged_problem: dict):
            on_answered(
                bool(logged_problem["correct"]), float(logged_problem["response_time"])
            )
            self.get_recommended_exercise(on_start_question)

        self.client.log_problem(self.user.id, payload, on_problem_logged)

    def on_visualize(self):
        def display_png(response: bytes):
            img = Image.open(io.BytesIO(response))
            img.show()

        if self.user is None:
            self.warn_no_user()
            return
        
        self.client.get_visualization(self.user.id, display_png)

    def get_users(self, callback: Callable[[list[dict]], None]):
        self.client.get_users(callback)

    def get_models(self, callback: Callable[[list[dict]], None]):
        self.client.get_models(callback)

    def select_model(self, payload: dict, on_start_question: Callable[[Question], None]):
        def callback_wrapper(response: dict):
            logger.info(f"Selected model: {response}")
            self.get_recommended_exercise(on_start_question)
        self.client.select_model(payload, callback_wrapper)

    def warn_no_user(self) -> None:
        if self.user is None:
            logger.warning("No user logged in")
            self.warn("Please log in or create a user first.")

    def warn(self, message: str) -> None:
        if self.warning_handler is not None:
            self.warning_handler(message)

    def log_user(self) -> None:
        if self.user is not None:
            logger.info(f"User logged in: {self.user}")
