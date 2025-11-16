"""add_is_pinned_to_conversations

Revision ID: 8e36fbb3d452
Revises: cd999454bfc3
Create Date: 2025-11-16 15:45:29.584690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e36fbb3d452'
down_revision: Union[str, None] = 'cd999454bfc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_pinned column to conversations table
    op.add_column('conversations', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_pinned column from conversations table
    op.drop_column('conversations', 'is_pinned')
