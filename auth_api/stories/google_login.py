from dataclasses import dataclass
from enum import Enum, auto
from uuid import uuid4

from flask_sqlalchemy import SQLAlchemy
from stories import story, arguments, Success, Failure, Result, Skip

from auth_api.models import GoogleUser, User
from auth_api.models.roles_enum import Roles
from auth_api.repository.user_repository import UserRepository
from auth_api.services.google_oauth import GoogleOauth, GoogleUserDto
from auth_api.services.token_service import TokenService


@dataclass(frozen=True)
class GoogleLoginStory:
    google_oauth: GoogleOauth
    user_repository: UserRepository
    token_service: TokenService
    db: SQLAlchemy

    @story
    @arguments("user_data")
    def login(I):
        I.extract_authorization_code
        I.exchange_code_to_google_user
        I.find_existed_user
        I.sign_up
        I.sign_in
        I.create_tokens
        I.commit
        I.get_tokens

    @story
    def sign_up(I):
        I.skip_if_exists
        I.create_user
        I.create_google_user
        I.store_google_user
        I.store_user

    @story
    def sign_in(I):
        I.skip_if_not_exists
        I.put_user_in_context

    @login.failures
    class Errors(Enum):
        missing_authorization_code = auto()

    def extract_authorization_code(self, ctx):
        if 'code' not in ctx.user_data or not ctx.user_data['code']:
            return Failure(self.Errors.missing_authorization_code)
        ctx.authorization_code = ctx.user_data['code']
        return Success()

    def exchange_code_to_google_user(self, ctx):
        ctx.google_user_dto = self.google_oauth.authorize_user(ctx.authorization_code)
        return Success()

    def find_existed_user(self, ctx):
        google_user_dto: GoogleUserDto = ctx.google_user_dto
        ctx.existed_google_user = self.user_repository.get_google_user_by_google_id(google_user_dto.google_user_id)
        ctx.existed_user = ctx.existed_google_user.map(lambda google_user: google_user.user)
        return Success()

    def skip_if_exists(self, ctx):
        return ctx.existed_user.map(lambda _: Skip()).value_or(Success())

    def skip_if_not_exists(self, ctx):
        return ctx.existed_user.map(lambda _: Success()).value_or(Skip())

    def put_user_in_context(self, ctx):
        ctx.user = ctx.existed_user.unwrap()
        ctx.google_user = ctx.existed_google_user.unwrap()
        return Success()

    def create_user(self, ctx):
        google_user_dto: GoogleUserDto = ctx.google_user_dto
        ctx.user = User(username=google_user_dto.name,
                        active=True,
                        external_uuid=uuid4(),
                        role=Roles.User,
                        )
        return Success()

    def create_google_user(self, ctx):
        google_user_dto: GoogleUserDto = ctx.google_user_dto
        user: User = ctx.user
        ctx.google_user = GoogleUser(email=google_user_dto.email,
                                     name=google_user_dto.name,
                                     family_name=google_user_dto.family_name,
                                     given_name=google_user_dto.given_name,
                                     picture=google_user_dto.picture,
                                     google_user_id=google_user_dto.google_user_id,
                                     locale=google_user_dto.locale,
                                     user=user)
        return Success()

    def store_google_user(self, ctx):
        google_user: GoogleUser = ctx.google_user
        self.user_repository.store_google_user(google_user)
        self.db.session.flush()
        return Success()

    def store_user(self, ctx):
        user: User = ctx.user
        self.user_repository.store_user(user)
        self.db.session.flush()
        return Success()

    def create_tokens(self, ctx):
        user: User = ctx.user
        ctx.access_token = self.token_service.create_access_token(user)
        ctx.refresh_token = self.token_service.create_refresh_token(user)
        self.db.session.flush()
        return Success()

    def commit(self, ctx):
        self.db.session.commit()
        return Success()

    def get_tokens(self, ctx):
        return Result(dict(access_token=ctx.access_token, refresh_token=ctx.refresh_token))
