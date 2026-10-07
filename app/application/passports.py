from typing import Protocol
from uuid import UUID

from app.domain.passports import PassportProgress


class PassportRepository(Protocol):
    """Read side of passports. Entries are only added inside a unit of work."""

    async def list_for_user(self, user_id: UUID) -> list[PassportProgress]: ...


class PassportService:
    def __init__(self, passports: PassportRepository) -> None:
        self._passports = passports

    async def list_for_user(self, user_id: UUID) -> list[PassportProgress]:
        return await self._passports.list_for_user(user_id)
