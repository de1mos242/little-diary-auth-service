from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

from auth_api.extensions import db


class InternalUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    login = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    user_id = db.Column(db.Integer, ForeignKey('user.id', ondelete='CASCADE'), unique=True)
    user = relationship("User", backref=backref("internal_users"), foreign_keys=[user_id])
