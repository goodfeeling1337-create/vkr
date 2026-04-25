"""Move scoring fields from variants onto reference_work; drop variants table.

Revision ID: 0004
Revises: 0003
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "reference_work",
        sa.Column("scoring_mode", sa.String(32), server_default="training", nullable=False),
    )
    op.add_column(
        "reference_work",
        sa.Column(
            "allow_optional_pure_junction",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE reference_work AS rw
            SET scoring_mode = v.scoring_mode,
                allow_optional_pure_junction = v.allow_optional_pure_junction
            FROM variants AS v
            WHERE rw.variant_id = v.id
            """
        ),
    )
    insp = sa.inspect(bind)
    for fk in insp.get_foreign_keys("reference_work"):
        if fk.get("referred_table") == "variants":
            op.drop_constraint(fk["name"], "reference_work", type_="foreignkey")
            break
    else:
        raise RuntimeError("foreign key reference_work -> variants not found")
    op.drop_column("reference_work", "variant_id")
    op.drop_table("variants")


def downgrade() -> None:
    raise NotImplementedError(
        "Откат не поддерживается: потеряны связи variant_id; восстановите из бэкапа при необходимости.",
    )
