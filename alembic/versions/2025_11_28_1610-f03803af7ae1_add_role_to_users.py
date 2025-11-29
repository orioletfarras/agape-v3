"""add_role_to_users

Revision ID: f03803af7ae1
Revises: 30dfe305aca8
Create Date: 2025-11-28 16:10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f03803af7ae1'
down_revision: Union[str, None] = '30dfe305aca8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column to users table
    op.add_column('users', sa.Column('role', sa.String(50), nullable=True, server_default='user'))
    
    # Set role to superadmin for oriol@penwin.org
    op.execute("UPDATE users SET role = 'superadmin' WHERE email = 'oriol@penwin.org'")


def downgrade() -> None:
    # Remove role column
    op.drop_column('users', 'role')
