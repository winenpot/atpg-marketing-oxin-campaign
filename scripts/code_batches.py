"""List, activate, void, export or freeze code batches; show their history.

Usage::

    uv run python -m scripts.code_batches list
    uv run python -m scripts.code_batches formats
    uv run python -m scripts.code_batches history <batch-id>
    uv run python -m scripts.code_batches export <batch-id> --csv-sha256 <hash>
    uv run python -m scripts.code_batches freeze <batch-id>
    uv run python -m scripts.code_batches activate <batch-id>
    uv run python -m scripts.code_batches void <batch-id>

``activate`` makes a ``generated`` batch redeemable. ``void`` stops every
unredeemed code of a batch immediately (leaked printer file, misprint);
codes already redeemed stay redeemed and keep their entries and coins.

``export`` records that the printer CSV for a batch was produced (its
SHA-256, so the printer's confirmation can be checked against it) and
freezes the batch's code format: once frozen, that format's spec must never
change (``app/domain/codes.py`` refuses to start if it does). ``freeze``
freezes a batch without recording an export, for a batch exported by other
means. Every state change is also written to ``code_batch_events``, an
append-only table, so a leaked-batch investigation has a full trail.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.domain.code_batches import BatchEventType, BatchStatus
from app.domain.codes import FORMATS, FormatRegistryError, get_format
from app.infrastructure.postgres.database import PostgreSQLAdapter
from app.infrastructure.postgres.models import (
    CodeBatchEventModel,
    CodeBatchModel,
    RedemptionCodeModel,
)


async def list_batches(factory: async_sessionmaker[AsyncSession]) -> list[str]:
    redeemed = func.sum(
        case((RedemptionCodeModel.redeemed_at.is_not(None), 1), else_=0)
    )
    statement = (
        select(
            CodeBatchModel.id,
            CodeBatchModel.city,
            CodeBatchModel.status,
            CodeBatchModel.coins_per_code,
            func.count(RedemptionCodeModel.id),
            redeemed,
            CodeBatchModel.label,
            CodeBatchModel.format_id,
            CodeBatchModel.frozen_at,
        )
        .outerjoin(
            RedemptionCodeModel, RedemptionCodeModel.batch_id == CodeBatchModel.id
        )
        .group_by(CodeBatchModel.id)
        .order_by(CodeBatchModel.created_at)
    )
    async with factory() as session:
        rows = (await session.execute(statement)).all()
    return [
        f"{row[0]}  {row[1]}  {row[2]:<9}  coins={row[3]:<4} codes={row[4]:<8} "
        f"redeemed={row[5] or 0:<8} format={row[7]:<10} "
        f"frozen={'yes' if row[8] else 'no':<3} {row[6]}"
        for row in rows
    ]


def list_formats() -> list[str]:
    """Every registered code format, for picking one with ``--format``."""
    return [
        f"{fmt.format_id}  length={fmt.canonical_length:<3} "
        f"entropy={fmt.entropy_bits:.0f}bits  grouping={fmt.grouping}  "
        f"fingerprint={fmt.fingerprint()[:12]}"
        for fmt in FORMATS.values()
    ]


async def batch_history(
    factory: async_sessionmaker[AsyncSession], batch_id: UUID
) -> list[str]:
    statement = (
        select(
            CodeBatchEventModel.created_at,
            CodeBatchEventModel.event_type,
            CodeBatchEventModel.actor,
            CodeBatchEventModel.detail,
        )
        .where(CodeBatchEventModel.batch_id == batch_id)
        .order_by(CodeBatchEventModel.created_at)
    )
    async with factory() as session:
        rows = (await session.execute(statement)).all()
    return [
        f"{created_at.isoformat()}  {event_type:<10} actor={actor or '-':<20} "
        f"{detail or ''}"
        for created_at, event_type, actor, detail in rows
    ]


async def set_status(
    factory: async_sessionmaker[AsyncSession],
    batch_id: UUID,
    target: BatchStatus,
    actor: str | None = None,
) -> bool:
    """Move a batch to ``target``; return False if the transition is not allowed."""
    now = datetime.now(UTC)
    allowed_from = {
        BatchStatus.ACTIVE: [BatchStatus.GENERATED.value],
        BatchStatus.VOID: [BatchStatus.GENERATED.value, BatchStatus.ACTIVE.value],
    }[target]
    values: dict[str, object] = {"status": target.value}
    values["activated_at" if target is BatchStatus.ACTIVE else "voided_at"] = now
    event_type = (
        BatchEventType.ACTIVATED
        if target is BatchStatus.ACTIVE
        else BatchEventType.VOIDED
    )
    async with factory() as session, session.begin():
        result = await session.execute(
            update(CodeBatchModel)
            .where(
                CodeBatchModel.id == batch_id, CodeBatchModel.status.in_(allowed_from)
            )
            .values(**values)
            .returning(CodeBatchModel.id)
        )
        changed = result.scalar_one_or_none() is not None
        if changed:
            await session.execute(
                insert(CodeBatchEventModel).values(
                    batch_id=batch_id,
                    event_type=event_type.value,
                    actor=actor,
                    created_at=now,
                )
            )
    return changed


async def freeze_batch(
    factory: async_sessionmaker[AsyncSession],
    batch_id: UUID,
    *,
    export_sha256: str | None = None,
    actor: str | None = None,
) -> bool:
    """Freeze a batch's code format (and record its export, if any).

    A batch's format must not change once its codes have left the database
    as plaintext (the printer file). Returns False if the batch does not
    exist or is already frozen under a different fingerprint check -- a
    batch may be frozen only once; re-running the same export is a no-op.
    """
    now = datetime.now(UTC)
    async with factory() as session, session.begin():
        batch = await session.get(CodeBatchModel, batch_id)
        if batch is None:
            return False
        code_format = get_format(batch.format_id)
        fingerprint = code_format.fingerprint()
        if batch.frozen_at is not None:
            return batch.format_fingerprint == fingerprint
        batch.format_fingerprint = fingerprint
        batch.frozen_at = now
        detail = f"fingerprint={fingerprint[:16]}"
        if export_sha256 is not None:
            batch.exported_at = now
            batch.export_sha256 = export_sha256
            detail = f"{detail} sha256={export_sha256[:16]}"
            event_type = BatchEventType.EXPORTED
        else:
            event_type = BatchEventType.FROZEN
        await session.execute(
            insert(CodeBatchEventModel).values(
                batch_id=batch_id,
                event_type=event_type.value,
                actor=actor,
                detail=detail,
                created_at=now,
            )
        )
    return True


async def main_async(arguments: argparse.Namespace) -> int:
    database = PostgreSQLAdapter(get_settings())
    try:
        if arguments.command == "list":
            for line in await list_batches(database.session_factory):
                print(line)
            return 0
        if arguments.command == "formats":
            for line in list_formats():
                print(line)
            return 0
        if arguments.command == "history":
            lines = await batch_history(database.session_factory, arguments.batch_id)
            if not lines:
                print(f"no events for batch {arguments.batch_id}", file=sys.stderr)
                return 1
            for line in lines:
                print(line)
            return 0
        if arguments.command in {"export", "freeze"}:
            try:
                ok = await freeze_batch(
                    database.session_factory,
                    arguments.batch_id,
                    export_sha256=getattr(arguments, "csv_sha256", None),
                )
            except FormatRegistryError as error:
                print(f"refusing to freeze: {error}", file=sys.stderr)
                return 1
            if not ok:
                print(
                    f"batch {arguments.batch_id} not found, or already frozen "
                    "under a different format",
                    file=sys.stderr,
                )
                return 1
            print(f"batch {arguments.batch_id} is now frozen", file=sys.stderr)
            return 0
        target = (
            BatchStatus.ACTIVE if arguments.command == "activate" else BatchStatus.VOID
        )
        changed = await set_status(database.session_factory, arguments.batch_id, target)
    finally:
        await database.dispose()
    if not changed:
        print(
            f"batch {arguments.batch_id} not found or cannot become {target}",
            file=sys.stderr,
        )
        return 1
    print(f"batch {arguments.batch_id} is now {target}", file=sys.stderr)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    commands.add_parser("formats")
    for name in ("history", "activate", "void", "freeze"):
        command = commands.add_parser(name)
        command.add_argument("batch_id", type=UUID)
    export_command = commands.add_parser("export")
    export_command.add_argument("batch_id", type=UUID)
    export_command.add_argument(
        "--csv-sha256", required=True, help="checksum of the printer CSV"
    )
    raise SystemExit(asyncio.run(main_async(parser.parse_args())))


if __name__ == "__main__":
    main()
