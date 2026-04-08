import logging
import threading
from enum import StrEnum
from typing import Optional

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.exceptions import MaxRetryError
from urllib3.util.retry import Retry

from eventbus import Event, EventEnum, bus
from utils.main_thread_dispatcher import MainThreadDispatcher

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:5000/api/v1/"
USERS = "users"
STUDENTS = "students"
MODELS = "models"


class HTTPMethod(StrEnum):
    GET = "GET"
    POST = "POST"


class APIClient:
    def __init__(self, main_thread_dispatcher: MainThreadDispatcher):
        self.main_thread_dispatcher = main_thread_dispatcher
        self.session = Session()
        self.session.headers.update({"Content-Type": "application/json"})
        retry_strategy = Retry(
            total=1, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def request(
        self,
        method: HTTPMethod,
        endpoint: str,
        payload: Optional[dict] = None,
        event_type: Optional[EventEnum] = None,
    ):
        def make_request():
            try:
                url = f"{URL}{endpoint}"
                response = self.session.request(
                    method.value, url, json=payload, timeout=(5, 10)
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"{method.value} {endpoint} -> {response.status_code}")
                if event_type is not None:
                    self.main_thread_dispatcher.queue_task(
                        lambda: bus.publish(Event(event_type, data))  # type: ignore
                    )

            except (
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
                MaxRetryError,
            ) as e:
                error_data = {"error": str(e), "endpoint": endpoint}
                logger.error(f"API error: {error_data}")
                bus.publish(Event(EventEnum.API_ERROR, error_data))

        thread = threading.Thread(target=make_request, daemon=True)
        thread.start()

    def create_user(self, user_dict: dict):
        self.request(HTTPMethod.POST, USERS, user_dict, EventEnum.USER_CHANGED)

    def get_users(self):
        self.request(HTTPMethod.GET, USERS, event_type=EventEnum.USERS_RECEIVED)

    def get_exercise(self, user_id: int):
        self.request(
            HTTPMethod.GET,
            f"{STUDENTS}/{user_id}/recommend",
            event_type=EventEnum.QUESTION_RECEIVED,
        )

    def log_problem(self, user_id: int, payload: dict):
        self.request(
            HTTPMethod.POST,
            f"{STUDENTS}/{user_id}/log",
            payload,
            EventEnum.PROBLEM_LOGGED,
        )

    def get_visualization(self, user_id: int):
        self.request(
            HTTPMethod.GET,
            f"{STUDENTS}/{user_id}/kt-predictions",
            event_type=EventEnum.VISUALIZATION_DATA_RECEIVED,
        )

    def get_models(self):
        self.request(HTTPMethod.GET, MODELS, event_type=EventEnum.MODELS_RECEIVED)

    def select_model(self, payload: dict):
        self.request(HTTPMethod.POST, MODELS, payload, EventEnum.MODEL_SELECTED)

    def get_current_model(self):
        self.request(
            HTTPMethod.GET,
            f"{MODELS}/current",
            event_type=EventEnum.CURRENT_MODEL_RECEIVED,
        )
