from dependencies import Injector
from flask import Flask
from flask_cors import CORS

from auth_api import auth, api, status
from auth_api.extensions import db, jwt, migrate, apispec
from auth_api.repository.token_repository import TokenRepository
from auth_api.repository.user_repository import UserRepository
from auth_api.services.google_oauth import GoogleOauth
from auth_api.services.token_service import TokenService
from auth_api.stories.google_login import GoogleLoginStory


def create_app(testing=False, cli=False):
    """Application factory, used to create application
    """
    app = Flask("auth_api")
    app.config.from_object("auth_api.config")

    if testing is True:
        app.config["TESTING"] = True

    configure_extensions(app, cli)
    configure_apispec(app)
    register_blueprints(app)
    CORS(app)
    configure_di_container(app)

    return app


def configure_extensions(app, cli):
    """configure flask extensions
    """
    db.init_app(app)
    jwt.init_app(app)

    if cli is True:
        migrate.init_app(app, db)


def configure_apispec(app):
    """Configure APISpec for swagger support
    """
    apispec.init_app(app, security=[{"jwt": []}])
    apispec.spec.components.security_scheme(
        "jwt", {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    )
    apispec.spec.components.schema(
        "PaginatedResult",
        {
            "properties": {
                "total": {"type": "integer"},
                "pages": {"type": "integer"},
                "next": {"type": "string"},
                "prev": {"type": "string"},
            }
        },
    )


def configure_di_container(app):
    app.extensions['di_container'] = DiContainer.let(db=db, settings=app.config)


def register_blueprints(app):
    """register all blueprints for application
    """
    app.register_blueprint(auth.views.blueprint)
    app.register_blueprint(status.views.blueprint)
    app.register_blueprint(api.views.blueprint)


class DiContainer(Injector):
    """
    db and settings should be set in runtime by make `let` method
    DiContainer.let(db=db, settings=app.config)
    """
    google_login_story = GoogleLoginStory
    user_repository = UserRepository
    token_service = TokenService
    token_repository = TokenRepository
    google_oauth = GoogleOauth
