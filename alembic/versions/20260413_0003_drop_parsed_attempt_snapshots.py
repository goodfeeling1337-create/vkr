"""drop_parsed_attempt_snapshots

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-13

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("parsed_attempt_snapshots")


def downgrade() -> None:
    op.create_table(
        "parsed_attempt_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["student_attempts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
