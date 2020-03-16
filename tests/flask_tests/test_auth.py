import json
from datetime import datetime, timedelta

from flask_jwt_extended import decode_token

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
