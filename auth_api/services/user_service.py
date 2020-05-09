from typing import List, Optional
from uuid import uuid4, UUID

from auth_api.commons.utils import hash_password
from auth_api.extensions import db, pwd_context
from auth_api.models import User, InternalUser
from auth_api.models.roles_enum import Roles


def create_internal_user(username: str, email: str, password: str, role: Roles,
                         resources: Optional[List[str]] = None,
                         external_uuid: Optional[UUID] = None) -> User:
    user = User(username=username,
                active=True,
                external_uuid=external_uuid or uuid4(),
                resources=resources,
                role=role)

    internal_user = InternalUser(login=username, email=email, password=hash_password(password), user=user)
    db.session.add(user)
    db.session.add(internal_user)
    return user


def update_internal_user(user: User,
                         username: str = None,
                         email: str = None,
                         role: Roles = None,
                         resources: Optional[List[str]] = None,
                         **kwargs):
    internal_user = user.internal_user
    if not internal_user:
        raise Exception(f"Internal user not found for {user.external_uuid}")

    if username:
        user.username = username
        internal_user.login = username
    if role:
        user.role = role
    if resources:
        user.resources = resources
    if email:
        internal_user.email = email


def update_password(user: User, new_password: str):
    internal_user = user.internal_user
    if not internal_user:
        raise Exception(f"Internal user not found for {user.external_uuid}")

    internal_user.password = hash_password(new_password)


def login_internal_user(login: str, password: str) -> Optional[User]:
    internal_user: InternalUser = InternalUser.query.filter_by(login=login).first()
    if internal_user is None or not pwd_context.verify(password, internal_user.password):
        return None
    return internal_user.user


def is_login_free(login: str, exclude_id: Optional[int] = None) -> bool:
    query_filter = InternalUser.query.filter(InternalUser.login == login)
    if exclude_id:
        query_filter = query_filter.filter(InternalUser.user_id != exclude_id)
    return query_filter.first() is None


def is_email_free(email: str, exclude_id: Optional[int] = None) -> bool:
    query_filter = InternalUser.query.filter(InternalUser.email == email)
    if exclude_id:
        query_filter = query_filter.filter(InternalUser.user_id != exclude_id)
    return query_filter.first() is None
