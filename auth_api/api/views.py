from flask import Blueprint, current_app, jsonify
from flask_restful import Api
from marshmallow import ValidationError

from auth_api.api.resources import UserResource, UserList
from auth_api.api.resources.user import UserSchema, UserPassword, PasswordChangeSchema, UserPublicInfo, UserPublicSchema
from auth_api.extensions import apispec

blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(blueprint)

api.add_resource(UserPassword, "/users/<int:user_id>/password")
api.add_resource(UserPublicInfo, "/users/public")
api.add_resource(UserResource, "/users/<int:user_id>")
api.add_resource(UserList, "/users")


@blueprint.before_app_first_request
def register_views():
    apispec.spec.components.schema("UserSchema", schema=UserSchema)
    apispec.spec.components.schema("UserPublicSchema", schema=UserPublicSchema)
    apispec.spec.components.schema("PasswordChangeSchema", schema=PasswordChangeSchema)
    apispec.spec.path(view=UserPassword, app=current_app)
    apispec.spec.path(view=UserPublicInfo, app=current_app)
    apispec.spec.path(view=UserResource, app=current_app)
    apispec.spec.path(view=UserList, app=current_app)


@blueprint.errorhandler(ValidationError)
def handle_marshmallow_error(e):
    """Return json error for marshmallow validation errors.

    This will avoid having to try/catch ValidationErrors in all endpoints, returning
    correct JSON response with associated HTTP 400 Status (https://tools.ietf.org/html/rfc7231#section-6.5.1)
    """
    return jsonify(e.messages), 400
