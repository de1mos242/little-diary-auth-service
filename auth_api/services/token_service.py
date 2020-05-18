from dataclasses import dataclass
from datetime import timedelta

from flask_jwt_extended import create_access_token, decode_token, create_refresh_token

from auth_api.models import User
from auth_api.models.roles_enum import Roles
from auth_api.repository.token_repository import TokenRepository


@dataclass(frozen=True)
class TokenService:
    settings: dict
    token_repository: TokenRepository

    def create_access_token(self, user: User) -> str:
        access_expire = self._get_access_token_expire_delta(user)
        access_token = create_access_token(identity=user.id,
                                           user_claims=self._get_user_claims(user),
                                           expires_delta=timedelta(seconds=access_expire))
        decoded_token = decode_token(access_token)
        self.token_repository.add_token_to_database(decoded_token)
        return access_token

    def create_refresh_token(self, user: User) -> str:
        refresh_expire = self._get_refresh_expire_delta(user)
        refresh_token = create_refresh_token(identity=user.id,
                                             expires_delta=timedelta(seconds=refresh_expire))
        decoded_token = decode_token(refresh_token)
        self.token_repository.add_token_to_database(decoded_token)
        return refresh_token

    def _get_access_token_expire_delta(self, user: User):
        if user.role == Roles.Tech:
            access_expire = self.settings["JWT_TECH_ACCESS_TOKEN_EXPIRE_SECONDS"]
        else:
            access_expire = self.settings["JWT_USER_ACCESS_TOKEN_EXPIRE_SECONDS"]
        return access_expire

    def _get_refresh_expire_delta(self, user):
        if user.role == Roles.Tech:
            refresh_expire = self.settings["JWT_TECH_REFRESH_TOKEN_EXPIRE_SECONDS"]
        else:
            refresh_expire = self.settings["JWT_USER_REFRESH_TOKEN_EXPIRE_SECONDS"]
        return refresh_expire

    @staticmethod
    def _get_user_claims(user: User) -> dict:
        return {"role": user.role, "uuid": user.external_uuid, "resources": user.resources}
