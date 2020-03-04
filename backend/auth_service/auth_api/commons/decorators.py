from functools import wraps

import flask_restful
from flask_jwt_extended import get_current_user

from auth_api.models.roles_enum import Roles


def user_or_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user.role == Roles.Admin:
            return func(*args, **kwargs)
        # pylint: disable=used-before-assignment
        if (request_user_id := kwargs.get('user_id', None)) and request_user_id == user.id:
            return func(*args, **kwargs)
        return flask_restful.abort(403)

    return wrapper


def admin_role(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user.role == Roles.Admin:
            return func(*args, **kwargs)
        return flask_restful.abort(403)

    return wrapper
