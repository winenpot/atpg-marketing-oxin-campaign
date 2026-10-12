from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.users import User


@dataclass(frozen=True, slots=True)
class UserCursor:
    """Position in the newest-first user list (keyset, stable under inserts)."""

    created_at: datetime
    id: UUID


@dataclass(frozen=True, slots=True)
class UserPage:
    items: list[User]
    next_cursor: UserCursor | None


class UserLister(Protocol):
    async def list_page(self, limit: int, after: UserCursor | None) -> list[User]:
        """Users ordered by (created_at, id) descending, strictly after ``after``."""
        ...


class AdminUserService:
    def __init__(self, users: UserLister) -> None:
        self._users = users

    async def list_users(self, limit: int, after: UserCursor | None) -> UserPage:
        rows = await self._users.list_page(limit + 1, after)
        items = rows[:limit]
        next_cursor = (
            UserCursor(created_at=items[-1].created_at, id=items[-1].id)
            if len(rows) > limit
            else None
        )
        return UserPage(items=items, next_cursor=next_cursor)
