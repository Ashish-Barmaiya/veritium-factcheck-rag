"""add simhash column to claims and create scraper_runs table

Revision ID: b4a08b900544
Revises: 24bad87021b8
Create Date: 2025-08-25 16:53:09.645116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b4a08b900544'
down_revision: Union[str, Sequence[str], None] = '24bad87021b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add simhash column
    op.add_column(
        'claims',
        sa.Column('simhash', sa.BigInteger(), nullable=True)
    )
    op.create_index('ix_claims_simhash', 'claims', ['simhash'])
    
    # Create scraper_runs table
    op.create_table(
        'scraper_runs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('scraper_name', sa.String(length=255), nullable=False),
        sa.Column('last_run', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('total_fetched', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_inserted', sa.Integer(), nullable=True, server_default='0'),
    )


def downgrade() -> None:
    # Drop scraper_runs table
    op.drop_table('scraper_runs')

    # Drop simhash column + index
    op.drop_index('ix_claims_simhash', table_name='claims')
    op.drop_column('claims', 'simhash')