import io
from PIL import Image
from typing import Callable


from utils.timer import Timer
from models.user import User
from models.user_type import UserType
from models.question import Question
from api.api_client import create_user, get_exercise, log_problem, get_visualization


class Session:
    def __init__(
        self, user: User | None, question: Question | None, exercise_timer: Timer
    ):
        self.user = user
        self.question = question
        self.exercise_timer = exercise_timer

    @classmethod
    def create(cls) -> "Session":
        return Session(User.from_config(), None, Timer())

    def set_user(self, new_user: User, on_start_question: Callable[[Question], None]):
        print(f"Setting user id to {new_user}")
        self.user = new_user
        self.user.to_config()
        self.get_recommended_exercise(on_start_question)

    def on_debug_create_user(self, on_start_question: Callable[[Question], None]):
        import random

        random_id = random.randint(0, 1000)
        payload = {
            "username": f"alfred{random_id}",
            "email": f"alfred{random_id}@batman.com",
            "user_type": "student",
        }

        def on_create_user(response: dict):
            self.set_user(User.from_dict(response), on_start_question)

        create_user(payload, on_create_user)

    def login(self, username: str, password: str, user_type: UserType):
        pass

    def logout(self):
        pass

    def on_get_user(self) -> User | None:
        if self.user is None:
            print("Please create a user first")
            return

        print(self.user.to_dict())
        return self.user

    def get_recommended_exercise(self, on_start_question: Callable[[Question], None]):
        if self.user is None:
            print("Please create a user first")
            return

        def start_exercise(response: dict):
            self.question = Question.from_dict(response["question"])
            self.exercise_timer.start_timer()
            on_start_question(self.question)

        get_exercise(self.user.id, start_exercise)

    def process_answer(
        self,
        answer: float,
        on_answered: Callable[[bool, float], None],
        on_start_question: Callable[[Question], None],
    ) -> None:
        if self.user is None or self.question is None:
            print("Please create a user first")
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

        log_problem(self.user.id, payload, on_problem_logged)

    def on_visualize(self):
        def display_png(response: bytes):
            img = Image.open(io.BytesIO(response))
            img.show()

        if self.user is not None:
            get_visualization(self.user.id, display_png)
        else:
            print("Please create a user first")
