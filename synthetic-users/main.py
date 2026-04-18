import random

from faker import Faker
from requests.exceptions import HTTPError

from api.llm_api import LLM_API
from api.server_api import ServerAPI
from domain.student_generation import (
    generate_student,
    update_state,
    update_student_history,
)
from modelfile import from_, system

MODEL_NAME = "user_synthesizer:latest"
NUM_USERS = 20


def main():
    # users = requests.get(f"{API_URL}/users").json()["users"]
    # user = random.choice(users)

    num_questions_per_user = [random.randint(5, 150) for _ in range(NUM_USERS)]
    total_questions = sum(num_questions_per_user)

    started_questions = 0

    faker = Faker()
    serverAPI = ServerAPI()
    llmAPI = LLM_API(MODEL_NAME)

    llmAPI.get_or_create_model(from_, system)
    synthesizer_id = serverAPI.get_or_create_synthesizer(from_)

    existing_usernames = serverAPI.get_student_names()
    skills = serverAPI.get_skills()
    if len(skills) == 0:
        raise RuntimeError("No skills found!")

    for i in range(NUM_USERS):
        user = generate_student(faker, skills, existing_usernames)
        try:
            user["id"] = serverAPI.post_student(user, synthesizer_id)
        except HTTPError as e:
            print(f"Failed to POST user {user['name']} ({user['id']})")
            print(e)
            print("Skipping user...")
            continue

        num_questions = num_questions_per_user[i]
        user["history"] = []
        for j in range(num_questions):
            started_questions += 1
            question_completion = started_questions / total_questions * 100
            print(
                f"Progress: {question_completion:0.2f}%, users: {i + 1}/{NUM_USERS}, questions {j + 1}/{num_questions}",
                end=" " * 50 + "\r",
            )

            try:
                question_json = serverAPI.get_question(user["id"])
                chat_message = llmAPI.create_chat_message(
                    user["state"], question_json["text"]
                )

                llm_answer_json = llmAPI.call_llm_with_retries(chat_message)
                log_json = serverAPI.post_log(
                    user["id"], question_json, llm_answer_json
                )
            except HTTPError as e:
                print(f"Server API failed for user {user['name']} ({user['id']})")
                print(e)
                print("Skipping question...")
                continue
            except Exception as e:
                print(f"LLM api failed for user {user['name']} ({user['id']})")
                print(e)
                print("Skipping question...")
                continue

            for skill in question_json["skills"]:
                update_state(user, skill, log_json["correct"])

            update_student_history(user, log_json, question_json, llm_answer_json)
        # print(" " * 200, end="\r")
        # print("Report:")
        # print("user:", user["name"], sep="\t")
        # print("skills:\t", end="")
        # print(*[skill for skill in user["state"].items()], sep="\n\t")
        # print("history:", end="")
        # print(*[log for log in user["history"]], sep="\n\t")
        # print("-" * 150)


if __name__ == "__main__":
    main()
