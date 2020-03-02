"""add role to user

Revision ID: 5658753ce8cb
Revises: d516befe650b
Create Date: 2020-03-02 16:18:16.980455+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5658753ce8cb'
down_revision = 'd516befe650b'
branch_labels = None
depends_on = None

roles = "user", "admin"


def upgrade():
    user_role_enum = postgresql.ENUM(*roles, name="user_role_enum")
    user_role_enum.create(op.get_bind())
    op.add_column('user', sa.Column('role', postgresql.ENUM(*roles, name='user_role_enum'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    op.drop_column('user', 'role')
    user_role_enum = postgresql.ENUM(*roles, name="user_role_enum")
    user_role_enum.drop(op.get_bind())
    # ### end Alembic commands ###
