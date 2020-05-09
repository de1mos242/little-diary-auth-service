import logging
from datetime import timedelta

from flask import request, jsonify, Blueprint, current_app as app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt,
)
from google_auth_oauthlib.flow import Flow

from auth_api.auth.helpers import revoke_token, is_token_revoked, add_token_to_database
from auth_api.extensions import jwt, apispec
from auth_api.models import User
from auth_api.models.roles_enum import Roles
from auth_api.services.user_service import login_internal_user

blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@blueprint.route("/login", methods=["POST"])
def login():
    """Authenticate user and return tokens

    ---
    post:
      tags:
        - auth
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                  example: myuser
                  required: true
                password:
                  type: string
                  example: P4$$w0rd!
                  required: true
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                    example: myaccesstoken
                  refresh_token:
                    type: string
                    example: myrefreshtoken
        400:
          description: bad request
      security: []
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get("username", None)
    password = request.json.get("password", None)
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = login_internal_user(username, password)
    if not user:
        return jsonify({"msg": "Bad credentials"}), 400

    access_expire = get_access_token_expire_delta(user)
    access_token = create_access_token(identity=user.id, user_claims=get_user_claims(user),
                                       expires_delta=timedelta(seconds=access_expire))
    refresh_expire = get_refresh_expire_delta(user)
    refresh_token = create_refresh_token(identity=user.id,
                                         expires_delta=timedelta(seconds=refresh_expire))
    add_token_to_database(access_token, app.config["JWT_IDENTITY_CLAIM"])
    add_token_to_database(refresh_token, app.config["JWT_IDENTITY_CLAIM"])

    ret = {"access_token": access_token, "refresh_token": refresh_token}
    return jsonify(ret), 200


def get_refresh_expire_delta(user):
    if user.role == Roles.Tech:
        refresh_expire = app.config["JWT_TECH_REFRESH_TOKEN_EXPIRE_SECONDS"]
    else:
        refresh_expire = app.config["JWT_USER_REFRESH_TOKEN_EXPIRE_SECONDS"]
    return refresh_expire


def get_access_token_expire_delta(user):
    if user.role == Roles.Tech:
        access_expire = app.config["JWT_TECH_ACCESS_TOKEN_EXPIRE_SECONDS"]
    else:
        access_expire = app.config["JWT_USER_ACCESS_TOKEN_EXPIRE_SECONDS"]
    return access_expire


@blueprint.route("/refresh", methods=["POST"])
@jwt_refresh_token_required
def refresh():
    """Get an access token from a refresh token

    ---
    post:
      tags:
        - auth
      parameters:
        - in: header
          name: Authorization
          required: true
          description: valid refresh token
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                    example: myaccesstoken
        400:
          description: bad request
        401:
          description: unauthorized
    """
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    access_expire = get_access_token_expire_delta(user)
    access_token = create_access_token(identity=current_user, user_claims=get_user_claims(user),
                                       expires_delta=timedelta(seconds=access_expire))
    ret = {"access_token": access_token}
    add_token_to_database(access_token, app.config["JWT_IDENTITY_CLAIM"])
    return jsonify(ret), 200


@blueprint.route("/revoke_access", methods=["DELETE"])
@jwt_required
def revoke_access_token():
    """Revoke an access token

    ---
    delete:
      tags:
        - auth
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: token revoked
        400:
          description: bad request
        401:
          description: unauthorized
    """
    jti = get_raw_jwt()["jti"]
    user_identity = get_jwt_identity()
    revoke_token(jti, user_identity)
    return jsonify({"message": "token revoked"}), 200


@blueprint.route("/revoke_refresh", methods=["DELETE"])
@jwt_refresh_token_required
def revoke_refresh_token():
    """Revoke a refresh token, used mainly for logout

    ---
    delete:
      tags:
        - auth
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: token revoked
        400:
          description: bad request
        401:
          description: unauthorized
    """
    jti = get_raw_jwt()["jti"]
    user_identity = get_jwt_identity()
    revoke_token(jti, user_identity)
    return jsonify({"message": "token revoked"}), 200


logger = logging.getLogger("requests_oauthlib")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


@blueprint.route("/login/google", methods=["POST"])
def login_google():
    """Authenticate by google+

    ---
    post:
      tags:
        - auth
        - google
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: string
                  required: true
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                    example: myaccesstoken
                  refresh_token:
                    type: string
                    example: myrefreshtoken
        400:
          description: bad request
      security: []
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    authorization_code = request.json.get("code", None)
    if not authorization_code:
        return jsonify({"msg": "Missing authorization_code"}), 400

    client_config = {
        "web":
            {
                "client_id": "CLIENT_ID",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_secret": "CLIENT_SECRET",
            }
    }

    scopes = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]
    flow = Flow.from_client_config(client_config, scopes)

    flow.redirect_uri = "http://localhost:3000"

    flow.fetch_token(code=authorization_code)
    session = flow.authorized_session()
    user_info = session.get('https://www.googleapis.com/userinfo/v2/me').json()
    example_resp = {
        "email": "de1m0s242@gmail.com",
        "family_name": "Yakovlev",
        "given_name": "Denis",
        "id": "100537797269200712146",
        "locale": "ru",
        "name": "Denis Yakovlev",
        "picture": "https://lh3.googleusercontent.com/a-/AOh14GijOAniLKyRe6AF5VaOLsXygb9i87dgXom8ndQsXA",
        "verified_email": True
    }

    # access_expire = get_access_token_expire_delta(app.config["JWT_USER_ACCESS_TOKEN_EXPIRE_SECONDS"])
    # access_token = create_access_token(identity=user.id, user_claims=get_user_claims(user),
    #                                    expires_delta=timedelta(seconds=access_expire))
    # refresh_expire = get_refresh_expire_delta(app.config["JWT_USER_REFRESH_TOKEN_EXPIRE_SECONDS"])
    # refresh_token = create_refresh_token(identity=user.id,
    #                                      expires_delta=timedelta(seconds=refresh_expire))
    # add_token_to_database(access_token, app.config["JWT_IDENTITY_CLAIM"])
    # add_token_to_database(refresh_token, app.config["JWT_IDENTITY_CLAIM"])

    ret = {
        "access_token": {
            "refresh_token": flow.credentials.refresh_token,
            "token_uri": flow.credentials.token_uri,
            "id_token": flow.credentials.id_token,
            "client_id": flow.credentials.client_id,
            "client_secret": flow.credentials.client_secret,
            "requires_scopes": flow.credentials.requires_scopes,
            "scopes": flow.credentials.scopes,
            "token": flow.credentials.token
        },
        "refresh_token": user_info
    }
    return jsonify(ret), 200


@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    return User.query.get(identity)


@jwt.token_in_blacklist_loader
def check_if_token_revoked(decoded_token):
    return is_token_revoked(decoded_token)


@blueprint.before_app_first_request
def register_views():
    apispec.spec.path(view=login, app=app)
    apispec.spec.path(view=refresh, app=app)
    apispec.spec.path(view=revoke_access_token, app=app)
    apispec.spec.path(view=revoke_refresh_token, app=app)

    apispec.spec.path(view=login_google, app=app)


def get_user_claims(user):
    return {"role": user.role, "uuid": user.external_uuid, "resources": user.resources}
