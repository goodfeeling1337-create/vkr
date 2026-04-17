"""reference_work max_attempts and deadline

Revision ID: 0002
Revises: 0001
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reference_work", sa.Column("max_attempts", sa.Integer(), nullable=True))
    op.add_column("reference_work", sa.Column("deadline_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("reference_work", "deadline_at")
    op.drop_column("reference_work", "max_attempts")
