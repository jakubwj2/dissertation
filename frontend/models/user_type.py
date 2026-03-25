from enum import Enum


class UserType(Enum):
    STUDENT = "student"
    TEACHER = "teacher"


def user_type_parser(value):
    """Parse and validate user_type enum value"""
    try:
        return UserType(value.lower())  # Convert to enum
    except ValueError:
        valid_values = [e.value for e in UserType]
        raise ValueError(f"Invalid user_type: {value}. Must be one of {valid_values}")
