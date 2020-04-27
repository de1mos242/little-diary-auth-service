from flask import Blueprint, current_app as app

from auth_api.extensions import apispec
from auth_api.models import User

blueprint = Blueprint("status", __name__, url_prefix="/status")


@blueprint.route("/health", methods=["GET"])
def health():
    """Check service health

    ---
    get:
      tags:
        - status
        - health
      responses:
        204:
          description: Service is health
        500:
          description: Service has some problems
      security: []
    """
    user_probe = User.query.filter(User.username == "admin").first()
    if not user_probe:
        return "User not found", 500

    return "", 200


@blueprint.before_app_first_request
def register_views():
    apispec.spec.path(view=health, app=app)
