from __future__ import annotations

import logging

import numpy as np
from shared.user_type import UserType
from shared.visualisation import visualize_predictions

from api.api_client import APIClient
from eventbus import Event, EventEnum, bus
from models.question import Question
from utils.main_thread_dispatcher import MainThreadDispatcher
from utils.timer import Timer

logger = logging.getLogger(__name__)


class Session:
    def __init__(
        self,
        exercise_timer: Timer,
        api_client: APIClient,
    ):
        self.question: Question | None = None
        self.exercise_timer = exercise_timer
        self.client = api_client

        bus.subscribe(EventEnum.SUBMIT_ANSWER, self.process_answer)
        bus.subscribe(EventEnum.PROBLEM_LOGGED, self.on_problem_logged)
        bus.subscribe(EventEnum.QUESTION_RECEIVED, self.on_question_received)
        bus.subscribe(EventEnum.MODEL_SELECTED, self.on_model_selected)
        bus.subscribe(EventEnum.USER_LOGGED_IN, self.on_user_logged_in)
        bus.subscribe(
            EventEnum.VISUALIZATION_DATA_RECEIVED, self.on_visualization_data_received
        )

    @classmethod
    def create(cls, main_thread_dispatcher: MainThreadDispatcher) -> Session:
        session = Session(Timer(), APIClient(main_thread_dispatcher))
        session.client.get_user()
        if session.client.logged_in:
            session.get_recommended_exercise()
        return session

    def login(self, username: str, password: str):
        payload = {"username": username, "password": password}
        self.client.login(payload)

    def register(self, username: str, password: str, user_type: UserType):
        payload = {
            "username": username,
            "password": password,
            "user_type": user_type.value,
        }
        self.client.register(payload)

    def logout(self):
        self.client.logout()

    def get_recommended_exercise(self):
        if self.client.logged_in is None:
            self.warn_no_user()
            return

        self.client.get_exercise()

    def process_answer(self, event: Event) -> None:
        if self.client.logged_in is None:
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

        self.client.log_problem(payload)

    def on_problem_logged(self, event: Event):
        self.get_recommended_exercise()

    def on_user_logged_in(self, event: Event):
        self.get_recommended_exercise()

    def on_question_received(self, event: Event):
        question = Question.from_dict(event.payload["question"])
        self.question = question
        self.exercise_timer.start_timer()

    def on_model_selected(self, event: Event):
        logger.info(f"Selected model: {event}")
        self.get_recommended_exercise()

    def on_visualize(self):
        if self.client.logged_in is None:
            self.warn_no_user()
            return

        self.client.get_visualization()

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
        if self.client.logged_in is None:
            self.warn("Please log in or create a user first.")

    def warn(self, message: str) -> None:
        logger.warning(message)
        bus.publish(Event(EventEnum.USER_WARNING, {"message": message}))
