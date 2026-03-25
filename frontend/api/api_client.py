import logging
import requests
import threading
from typing import Optional, Callable, Any
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError
from enum import StrEnum

logger = logging.getLogger(__name__)

URL = "http://127.0.0.1:5000/api/v1/"
USERS = "users"
STUDENTS = "students"


class HTTPMethod(StrEnum):
    GET = "GET"
    POST = "POST"


class APIClient:
    def __init__(self):
        self.session = Session()
        self.session.headers.update({"Content-Type": "application/json"})
        retry_strategy = Retry(
            total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
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
                # TODO: Handle errors
                if callback:
                    callback(error_data)

        thread = threading.Thread(target=make_request, daemon=True)
        thread.start()

    def create_user(self, user_dict: dict, callback: Callable[[dict], None]):
        self.request(HTTPMethod.POST, USERS, user_dict, callback)

    def get_users(self, callback: Callable[[list[dict]], None]):
        self.request(HTTPMethod.GET, USERS, callback=callback)

    def get_exercise(self, user_id: int, callback: Callable[[dict], None]):
        self.request(
            HTTPMethod.GET, f"{STUDENTS}/{user_id}/recommend", callback=callback
        )

    def log_problem(
        self, user_id: int, payload: dict, callback: Callable[[dict], None]
    ):
        self.request(HTTPMethod.POST, f"{STUDENTS}/{user_id}/log", payload, callback)

    def get_visualization(self, user_id: int, callback: Callable[[bytes], None]):
        self.request(
            HTTPMethod.GET, f"{STUDENTS}/{user_id}/visualize", callback=callback
        )
