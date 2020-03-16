from sqlalchemy.dialects.postgresql import ENUM

roles = "user", "admin", "tech"
roles_enum = ENUM(*roles, name="user_role_enum")


class Roles:
    [User, Admin, Tech] = roles
