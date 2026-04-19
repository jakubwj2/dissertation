from typing import Any

import requests
from requests import Session
from shared.user_type import UserType

from models.SyntheticStudent import SyntheticStudent

API_URL = "http://127.0.0.1:5000/api/v1"


class ServerAPI:
    def __init__(self) -> None:
        self.session = Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def get_json(self, response: requests.Response):
        response.raise_for_status()
        return response.json()

    def get_or_create_synthesizer(self, synthesizer: str) -> int:
        response = self.session.get(f"{API_URL}/synthesizers")

        for api_synthesizer in response.json():
            if api_synthesizer["model_name"] == synthesizer:
                return int(api_synthesizer["id"])

        post_response = self.session.post(
            f"{API_URL}/synthesizers", json={"model_name": synthesizer}
        )
        return self.get_json(post_response)["id"]

    def register_student(self, student: SyntheticStudent, synthesizer_id: int) -> None:
        payload = {
            "username": student.name,
            "user_type": UserType.STUDENT.value,
            "synthesizer_id": synthesizer_id,
            "password": student.password,
        }
        response = self.session.post(f"{API_URL}/register", json=payload)
        self.get_json(response)

    def login_student(self, student: SyntheticStudent) -> None:
        payload = {
            "username": student.name,
            "password": student.password,
        }
        response = self.session.post(f"{API_URL}/login", json=payload)
        access_token = self.get_json(response)["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def get_skills(self) -> list[str]:
        response = self.session.get(f"{API_URL}/skills")
        return self.get_json(response)

    def get_student_names(self) -> list[str]:
        response = self.session.get(f"{API_URL}/users/students")
        students = self.get_json(response)
        return [student["username"] for student in students]

    def get_question(self) -> dict[str, Any]:
        response = self.session.get(f"{API_URL}/recommend")
        return self.get_json(response)["question"]

    def post_log(
        self, question: dict[str, Any], llm_answer: dict[str, Any]
    ) -> dict[str, Any]:
        payload = {
            "question_id": question["question_id"],
            "answer": llm_answer["answer"],
            "response_time": llm_answer["response_time"],
        }

        response = self.session.post(f"{API_URL}/log", json=payload)
        return self.get_json(response)
