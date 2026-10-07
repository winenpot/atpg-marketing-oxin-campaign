"""The batch lifecycle CLI against real PostgreSQL: export, freeze, history."""

import hashlib
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, update

from app.core.config import Settings
from app.domain.code_batches import BatchEventType, BatchStatus
from app.domain.codes import V2_B10, CodeFormat, register_format, unregister_format
from app.domain.passports import CityCode
from app.infrastructure.postgres.database import PostgreSQLAdapter
from app.infrastructure.postgres.models import CodeBatchEventModel, CodeBatchModel
from scripts.code_batches import (
    batch_history,
    freeze_batch,
    list_batches,
    list_formats,
    set_status,
)
from scripts.generate_codes import generate_batch

PEPPER = "batch-lifecycle-test-pepper"


@pytest.fixture
async def database(test_database_url: str) -> AsyncIterator[PostgreSQLAdapter]:
    adapter = PostgreSQLAdapter(
        Settings(database_url=test_database_url, _env_file=None)
    )
    try:
        yield adapter
    finally:
        await adapter.dispose()


async def make_batch(database: PostgreSQLAdapter, tmp_path: Path, name: str) -> UUID:
    output = tmp_path / f"{name}.csv"
    return await generate_batch(
        database.session_factory,
        city=CityCode.PARIS,
        quantity=1,
        coins_per_code=0,
        label=name,
        base_url="https://play.example.ir",
        output=output,
        pepper=PEPPER,
    )


async def test_generating_a_batch_records_a_generated_event(
    database: PostgreSQLAdapter, tmp_path: Path
) -> None:
    batch_id = await make_batch(database, tmp_path, "gen")

    lines = await batch_history(database.session_factory, batch_id)

    assert len(lines) == 1
    assert "generated" in lines[0]


async def test_export_freezes_the_format_and_stores_the_checksum(
    database: PostgreSQLAdapter, tmp_path: Path
) -> None:
    batch_id = await make_batch(database, tmp_path, "export")
    checksum = hashlib.sha256(b"printer file").hexdigest()

    changed = await freeze_batch(
        database.session_factory, batch_id, export_sha256=checksum
    )

    assert changed is True
    async with database.session_factory() as session:
        batch = await session.get(CodeBatchModel, batch_id)
    assert batch is not None
    assert batch.frozen_at is not None
    assert batch.exported_at is not None
    assert batch.export_sha256 == checksum
    assert batch.format_fingerprint == V2_B10.fingerprint()

    lines = await batch_history(database.session_factory, batch_id)
    assert any("exported" in line for line in lines)


async def test_freezing_twice_is_a_no_op_and_stays_consistent(
    database: PostgreSQLAdapter, tmp_path: Path
) -> None:
    batch_id = await make_batch(database, tmp_path, "double-freeze")

    first = await freeze_batch(database.session_factory, batch_id)
    second = await freeze_batch(database.session_factory, batch_id)

    assert first is True
    assert second is True
    lines = await batch_history(database.session_factory, batch_id)
    assert sum(1 for line in lines if "frozen" in line) == 1


async def test_freezing_an_unknown_batch_returns_false(
    database: PostgreSQLAdapter,
) -> None:
    assert await freeze_batch(database.session_factory, uuid4()) is False


async def test_activate_and_void_record_events(
    database: PostgreSQLAdapter, tmp_path: Path
) -> None:
    batch_id = await make_batch(database, tmp_path, "lifecycle")

    assert await set_status(database.session_factory, batch_id, BatchStatus.ACTIVE)
    assert await set_status(database.session_factory, batch_id, BatchStatus.VOID)

    lines = await batch_history(database.session_factory, batch_id)
    kinds = [line.split()[1] for line in lines]
    assert kinds == [
        BatchEventType.GENERATED.value,
        BatchEventType.ACTIVATED.value,
        BatchEventType.VOIDED.value,
    ]


async def test_batch_events_table_is_append_only(
    database: PostgreSQLAdapter, tmp_path: Path
) -> None:
    batch_id = await make_batch(database, tmp_path, "append-only")
    async with database.session_factory() as session:
        event_id = await session.scalar(
            select(CodeBatchEventModel.id).where(
                CodeBatchEventModel.batch_id == batch_id
            )
        )
        with pytest.raises(Exception, match="append-only"):
            await session.execute(
                update(CodeBatchEventModel)
                .where(CodeBatchEventModel.id == event_id)
                .values(detail="tampered")
            )
            await session.commit()


async def test_list_batches_shows_format_and_frozen_state(
    database: PostgreSQLAdapter, tmp_path: Path
) -> None:
    batch_id = await make_batch(database, tmp_path, "listing")
    await freeze_batch(database.session_factory, batch_id)

    lines = await list_batches(database.session_factory)

    matching = [line for line in lines if str(batch_id) in line]
    assert len(matching) == 1
    assert "format=v2-b10" in matching[0]
    assert "frozen=yes" in matching[0]


async def test_list_formats_includes_every_registered_format() -> None:
    extra = CodeFormat(format_id="listing-test", body_length=3, grouping=(2, 2))
    register_format(extra)
    try:
        lines = list_formats()
        assert any(line.startswith("v2-b10") for line in lines)
        assert any(line.startswith("listing-test") for line in lines)
    finally:
        unregister_format("listing-test")
