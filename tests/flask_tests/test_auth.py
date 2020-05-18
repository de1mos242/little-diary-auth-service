import json
from datetime import datetime, timedelta
from typing import Optional
from unittest import mock

from flask_jwt_extended import decode_token
from google_auth_oauthlib.flow import Flow

from auth_api.models import User, GoogleUser
from auth_api.models.roles_enum import Roles


def test_revoke_access_token(client, admin_headers):
    resp = client.delete("/auth/revoke_access", headers=admin_headers)
    assert resp.status_code == 200

    resp = client.get("/api/v1/users", headers=admin_headers)
    assert resp.status_code == 401


def test_revoke_refresh_token(client, admin_refresh_headers):
    resp = client.delete("/auth/revoke_refresh", headers=admin_refresh_headers)
    assert resp.status_code == 200

    resp = client.post("/auth/refresh", headers=admin_refresh_headers)
    assert resp.status_code == 401


def test_login(app, client, regular_user):
    data = {
        'username': regular_user.username,
        'password': 'user_password'
    }
    resp = client.post(
        '/auth/login',
        data=json.dumps(data),
        headers={'content-type': 'application/json'}
    )
    assert resp.status_code == 200

    tokens = json.loads(resp.get_data(as_text=True))
    access_token = tokens['access_token']
    decoded = decode_token(access_token)
    assert decoded['user_claims']['uuid'] == str(regular_user.external_uuid)
    assert decoded['user_claims']['role'] == Roles.User
    token_expire_delta = timedelta(seconds=app.config["JWT_USER_ACCESS_TOKEN_EXPIRE_SECONDS"])
    expect_expire = datetime.now() + token_expire_delta
    minute_delta = timedelta(minutes=1)
    assert expect_expire - minute_delta < datetime.fromtimestamp(decoded['exp']) < expect_expire + minute_delta

    refresh_token = tokens['refresh_token']
    decoded_refresh = decode_token(refresh_token)
    token_expire_delta = timedelta(seconds=app.config["JWT_USER_REFRESH_TOKEN_EXPIRE_SECONDS"])
    expect_expire = datetime.now() + token_expire_delta
    minute_delta = timedelta(minutes=1)
    assert expect_expire - minute_delta < datetime.fromtimestamp(decoded_refresh['exp']) < expect_expire + minute_delta


def test_tech_login(app, client, tech_user):
    data = {
        'username': tech_user.username,
        'password': 'tech'
    }
    resp = client.post(
        '/auth/login',
        data=json.dumps(data),
        headers={'content-type': 'application/json'}
    )
    assert resp.status_code == 200

    tokens = json.loads(resp.get_data(as_text=True))
    access_token = tokens['access_token']
    decoded = decode_token(access_token)
    assert decoded['user_claims']['uuid'] == str(tech_user.external_uuid)
    assert decoded['user_claims']['role'] == Roles.Tech
    assert decoded['user_claims']['resources'] == tech_user.resources
    token_expire_delta = timedelta(seconds=app.config["JWT_TECH_ACCESS_TOKEN_EXPIRE_SECONDS"])
    expect_expire = datetime.now() + token_expire_delta
    minute_delta = timedelta(minutes=1)
    assert expect_expire - minute_delta < datetime.fromtimestamp(decoded['exp']) < expect_expire + minute_delta

    refresh_token = tokens['refresh_token']
    decoded_refresh = decode_token(refresh_token)
    token_expire_delta = timedelta(seconds=app.config["JWT_TECH_REFRESH_TOKEN_EXPIRE_SECONDS"])
    expect_expire = datetime.now() + token_expire_delta
    minute_delta = timedelta(minutes=1)
    assert expect_expire - minute_delta < datetime.fromtimestamp(decoded_refresh['exp']) < expect_expire + minute_delta


@mock.patch.object(Flow, "fetch_token")
@mock.patch.object(Flow, "authorized_session")
def test_google_sign_up(get_session_mock, _, client, db):
    google_response_mock = {
        "email": "de1m0s242@gmail.com",
        "family_name": "Yakovlev",
        "given_name": "Denis",
        "id": "100537797269200712146",
        "locale": "ru",
        "name": "Denis Yakovlev",
        "picture": "https://lh3.googleusercontent.com/a-/AOh14GijOAniLKyRe6AF5VaOLsXygb9i87dgXom8ndQsXA",
        "verified_email": True
    }
    get_session_mock.return_value.get.return_value.json.return_value = google_response_mock

    data = dict(code="google_auth_code")
    resp = client.post(
        '/auth/login/google',
        data=json.dumps(data),
        headers={'content-type': 'application/json'}
    )
    assert resp.status_code == 200, resp.data

    tokens = json.loads(resp.get_data(as_text=True))
    access_token = tokens['access_token']
    decoded = decode_token(access_token)
    assert decoded['user_claims']['role'] == Roles.User

    user_uuid = decoded['user_claims']['uuid']

    refresh_token = tokens['refresh_token']
    decoded_refresh = decode_token(refresh_token)
    assert decoded_refresh is not None

    user = db.session.query(User).filter(User.external_uuid == user_uuid).first()
    assert user is not None
    assert user.role == Roles.User
    assert user.username == google_response_mock['name']
    assert user.active is True

    google_user: Optional[GoogleUser] = user.google_user
    assert google_user is not None
    assert google_user.google_user_id == google_response_mock['id']
    assert google_user.email == google_response_mock['email']
    assert google_user.family_name == google_response_mock['family_name']
    assert google_user.given_name == google_response_mock['given_name']
    assert google_user.locale == google_response_mock['locale']
    assert google_user.name == google_response_mock['name']
    assert google_user.picture == google_response_mock['picture']


@mock.patch.object(Flow, "fetch_token")
@mock.patch.object(Flow, "authorized_session")
def test_google_sign_in(get_session_mock, _, google_user_factory, client, db):
    google_response_mock = {
        "email": "de1m0s242@gmail.com",
        "family_name": "Yakovlev",
        "given_name": "Denis",
        "id": "100537797269200712146",
        "locale": "ru",
        "name": "Denis Yakovlev",
        "picture": "https://lh3.googleusercontent.com/a-/AOh14GijOAniLKyRe6AF5VaOLsXygb9i87dgXom8ndQsXA",
        "verified_email": True
    }
    get_session_mock.return_value.get.return_value.json.return_value = google_response_mock

    google_user = google_user_factory(google_user_id=google_response_mock['id'])
    db.session.add(google_user)
    db.session.commit()
    user = google_user.user

    data = dict(code="google_auth_code")
    resp = client.post(
        '/auth/login/google',
        data=json.dumps(data),
        headers={'content-type': 'application/json'}
    )
    assert resp.status_code == 200, resp.data

    tokens = json.loads(resp.get_data(as_text=True))
    access_token = tokens['access_token']
    decoded = decode_token(access_token)
    assert decoded['user_claims']['uuid'] == str(user.external_uuid)
    assert decoded['user_claims']['role'] == Roles.User
