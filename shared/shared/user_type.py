from enum import StrEnum


class UserType(StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"

VALID_VALUES = tuple(e.value for e in UserType)

def user_type_parser(value: UserType | str) -> UserType:
    """Normalize UserType

    Arguments:
        value {UserType | str} -- Value to normalize (case insensitive).

    Raises:
        ValueError: If values is neither a UserType nor a string. 
        ValueError: If values is not one of VALID_VALUES.

    Returns:
        UserType -- The normalized UserType.
    """
    if isinstance(value, UserType):
        return value
    if not isinstance(value, str):
        raise ValueError(f"Invalid user_type: {value!r}. Must be a string")
    try:
        return UserType(value.lower())
    except ValueError:
        raise ValueError(f"Invalid user_type: {value!r}. Must be one of {VALID_VALUES}")
