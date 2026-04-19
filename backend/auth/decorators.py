from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request
from shared.user_type import UserType, user_type_parser


def role_required(*allowed_roles: UserType):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return {"msg": "Access denied"}, 403
            claims = get_jwt()
            user_type = claims.get("user_type")
            if user_type is None:
                return {"msg": "Access denied"}, 403
            user_type = user_type_parser(str(user_type))
            if user_type not in allowed_roles:
                return {"msg": "Access denied"}, 403
            return fn(*args, **kwargs)

        return decorator

    return wrapper
