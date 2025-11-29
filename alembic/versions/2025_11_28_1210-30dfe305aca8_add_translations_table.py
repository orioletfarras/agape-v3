"""add_translations_table

Revision ID: 30dfe305aca8
Revises: ab96717db4e8
Create Date: 2025-11-28 12:10:34.913479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '30dfe305aca8'
down_revision: Union[str, None] = 'ab96717db4e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create translations table
    op.create_table(
        'translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=500), nullable=False),
        sa.Column('translation', sa.Text(), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_translations_id'), 'translations', ['id'], unique=False)
    op.create_index('idx_translations_key_lang', 'translations', ['key', 'language'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_translations_key_lang', table_name='translations')
    op.drop_index(op.f('ix_translations_id'), table_name='translations')
    op.drop_table('translations')
