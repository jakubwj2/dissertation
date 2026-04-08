from enum import StrEnum, auto


class EventEnum(StrEnum):
    SUBMIT_ANSWER = auto()
    PROBLEM_LOGGED = auto()
    QUESTION_RECEIVED = auto()
    MODELS_RECEIVED = auto()
    MODEL_SELECTED = auto()
    CURRENT_MODEL_RECEIVED = auto()
    USERS_RECEIVED = auto()
    USER_SELECTED = auto()
    API_ERROR = auto()
