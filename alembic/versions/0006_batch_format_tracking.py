"""Track code format, export and freeze state on batches; add batch events.

Revision ID: 0006_batch_format_tracking
Revises: 0005_batches_wallets_ledger

Additive only (expand, migrate, contract):

* ``code_batches`` gains ``format_id`` (defaults to the pre-existing v2-b10
  shape for every row created so far), ``format_fingerprint``, export and
  freeze timestamps and the export checksum.
* ``code_batch_events``: one append-only row per batch lifecycle event
  (generated, exported, frozen, activated, voided), mirroring the coin
  ledger's append-only pattern so a leaked-batch investigation has a full
  trail. A trigger rejects UPDATE and DELETE.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_batch_format_tracking"
down_revision: str | None = "0005_batches_wallets_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFAULT_FORMAT_ID = "v2-b10"


def upgrade() -> None:
    op.add_column(
        "code_batches",
        sa.Column(
            "format_id",
            sa.String(length=40),
            nullable=False,
            server_default=_DEFAULT_FORMAT_ID,
        ),
    )
    op.add_column(
        "code_batches",
        sa.Column("format_fingerprint", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "code_batches",
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "code_batches",
        sa.Column("export_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "code_batches",
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "code_batch_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("actor", sa.String(length=200), nullable=True),
        sa.Column("detail", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["code_batches.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "event_type IN ('generated', 'exported', 'frozen', 'activated', 'voided')",
            name="ck_code_batch_events_type",
        ),
    )
    op.create_index(
        "ix_code_batch_events_batch_time",
        "code_batch_events",
        ["batch_id", "created_at"],
    )
    op.execute(
        """
        CREATE FUNCTION code_batch_events_append_only() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'code_batch_events is append-only; '
                'it is a history trail, not editable state';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER code_batch_events_no_update_or_delete
        BEFORE UPDATE OR DELETE ON code_batch_events
        FOR EACH ROW EXECUTE FUNCTION code_batch_events_append_only();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS code_batch_events_no_update_or_delete "
        "ON code_batch_events"
    )
    op.execute("DROP FUNCTION IF EXISTS code_batch_events_append_only()")
    op.drop_index("ix_code_batch_events_batch_time", table_name="code_batch_events")
    op.drop_table("code_batch_events")
    op.drop_column("code_batches", "frozen_at")
    op.drop_column("code_batches", "export_sha256")
    op.drop_column("code_batches", "exported_at")
    op.drop_column("code_batches", "format_fingerprint")
    op.drop_column("code_batches", "format_id")
