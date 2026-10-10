"""PostgreSQL adapter for the per-account invalid-code attempt throttle."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.postgres.models import RedemptionFailureModel


class PostgreSQLFailureThrottle:
    def __init__(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = factory

    async def record(self, user_id: UUID, occurred_at: datetime) -> None:
        async with self._factory() as session:
            session.add(
                RedemptionFailureModel(user_id=user_id, occurred_at=occurred_at)
            )
            await session.commit()

    async def count_in_window(self, user_id: UUID, window_start: datetime) -> int:
        async with self._factory() as session:
            result = await session.execute(
                select(func.count()).where(
                    RedemptionFailureModel.user_id == user_id,
                    RedemptionFailureModel.occurred_at >= window_start,
                )
            )
            return result.scalar_one()
