"""Add code batches, wallets and the append-only coin ledger.

Revision ID: 0005_batches_wallets_ledger
Revises: 0004_redemption_codes

* ``code_batches``: one row per print run; a code is redeemable only while
  its batch is ``active`` (activate at launch, ``void`` a leaked batch).
* ``redemption_codes.batch_id``: nullable so pre-existing v1 rows survive;
  rows without a batch can never be redeemed.
* ``wallets``: cached coin balance, ``CHECK (balance >= 0)``.
* ``coin_ledger_entries``: source of truth for coins; a trigger rejects
  UPDATE and DELETE so history can only grow.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_batches_wallets_ledger"
down_revision: str | None = "0004_redemption_codes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "code_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city", sa.String(length=2), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("coins_per_code", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantity > 0", name="ck_code_batches_quantity_positive"),
        sa.CheckConstraint(
            "coins_per_code >= 0", name="ck_code_batches_coins_non_negative"
        ),
        sa.CheckConstraint(
            "status IN ('generated', 'active', 'void')",
            name="ck_code_batches_status",
        ),
    )

    op.add_column(
        "redemption_codes",
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_redemption_codes_batch_id",
        "redemption_codes",
        "code_batches",
        ["batch_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_redemption_codes_batch_id", "redemption_codes", ["batch_id"])
    op.create_index(
        "ix_redemption_codes_redeemer_time",
        "redemption_codes",
        ["redeemed_by_user_id", "redeemed_at"],
        postgresql_where=sa.text("redeemed_by_user_id IS NOT NULL"),
    )

    op.create_table(
        "wallets",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.BigInteger(), nullable=False),
        sa.Column("lifetime_earned", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint("balance >= 0", name="ck_wallets_balance_non_negative"),
        sa.CheckConstraint(
            "lifetime_earned >= 0", name="ck_wallets_lifetime_earned_non_negative"
        ),
    )

    op.create_table(
        "coin_ledger_entries",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
        sa.CheckConstraint(
            "amount <> 0", name="ck_coin_ledger_entries_amount_non_zero"
        ),
    )
    op.create_index(
        "ix_coin_ledger_entries_user_time",
        "coin_ledger_entries",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_coin_ledger_entries_created_at", "coin_ledger_entries", ["created_at"]
    )
    op.execute(
        """
        CREATE FUNCTION coin_ledger_entries_append_only() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'coin_ledger_entries is append-only; '
                'record a compensating entry instead';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER coin_ledger_entries_no_update_or_delete
        BEFORE UPDATE OR DELETE ON coin_ledger_entries
        FOR EACH ROW EXECUTE FUNCTION coin_ledger_entries_append_only();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS coin_ledger_entries_no_update_or_delete "
        "ON coin_ledger_entries"
    )
    op.execute("DROP FUNCTION IF EXISTS coin_ledger_entries_append_only()")
    op.drop_index("ix_coin_ledger_entries_created_at", table_name="coin_ledger_entries")
    op.drop_index("ix_coin_ledger_entries_user_time", table_name="coin_ledger_entries")
    op.drop_table("coin_ledger_entries")
    op.drop_table("wallets")
    op.drop_index("ix_redemption_codes_redeemer_time", table_name="redemption_codes")
    op.drop_index("ix_redemption_codes_batch_id", table_name="redemption_codes")
    op.drop_constraint(
        "fk_redemption_codes_batch_id", "redemption_codes", type_="foreignkey"
    )
    op.drop_column("redemption_codes", "batch_id")
    op.drop_table("code_batches")
