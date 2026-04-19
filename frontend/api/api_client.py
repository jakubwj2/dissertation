import logging
import threading
from enum import StrEnum
from typing import Optional

import keyring
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

SERVICE_NAME = "smart_tutor"
TOKER_NAME = "access_token"


class HTTPMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


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

        access_token = keyring.get_password(SERVICE_NAME, TOKER_NAME)
        if access_token is not None:
            # don't set keyring password here
            self.session.headers.update({"Authorization": f"Bearer {access_token}"})
            bus.publish(Event(EventEnum.USER_LOGGED_IN, {"access_token": access_token}))

        self.logged_in = access_token is not None

        bus.subscribe(EventEnum.USER_LOGGED_IN, self.on_user_logged_in)
        bus.subscribe(EventEnum.USER_LOGGED_OUT, self.on_user_logged_out)

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

    def get_exercise(self):
        self.request(
            HTTPMethod.GET, "/recommend", event_type=EventEnum.QUESTION_RECEIVED
        )

    def log_problem(self, payload: dict):
        self.request(HTTPMethod.POST, "/log", payload, EventEnum.PROBLEM_LOGGED)

    def get_visualization(self):
        self.request(
            HTTPMethod.GET,
            "/kt-predictions",
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

    def login(self, payload):
        self.request(HTTPMethod.POST, "login", payload, EventEnum.USER_LOGGED_IN)

    def logout(self):
        self.request(HTTPMethod.DELETE, "logout", event_type=EventEnum.USER_LOGGED_OUT)

    def register(self, payload):
        self.request(HTTPMethod.POST, "register", payload, EventEnum.USER_REGISTERED)

    def get_user(self):
        self.request(HTTPMethod.GET, "whoami", event_type=EventEnum.USER_DATA_RECEIVED)

    def on_user_logged_in(self, event: Event):
        self.session.headers.update({
            "Authorization": f"Bearer {event.payload['access_token']}"
        })
        keyring.set_password(SERVICE_NAME, TOKER_NAME, event.payload["access_token"])
        self.logged_in = True

    def on_user_logged_out(self, event: Event):
        self.session.headers.pop("Authorization")
        keyring.delete_password(SERVICE_NAME, TOKER_NAME)
        self.logged_in = False
