from unittest import mock

from google_auth_oauthlib.flow import Flow

from auth_api.services.google_oauth import GoogleOauth


@mock.patch.object(Flow, "fetch_token")
@mock.patch.object(Flow, "authorized_session")
def test_authorize_user(get_session_mock, fetch_mock):
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

    google_oauth = GoogleOauth({"OAUTH_GOOGLE_CLIENT_ID": "100",
                                "OAUTH_GOOGLE_CLIENT_SECRET": "200",
                                "OAUTH_GOOGLE_REDIRECT_URI": "http://localhost/"})
    user = google_oauth.authorize_user("auth_code")

    assert user.email == google_response_mock["email"]
    assert user.family_name == google_response_mock["family_name"]
    assert user.google_user_id == google_response_mock["id"]
    assert user.locale == google_response_mock["locale"]
    assert user.name == google_response_mock["name"]
    assert user.picture == google_response_mock["picture"]

    fetch_mock.assert_called_with(code="auth_code")
    get_session_mock.assert_called()
    get_session_mock.return_value.get.assert_called()
    get_session_mock.return_value.get.return_value.json.assert_called()
