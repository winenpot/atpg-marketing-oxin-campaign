"""Add redemption_failures table for the per-account invalid-code throttle.

Revision ID: 0007_redemption_failures
Revises: 0006_batch_format_tracking

* ``redemption_failures``: append-only log of CODE_INVALID outcomes.
  Indexed on (user_id, occurred_at) so the count-in-window query is fast.
  On delete CASCADE from users so cleaning up a test/dev user is easy.
  No UPDATE/DELETE trigger needed — the application never modifies rows;
  old rows are pruned by a periodic background job (B11).

Additive only: no existing column or constraint is changed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007_redemption_failures"
down_revision: str | None = "0006_batch_format_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "redemption_failures",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_redemption_failures_user_time",
        "redemption_failures",
        ["user_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_redemption_failures_user_time", table_name="redemption_failures")
    op.drop_table("redemption_failures")
