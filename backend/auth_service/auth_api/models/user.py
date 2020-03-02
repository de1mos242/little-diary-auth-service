from sqlalchemy.dialects.postgresql import UUID

from auth_api.extensions import db, pwd_context
from auth_api.models.roles_enum import Roles, roles_enum


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    external_uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False)
    role = db.Column(roles_enum, nullable=False, default=Roles.User)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.password = pwd_context.hash(self.password)

    def __repr__(self):
        return "<User %s %s>" % self.username, self.external_uuid
