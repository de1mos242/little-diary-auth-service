from dataclasses import dataclass
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

from auth_api.models import TokenBlacklist


@dataclass(frozen=True)
class TokenRepository:
    db: SQLAlchemy

    def add_token_to_database(self, decoded_token: dict):
        jti = decoded_token["jti"]
        token_type = decoded_token["type"]
        user_identity = decoded_token["identity"]
        expires = datetime.fromtimestamp(decoded_token["exp"])
        revoked = False

        db_token = TokenBlacklist(
            jti=jti,
            token_type=token_type,
            user_id=user_identity,
            expires=expires,
            revoked=revoked,
        )
        self.db.session.add(db_token)
