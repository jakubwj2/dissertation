from enum import StrEnum, auto


class EventEnum(StrEnum):
    SUBMIT_ANSWER = auto()
    PROBLEM_LOGGED = auto()
    QUESTION_RECEIVED = auto()
    MODELS_RECEIVED = auto()
    MODEL_SELECTED = auto()
    CURRENT_MODEL_RECEIVED = auto()

    VISUALIZATION_DATA_RECEIVED = auto()
    API_ERROR = auto()

    USER_LOGGED_IN = auto()
    USER_LOGGED_OUT = auto()
    USER_REGISTERED = auto()
    USERS_RECEIVED = auto()
    USER_DATA_RECEIVED = auto()
    USER_WARNING = auto()
