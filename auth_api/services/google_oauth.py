from dataclasses import dataclass

from google_auth_oauthlib.flow import Flow


@dataclass(frozen=True)
class GoogleUserDto:
    email: str
    family_name: str
    given_name: str
    google_user_id: str
    locale: str
    name: str
    picture: str


class GoogleOauth:
    def __init__(self, settings: dict):
        self.settings = settings
        self.client_config = {"web": {"client_id": self.settings['OAUTH_GOOGLE_CLIENT_ID'],
                                      "client_secret": self.settings['OAUTH_GOOGLE_CLIENT_SECRET'],
                                      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                      "token_uri": "https://oauth2.googleapis.com/token", }}
        self.scopes = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
        ]

    def _init_flow(self) -> Flow:
        flow = Flow.from_client_config(self.client_config, self.scopes)
        flow.redirect_uri = self.settings['OAUTH_GOOGLE_REDIRECT_URI']
        return flow

    def authorize_user(self, authorization_code: str) -> GoogleUserDto:
        """
        Perform a google oauth authorization using authorization code grant
        :param authorization_code: code from web app after user authorization at google
        :return: dto with information about logged in user
        """
        flow = self._init_flow()
        flow.fetch_token(code=authorization_code)
        session = flow.authorized_session()
        user_info = session.get('https://www.googleapis.com/userinfo/v2/me').json()

        return GoogleUserDto(email=user_info['email'],
                             family_name=user_info['family_name'],
                             given_name=user_info['given_name'],
                             google_user_id=user_info['id'],
                             locale=user_info['locale'],
                             name=user_info['name'],
                             picture=user_info['picture'])
