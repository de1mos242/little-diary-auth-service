from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

from auth_api.extensions import db


class GoogleUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(80))
    name = db.Column(db.Text, nullable=False)
    family_name = db.Column(db.Text)
    given_name = db.Column(db.Text)
    picture = db.Column(db.Text)
    google_user_id = db.Column(db.String(80), unique=True, nullable=False)
    locale = db.Column(db.String(80))

    user_id = db.Column(db.Integer, ForeignKey('user.id', ondelete='CASCADE'), unique=True)
    user = relationship("User", backref=backref("google_users"), foreign_keys=[user_id])
