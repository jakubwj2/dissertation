import requests
from requests import Session
from shared.user_type import UserType

API_URL = "http://127.0.0.1:5000/api/v1"


class ServerAPI:
    def __init__(self) -> None:
        self.session = Session()

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

    def post_student(self, user: dict, synthesizer_id: int) -> int:
        user_payload = {
            "username": user["name"],
            "user_type": UserType.STUDENT.value,
            "synthesizer_id": synthesizer_id,
        }
        response = self.session.post(f"{API_URL}/users", json=user_payload)
        return self.get_json(response)["id"]

    def get_skills(self) -> list:
        response = requests.get(f"{API_URL}/skills")
        return self.get_json(response)

    def get_student_names(self):
        response = requests.get(f"{API_URL}/users/students")
        students = self.get_json(response)
        return [student["username"] for student in students]

    def get_question(self, user_id: int) -> dict:
        response = self.session.get(f"{API_URL}/students/{user_id}/recommend")
        return self.get_json(response)["question"]

    def post_log(self, user_id: int, question: dict, llm_answer: dict) -> dict:
        payload = {
            "question_id": question["question_id"],
            "answer": llm_answer["answer"],
            "response_time": llm_answer["response_time"],
        }

        response = self.session.post(f"{API_URL}/students/{user_id}/log", json=payload)
        return self.get_json(response)
