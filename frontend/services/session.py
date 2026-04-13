from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from shared.user_type import UserType
from shared.visualisation import visualize_predictions

from api.api_client import APIClient
from eventbus import Event, EventEnum, bus
from models.question import Question
from models.user import User
from utils.main_thread_dispatcher import MainThreadDispatcher
from utils.timer import Timer

logger = logging.getLogger(__name__)


class Session:
    def __init__(
        self,
        user: Optional[User],
        question: Optional[Question],
        exercise_timer: Timer,
        api_client: APIClient,
    ):
        self.user = user
        self.question = question
        self.exercise_timer = exercise_timer
        self.client = api_client

        bus.subscribe(EventEnum.SUBMIT_ANSWER, self.process_answer)
        bus.subscribe(EventEnum.PROBLEM_LOGGED, self.on_problem_logged)
        bus.subscribe(EventEnum.QUESTION_RECEIVED, self.on_question_received)
        bus.subscribe(EventEnum.MODEL_SELECTED, self.on_model_selected)
        bus.subscribe(EventEnum.USER_CHANGED, self.on_user_changed)
        bus.subscribe(
            EventEnum.VISUALIZATION_DATA_RECEIVED, self.on_visualization_data_received
        )

    @classmethod
    def create(cls, main_thread_dispatcher: MainThreadDispatcher) -> Session:
        return Session(
            User.from_config(), None, Timer(), APIClient(main_thread_dispatcher)
        )

    def set_user(self, new_user: User):
        if self.user == new_user:
            return

        self.user = new_user
        self.log_user()
        bus.publish(Event(EventEnum.USER_CHANGED, new_user.to_dict()))
        self.user.to_config()
        self.get_recommended_exercise()

    def on_debug_create_user(self):
        import random

        random_id = random.randint(0, 1000)
        user_dict = {
            "username": f"alfred{random_id}",
            "user_type": "student",
        }

        self.client.create_user(user_dict)

    def on_user_changed(self, event: Event):
        self.set_user(User.from_dict(event.payload))

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
        self.exercise_timer.stop_timer()

        payload = {
            "answer": answer,
            "response_time": self.exercise_timer.get_time(),
            "question_id": self.question.id,
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
        if self.user is None:
            self.warn_no_user()
            return

        self.client.get_visualization(self.user.id)

    def on_visualization_data_received(self, event: Event):
        responses = np.array(event.payload["responses"])
        ids = np.array(event.payload["ids"])
        probabilities = np.array(event.payload["probabilities"])
        mask = np.array(event.payload["mask"])

        dataset_name = event.payload["dataset_name"]
        model_name = event.payload["model_name"]

        fig = visualize_predictions(
            responses, ids, probabilities, mask, dataset_name, model_name
        )

        fig.show()

    def warn_no_user(self) -> None:
        if self.user is None:
            self.warn("Please log in or create a user first.")

    def warn(self, message: str) -> None:
        logger.warning(message)
        bus.publish(Event(EventEnum.USER_WARNING, {"message": message}))

    def log_user(self) -> None:
        if self.user is not None:
            logger.info(f"User logged in: {self.user}")
