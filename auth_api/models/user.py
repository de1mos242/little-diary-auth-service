from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy.dialects.postgresql import UUID

from auth_api.extensions import db
from auth_api.models.roles_enum import Roles, roles_enum

# https://stackoverflow.com/a/39757388/1641461
if TYPE_CHECKING:
    from auth_api.models import InternalUser


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    external_uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False)
    role = db.Column(roles_enum, nullable=False, default=Roles.User)
    resources = db.Column(db.ARRAY(db.Text), default=[])

    def __repr__(self):
        return "<User %s %s>" % (self.username, self.external_uuid)

    @property
    def internal_user(self) -> Optional[InternalUser]:
        if self.internal_users:
            return self.internal_users[0]
        return None
