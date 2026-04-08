from __future__ import annotations

import io
import logging
from typing import Callable, Optional

from PIL import Image
from shared.user_type import UserType

from api.api_client import APIClient
from eventbus import Event, EventEnum, bus
from models.question import Question
from models.user import User
from utils.timer import Timer

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

        bus.subscribe(EventEnum.SUBMIT_ANSWER, self.process_answer)
        bus.subscribe(EventEnum.PROBLEM_LOGGED, self.on_problem_logged)
        bus.subscribe(EventEnum.QUESTION_RECEIVED, self.on_question_received)
        bus.subscribe(EventEnum.MODEL_SELECTED, self.on_model_selected)

    @classmethod
    def create(cls, warning_handler: Optional[Callable[[str], None]] = None) -> Session:
        return Session(User.from_config(), None, Timer(), APIClient(), warning_handler)

    def set_user(self, new_user: User):
        self.user = new_user
        self.log_user()
        self.user.to_config()
        self.get_recommended_exercise()

    def on_debug_create_user(self):
        import random

        random_id = random.randint(0, 1000)
        user_dict = {
            "username": f"alfred{random_id}",
            "user_type": "student",
        }

        def on_create_user(response: dict):
            self.set_user(User.from_dict(response))

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

    def get_recommended_exercise(self):
        if self.user is None:
            self.warn_no_user()
            return

        self.client.get_exercise(self.user.id)

    def process_answer(self, event: Event) -> None:
        if self.user is None:
            self.warn_no_user()
            return
        if self.question is None:
            logger.error("User logged in but no question, this should not happen")
            self.warn("Something went wrong. Please restart the application.")
            return

        answer = event.payload["answer"]
        correct = answer == self.question.answer
        self.exercise_timer.stop_timer()

        payload = {
            "correct": correct,
            "response_time": self.exercise_timer.get_time(),
            "skill_id": self.question.id,
        }

        self.client.log_problem(self.user.id, payload)

    def on_problem_logged(self, event: Event):
        self.get_recommended_exercise()

    def on_question_received(self, event: Event):
        question = Question.from_dict(event.payload["question"])
        self.question = question
        self.exercise_timer.start_timer()

    def on_model_selected(self, event: Event):
        logger.info(f"Selected model: {event}")
        self.get_recommended_exercise()

    def on_visualize(self):
        def display_png(response: bytes):
            img = Image.open(io.BytesIO(response))
            img.show()

        if self.user is None:
            self.warn_no_user()
            return

        self.client.get_visualization(self.user.id, display_png)

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
