import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from requests.exceptions import HTTPError

from api.llm_api import LLM_API
from api.server_api import ServerAPI
from modelfile import from_, system
from models.SyntheticStudent import SyntheticStudent

MODEL_NAME = "student_synthesizer:latest"
NUM_STUDENTS = 10
MAX_WORKERS = min((os.cpu_count() or 1) + 4, NUM_STUDENTS)
NUM_QUESTIONS_RANGE = (5, 150)

print(MAX_WORKERS)


def main(model_name: str = MODEL_NAME, num_students: int = NUM_STUDENTS) -> None:
    num_questions_per_student = [
        random.randint(*NUM_QUESTIONS_RANGE) for _ in range(num_students)
    ]

    serverAPI = ServerAPI()
    llmAPI = LLM_API(model_name)

    # ensure llm model and synthesizer id exist
    llmAPI.get_or_create_model(from_, system)
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
                model_name,
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
                print(
                    f"Created student: {student.name} ({users_completed}/{num_students})"
                )

    # for num_questions in num_questions_per_student:
    #     student = process_student(
    #         num_questions, synthesizer_id, existing_usernames, skills
    #     )
    #     users_completed += 1
    #     if student is not None:
    #         print(f"Created student: {student.name} ({users_completed}/{num_students})")

    end = time.time()
    print(f"Total time: {end - start}")


def process_student(
    num_questions, synthesizer_id, existing_usernames, skills, model_name
):
    serverAPI = ServerAPI()
    llmAPI = LLM_API(model_name)
    student = SyntheticStudent.create(skills, existing_usernames)
    try:
        student.id = serverAPI.post_student(student, synthesizer_id)
    except HTTPError as e:
        print(f"Failed to POST student {student.name} ({student.id})")
        print(e)
        print("Skipping student...")
        return

    for j in range(num_questions):
        # started_questions += 1
        # question_completion = started_questions / total_questions * 100
        # print(
        #         f"Progress: {question_completion:0.2f}%, students: {i + 1}/{num_students}, questions {j + 1}/{num_questions}",
        #         end=" " * 50 + "\r",
        #     )

        try:
            question_json = serverAPI.get_question(student.id)
            chat_message = llmAPI.create_chat_message(
                student.skill_states, question_json["text"]
            )

            llm_answer_json = llmAPI.call_llm_with_retries(chat_message)
            log_json = serverAPI.post_log(student.id, question_json, llm_answer_json)
        except HTTPError as e:
            print(f"Server API failed for student {student.name} ({student.id})")
            print(e)
            print("Skipping question...")
            continue
        except Exception as e:
            print(f"LLM api failed for student {student.name} ({student.id})")
            print(e)
            print("Skipping question...")
            continue

        for skill in question_json["skills"]:
            student.update_state(skill, log_json["correct"])

        student.update_student_history(log_json, question_json, llm_answer_json)
    # print(" " * 200, end="\r")
    # print("Report:")
    # print("student:", student.name, sep="\t")
    # print("skills:\t", end="")
    # print(*[skill for skill in student.skill_states.items()], sep="\n\t")
    # print("history:", end="")
    # print(*[log for log in student.history], sep="\n\t")
    # print("-" * 150)
    return student


if __name__ == "__main__":
    main()
