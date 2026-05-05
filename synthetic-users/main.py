import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from requests.exceptions import HTTPError

from api.llm_api import LLM_API
from api.server_api import ServerAPI
from modelfile import system
from models.SyntheticStudent import SyntheticStudent

NUM_STUDENTS = 100
# MAX_WORKERS = min((os.cpu_count() or 1) + 4, NUM_STUDENTS)
MAX_WORKERS = 10
NUM_QUESTIONS_RANGE = (5, 100)
CREDENTIALS_FILE = "credentials.txt"


def main(from_: str, num_students: int = NUM_STUDENTS) -> None:
    num_questions_per_student = [
        random.randint(*NUM_QUESTIONS_RANGE) for _ in range(num_students)
    ]

    serverAPI = ServerAPI()

    # ensure llm model and synthesizer id exist
    synthesizer_id = serverAPI.get_or_create_synthesizer(from_)

    existing_usernames = serverAPI.get_student_names()
    skills = serverAPI.get_skills()
    if len(skills) == 0:
        raise RuntimeError("No skills found!")

    users_completed = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(
                process_student,
                num_questions,
                synthesizer_id,
                existing_usernames,
                skills,
                from_,
            )
            for num_questions in num_questions_per_student
        ]

        for future in as_completed(futures):
            try:
                student = future.result()
            except Exception as e:
                print(f"Worker failed for student: {e}")
                continue
            users_completed += 1

            if student is not None:
                with open(CREDENTIALS_FILE, "a") as f:
                    f.write(f"{student.name}:{student.password}\n")
                print(
                    f"Created student: {student.name} ({users_completed}/{num_students})"
                )

    end = time.time()
    print(f"Total time: {end - start}")


def process_student(num_questions, synthesizer_id, existing_usernames, skills, from_):
    serverAPI = ServerAPI()
    llmAPI = LLM_API(from_, system)
    student = SyntheticStudent.create(skills, existing_usernames)
    try:
        serverAPI.register_student(student, synthesizer_id)
        serverAPI.login_student(student)
    except HTTPError as e:
        print(f"Failed to POST student {student.name}")
        print(e)
        print("Skipping student...")
        return

    for _ in range(num_questions):
        try:
            question_json = serverAPI.get_question()
            chat_message = llmAPI.create_chat_message(
                student.skill_states, question_json["text"]
            )

            llm_answer_json = llmAPI.call_llm_with_retries(chat_message)
            log_json = serverAPI.post_log(question_json, llm_answer_json)
        except HTTPError as e:
            print(f"Server API failed for student {student.name}")
            print(e)
            print("Skipping question...")
            continue
        except Exception as e:
            print(f"LLM api failed for student {student.name}")
            print(e)
            import traceback
            traceback.print_exc()
            print("Skipping question...")
            continue

        for skill in question_json["skills"]:
            student.update_state(skill, log_json["correct"])

        student.update_student_history(log_json, question_json, llm_answer_json)
    return student


if __name__ == "__main__":
    models = [
        # "llama3.2:latest",  # 3b
        # "mistral:latest",  # 7b
        # "qwen2.5:latest",  # 7b
        # "deepseek-r1:1.5b",  # 1.5b
        "gemma3:1b",  # 4b
    ]
    for from_ in models:
        print(f"Using model: {from_}")
        main(from_)
