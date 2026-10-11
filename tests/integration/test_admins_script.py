"""scripts.admins: the superuser bootstrap (promote/demote/list) against a
real database. The user must already exist; this script never creates one.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.domain.users import UserRole
from app.infrastructure.postgres.database import PostgreSQLAdapter
from app.infrastructure.postgres.repositories import PostgreSQLUserRepository
from scripts.admins import list_admins, set_role


@pytest.mark.asyncio
async def test_promote_then_demote_a_real_user(test_database_url: str) -> None:
    database = PostgreSQLAdapter(Settings(database_url=test_database_url))
    users = PostgreSQLUserRepository(database.session_factory)
    identifier = f"admin-{uuid4().hex}@example.com"
    try:
        created = await users.create(identifier, datetime.now(UTC))
        assert created.role is UserRole.PLAYER

        promoted = await set_role(database.session_factory, identifier, UserRole.ADMIN)
        assert promoted is True
        reloaded = await users.get_by_identifier(identifier)
        assert reloaded is not None
        assert reloaded.role is UserRole.ADMIN

        lines = await list_admins(database.session_factory)
        assert any(identifier in line for line in lines)

        demoted = await set_role(database.session_factory, identifier, UserRole.PLAYER)
        assert demoted is True
        reloaded = await users.get_by_identifier(identifier)
        assert reloaded is not None
        assert reloaded.role is UserRole.PLAYER
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_promoting_an_unknown_identifier_fails(test_database_url: str) -> None:
    database = PostgreSQLAdapter(Settings(database_url=test_database_url))
    try:
        changed = await set_role(
            database.session_factory,
            f"nobody-{uuid4().hex}@example.com",
            UserRole.ADMIN,
        )
    finally:
        await database.dispose()

    assert changed is False
