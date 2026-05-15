"""Optional course label on reference_work for filtering.

Revision ID: 0005
Revises: 0004
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reference_work",
        sa.Column("course_label", sa.String(256), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reference_work", "course_label")
