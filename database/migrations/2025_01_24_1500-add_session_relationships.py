"""Add session_id foreign key to URLs and relationships

Revision ID: add_session_relationships
Revises:
Create Date: 2025-01-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# alembic revision identifiers
revision: str = 'add_session_relationships'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # add session_id column if urls table lacks it
    # use batch mode to stay sqlite compatible
    with op.batch_alter_table('urls', schema=None) as batch_op:
        batch_op.add_column(sa.Column('session_id', sa.String(length=100), nullable=True))
        batch_op.create_index(batch_op.f('ix_urls_session_id'), ['session_id'], unique=False)
        batch_op.create_foreign_key('fk_urls_session_id', 'crawl_sessions', ['session_id'], ['session_id'])


def downgrade() -> None:
    """Downgrade database schema."""
    with op.batch_alter_table('urls', schema=None) as batch_op:
        batch_op.drop_constraint('fk_urls_session_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_urls_session_id'))
        batch_op.drop_column('session_id')
