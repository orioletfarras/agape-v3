"""rename event title to name and start_date to event_date

Revision ID: ab96717db4e8
Revises: 7cbd669685c9
Create Date: 2025-11-28 05:17:39.794633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab96717db4e8'
down_revision: Union[str, None] = '7cbd669685c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename columns in events table (MySQL requires existing_type)
    op.alter_column('events', 'title',
                    new_column_name='name',
                    existing_type=sa.String(255),
                    existing_nullable=False)
    op.alter_column('events', 'start_date',
                    new_column_name='event_date',
                    existing_type=sa.DateTime(),
                    existing_nullable=False)


def downgrade() -> None:
    # Rename columns back to original names
    op.alter_column('events', 'name',
                    new_column_name='title',
                    existing_type=sa.String(255),
                    existing_nullable=False)
    op.alter_column('events', 'event_date',
                    new_column_name='start_date',
                    existing_type=sa.DateTime(),
                    existing_nullable=False)
