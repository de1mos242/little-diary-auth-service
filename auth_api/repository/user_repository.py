from typing import Optional

from returns.maybe import maybe

from auth_api.extensions import db
from auth_api.models import GoogleUser, User


class UserRepository:

    @staticmethod
    @maybe
    def get_google_user_by_google_id(google_id: str) -> Optional[GoogleUser]:
        return db.session.query(GoogleUser).filter(GoogleUser.google_user_id == google_id).first()

    @staticmethod
    def store_google_user(google_user: GoogleUser):
        db.session.add(google_user)

    @staticmethod
    def store_user(user: User):
        db.session.add(user)
