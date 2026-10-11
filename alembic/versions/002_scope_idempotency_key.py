"""Scope idempotency keys per user and store a request fingerprint

Revision ID: 002_scope_idempotency
Revises: 001_initial
Create Date: 2026-10-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002_scope_idempotency'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace the global unique index with a (user_id, idempotency_key) constraint."""
    op.add_column('transactions', sa.Column('request_fingerprint', sa.String(64), nullable=True))
    op.drop_index('ix_transactions_idempotency_key', table_name='transactions')
    op.create_index('ix_transactions_idempotency_key', 'transactions', ['idempotency_key'])
    op.create_unique_constraint(
        'uq_transactions_user_idempotency_key', 'transactions', ['user_id', 'idempotency_key']
    )


def downgrade() -> None:
    """Restore the global unique index."""
    op.drop_constraint('uq_transactions_user_idempotency_key', 'transactions', type_='unique')
    op.drop_index('ix_transactions_idempotency_key', table_name='transactions')
    op.create_index('ix_transactions_idempotency_key', 'transactions', ['idempotency_key'], unique=True)
    op.drop_column('transactions', 'request_fingerprint')
