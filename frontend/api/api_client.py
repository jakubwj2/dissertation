import logging
import threading
from enum import StrEnum
from typing import Any, Callable, Optional

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.exceptions import MaxRetryError
from urllib3.util.retry import Retry

from eventbus import Event, EventEnum, bus

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:5000/api/v1/"
USERS = "users"
STUDENTS = "students"
MODELS = "models"


class HTTPMethod(StrEnum):
    GET = "GET"
    POST = "POST"


class APIClient:
    def __init__(self):
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
        callback: Optional[Callable[[Any], None]] = None,
    ):
        def make_request():
            try:
                url = f"{URL}{endpoint}"
                response = self.session.request(
                    method.value, url, json=payload, timeout=(5, 10)
                )
                response.raise_for_status()
                if "application/json" in response.headers.get("content-type", ""):
                    data = response.json()
                else:
                    data = response.content
                logger.info(
                    f"Success: {method.value} {endpoint} -> {response.status_code}"
                )
                if callback:
                    callback(data)

            except (
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
                MaxRetryError,
            ) as e:
                error_data = {"error": str(e), "endpoint": endpoint}
                logger.error(f"API error: {error_data}")
                bus.publish(Event(EventEnum.API_ERROR, error_data))
                # TODO: Handle errors
                if callback:
                    callback(error_data)

        thread = threading.Thread(target=make_request, daemon=True)
        thread.start()

    def create_user(self, user_dict: dict, callback: Callable[[dict], None]):
        self.request(HTTPMethod.POST, USERS, user_dict, callback)

    def get_users(self):
        self.event_request(HTTPMethod.GET, USERS, event_type=EventEnum.USERS_RECEIVED)

    def get_exercise(self, user_id: int):
        self.event_request(
            HTTPMethod.GET,
            f"{STUDENTS}/{user_id}/recommend",
            event_type=EventEnum.QUESTION_RECEIVED,
        )

    def log_problem(self, user_id: int, payload: dict):
        self.event_request(
            HTTPMethod.POST,
            f"{STUDENTS}/{user_id}/log",
            payload,
            EventEnum.PROBLEM_LOGGED,
        )

    def get_visualization(self, user_id: int, callback: Callable[[bytes], None]):
        self.request(
            HTTPMethod.GET, f"{STUDENTS}/{user_id}/visualize", callback=callback
        )

    def get_models(self):
        self.event_request(HTTPMethod.GET, MODELS, event_type=EventEnum.MODELS_RECEIVED)

    def select_model(self, payload: dict):
        self.event_request(HTTPMethod.POST, MODELS, payload, EventEnum.MODEL_SELECTED)

    def get_current_model(self):
        self.event_request(
            HTTPMethod.GET,
            f"{MODELS}/current",
            event_type=EventEnum.CURRENT_MODEL_RECEIVED,
        )

    def event_request(
        self,
        method: HTTPMethod,
        endpoint: str,
        payload: Optional[dict] = None,
        event_type: EventEnum | None = None,
    ):
        def callback(data: Any):
            # logger.info(f"Event callback for {event_type.value} with data: {data}")
            if event_type is not None:
                bus.publish(Event(event_type, data))

        self.request(method, endpoint, payload, callback)
