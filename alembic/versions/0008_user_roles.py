"""Add a role column to users, for the scripts.admins superuser bootstrap.

Revision ID: 0008_user_roles
Revises: 0007_redemption_failures

* ``users.role``: ``player`` (default, every signed-up player) or ``admin``
  (staff operating scripts.admins / scripts.code_batches / a future admin
  panel). No roles table: two values, no per-role permission sets yet --
  add one only when a third role is actually needed.
* CHECK constraint mirrors the application-level ``UserRole`` enum so a
  bad value can never reach the column, even from a hand-written UPDATE.

Additive only: no existing column, index or constraint is changed.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_user_roles"
down_revision: str | None = "0007_redemption_failures"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role", sa.String(length=20), nullable=False, server_default="player"
        ),
    )
    op.create_check_constraint("ck_users_role", "users", "role IN ('player', 'admin')")


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
