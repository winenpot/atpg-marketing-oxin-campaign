"""List, activate or void code batches (the redemption kill switch).

Usage::

    uv run python scripts/code_batches.py list
    uv run python scripts/code_batches.py activate <batch-id>
    uv run python scripts/code_batches.py void <batch-id>

``activate`` makes a ``generated`` batch redeemable. ``void`` stops every
unredeemed code of a batch immediately (leaked printer file, misprint);
codes already redeemed stay redeemed and keep their entries and coins.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.domain.code_batches import BatchStatus
from app.infrastructure.postgres.database import PostgreSQLAdapter
from app.infrastructure.postgres.models import CodeBatchModel, RedemptionCodeModel


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
        f"redeemed={row[5] or 0:<8} {row[6]}"
        for row in rows
    ]


async def set_status(
    factory: async_sessionmaker[AsyncSession], batch_id: UUID, target: BatchStatus
) -> bool:
    """Move a batch to ``target``; return False if the transition is not allowed."""
    now = datetime.now(UTC)
    allowed_from = {
        BatchStatus.ACTIVE: [BatchStatus.GENERATED.value],
        BatchStatus.VOID: [BatchStatus.GENERATED.value, BatchStatus.ACTIVE.value],
    }[target]
    values: dict[str, object] = {"status": target.value}
    values["activated_at" if target is BatchStatus.ACTIVE else "voided_at"] = now
    async with factory() as session, session.begin():
        result = await session.execute(
            update(CodeBatchModel)
            .where(
                CodeBatchModel.id == batch_id, CodeBatchModel.status.in_(allowed_from)
            )
            .values(**values)
            .returning(CodeBatchModel.id)
        )
        return result.scalar_one_or_none() is not None


async def main_async(arguments: argparse.Namespace) -> int:
    database = PostgreSQLAdapter(get_settings())
    try:
        if arguments.command == "list":
            for line in await list_batches(database.session_factory):
                print(line)
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
    for name in ("activate", "void"):
        command = commands.add_parser(name)
        command.add_argument("batch_id", type=UUID)
    raise SystemExit(asyncio.run(main_async(parser.parse_args())))


if __name__ == "__main__":
    main()
