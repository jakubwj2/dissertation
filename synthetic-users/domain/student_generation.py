import random

from faker import Faker

from core.math_helpers import clamp_and_round
from core.names import increment_trailing_number


def generate_student(
    faker: Faker, skills: list[str], existing_usernames: list[str]
) -> dict:

    new_username = faker.user_name()

    if new_username in existing_usernames:
        new_username = increment_trailing_number(new_username)

    user = {
        "name": new_username,
        "state": {},
        "history": [],
    }
    prior_overall_mastery = random.uniform(0, 0.75)
    prior_overall_learning_rate = random.uniform(0.01, 0.1)

    for skill in skills:
        skill_mastery = prior_overall_mastery + random.gauss(0, 0.1)
        skill_mastery = clamp_and_round(skill_mastery, 0.05, 0.75)

        skill_learning_rate = prior_overall_learning_rate + random.gauss(0, 0.025)
        skill_learning_rate = clamp_and_round(skill_learning_rate, 0.01, 0.1)

        skill_state = {
            "mastery": skill_mastery,
            "learn_rate": skill_learning_rate,
            "guess_rate": round(random.uniform(0.05, 0.2), 2),
            "slip_rate": round(random.uniform(0.01, 0.1), 2),
            # "forget_rate": round(random.uniform(0.0, 0.05), 2),
        }
        user["state"][skill] = skill_state

    return user


def update_state(user: dict, skill: str, correct: bool) -> None:
    """Apply a BKT-style posterior update to one skill after a student response."""
    skill_state = user["state"][skill]

    eps = 1e-8
    p_L = skill_state["mastery"] + eps
    p_T = skill_state["learn_rate"] + eps
    p_G = skill_state["guess_rate"] + eps
    p_S = skill_state["slip_rate"] + eps

    if correct:
        posterior = (p_L * (1 - p_S)) / ((p_L * (1 - p_S)) + ((1 - p_L) * p_G))
    else:
        posterior = (p_L * p_S) / ((p_L * p_S) + ((1 - p_L) * (1 - p_G)))

    new_mastery = posterior + (1 - posterior) * p_T
    skill_state["mastery"] = clamp_and_round(new_mastery, 0.05, 0.9999, 4)


def update_student_history(
    user: dict, log_response: dict, question: dict, llm_answer: dict
):
    user["history"].append({
        "log_id": log_response["id"],
        "question": question["text"],
        "correct": log_response["correct"],
        "answer": llm_answer["answer"],
        "response_time": llm_answer["response_time"],
    })
