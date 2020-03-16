from sqlalchemy.dialects.postgresql import UUID

from auth_api.commons.utils import hash_password
from auth_api.extensions import db
from auth_api.models.roles_enum import Roles, roles_enum


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    external_uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False)
    role = db.Column(roles_enum, nullable=False, default=Roles.User)
    resources = db.Column(db.ARRAY(db.Text), default=[])

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.password = hash_password(self.password)

    def update_password(self, new_password):
        self.password = hash_password(new_password)

    def __repr__(self):
        return "<User %s %s>" % (self.username, self.external_uuid)
