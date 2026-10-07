"""Add redemption records, coin wallets and the coin ledger.

Also adds batch tracking and voiding to redemption codes.

Revision ID: 0005_coins_and_redemptions
Revises: 0004_redemption_codes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_coins_and_redemptions"
down_revision: str | None = "0004_redemption_codes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "redemption_codes", sa.Column("batch", sa.String(length=40), nullable=True)
    )
    op.add_column(
        "redemption_codes",
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_redemption_codes_batch", "redemption_codes", ["batch"])

    op.create_table(
        "redemptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city", sa.String(length=2), nullable=False),
        sa.Column("coins_awarded", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["code_id"], ["redemption_codes.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_id", name="uq_redemptions_code_id"),
    )
    op.create_index("ix_redemptions_user_id", "redemptions", ["user_id"])

    op.create_table(
        "wallets",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("balance >= 0", name="ck_wallets_balance"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "coin_ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount <> 0", name="ck_coin_ledger_amount"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_coin_ledger_idempotency_key"),
    )
    op.create_index(
        "ix_coin_ledger_user_created",
        "coin_ledger_entries",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_coin_ledger_user_created", table_name="coin_ledger_entries")
    op.drop_table("coin_ledger_entries")
    op.drop_table("wallets")
    op.drop_index("ix_redemptions_user_id", table_name="redemptions")
    op.drop_table("redemptions")
    op.drop_index("ix_redemption_codes_batch", table_name="redemption_codes")
    op.drop_column("redemption_codes", "voided_at")
    op.drop_column("redemption_codes", "batch")
