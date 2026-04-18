import json
from dataclasses import asdict

import ollama as lm
from ollama import ListResponse

from models.SyntheticStudent import SkillState


class LLM_API:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def get_or_create_model(self, from_: str, system_prompt: str) -> None:
        model_list: ListResponse = lm.list()

        contains_model = False
        for model in model_list.models:
            if model.model == self.model_name:
                contains_model = True
                break

        if not contains_model:
            create_response = lm.create(
                model=self.model_name,
                system=system_prompt,
                from_=from_,
                stream=False,
            )

            print(create_response)

    def create_chat_message(
        self, student_state: dict[str, SkillState], question_text: str
    ) -> dict:
        student_state_json = json.dumps({
            skill: asdict(state) for skill, state in student_state.items()
        })

        return {
            "role": "user",
            "content": str({
                "student_state": student_state_json,
                "question": question_text,
            }),
        }

    def parse_response(self, message_content: str | None) -> dict | None:
        if message_content is None:
            return None

        try:
            student_answer: dict = json.loads(message_content)
            json.dumps(
                student_answer, allow_nan=False
            )  # used by requests to validate json
            if not set(student_answer.keys()) == {"answer", "response_time"}:
                return None

            answer = float(student_answer["answer"])
            response_time = float(student_answer["response_time"])

            if response_time < 0:
                return None

            return {"answer": answer, "response_time": response_time}
        except (json.decoder.JSONDecodeError, ValueError, TypeError):
            return None

    def call_llm_with_retries(self, chat_message: dict, retries: int = 3) -> dict:
        last_error = None
        for _ in range(retries):
            try:
                llm_response = lm.chat(
                    model=self.model_name,
                    messages=[chat_message],
                    format={
                        "type": "object",
                        "properties": {
                            "answer": {"type": "number"},
                            "response_time": {"type": "number"},
                        },
                        "required": ["answer", "response_time"],
                        "additionalProperties": False,
                    },
                )
            except Exception as e:
                last_error = e
                continue

            content = getattr(llm_response.message, "content", None)
            if content is None:
                last_error = RuntimeError("Failed to generate answer")
                continue

            answer = self.parse_response(content)
            if answer is not None:
                return answer
            else:
                last_error = RuntimeError(
                    f"LLM failed to generate valid json: {content}"
                )

        raise RuntimeError(
            f"Failed to generate answer after {retries} retries"
        ) from last_error
