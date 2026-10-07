from typing import Self

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.application.ports import ReadinessPort
from app.core.config import Settings
from app.infrastructure.postgres.models import CodeBatchModel


class PostgreSQLAdapter(ReadinessPort):
    def __init__(self, settings: Settings) -> None:
        self.engine: AsyncEngine = create_async_engine(
            settings.database_url,
            connect_args={
                "timeout": settings.db_connect_timeout_seconds,
                # A runaway query fails instead of holding a connection forever.
                "server_settings": {
                    "statement_timeout": str(settings.db_statement_timeout_ms),
                    "timezone": "UTC",
                },
            },
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def check_connection(self) -> None:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def frozen_batch_formats(self) -> list[tuple[str, str]]:
        """Every (format_id, format_fingerprint) pair of a frozen batch.

        Used at startup to catch a registered ``CodeFormat`` that has
        drifted from what a printed batch was frozen under (see
        ``app.domain.codes.verify_frozen_formats``).
        """
        statement = select(
            CodeBatchModel.format_id, CodeBatchModel.format_fingerprint
        ).where(CodeBatchModel.frozen_at.is_not(None))
        async with self.session_factory() as session:
            rows = (await session.execute(statement)).all()
        return [
            (format_id, fingerprint) for format_id, fingerprint in rows if fingerprint
        ]

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.dispose()
