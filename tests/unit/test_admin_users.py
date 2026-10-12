"""Admin user list: keyset paging, cursor handling and the admin gate."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_admin_user_service, get_current_user
from app.api.errors import ApiError
from app.api.v1.admin import decode_cursor, encode_cursor
from app.app import create_app
from app.application.admin_users import AdminUserService, UserCursor
from app.core.config import Settings
from app.domain.users import AccountStatus, User, UserRole, VerificationStatus

BASE = datetime(2026, 10, 1, tzinfo=UTC)


def make_user(index: int, role: UserRole = UserRole.PLAYER) -> User:
    created = BASE + timedelta(minutes=index)
    return User(
        id=UUID(int=index),
        identifier=f"user-{index}",
        display_name=None,
        account_status=AccountStatus.ACTIVE,
        verification_status=VerificationStatus.VERIFIED,
        role=role,
        created_at=created,
        updated_at=created,
    )


class FakeLister:
    def __init__(self, users: list[User]) -> None:
        self.users = users

    async def list_page(self, limit: int, after: UserCursor | None) -> list[User]:
        ordered = sorted(self.users, key=lambda u: (u.created_at, u.id), reverse=True)
        if after is not None:
            key = (after.created_at, after.id)
            ordered = [u for u in ordered if (u.created_at, u.id) < key]
        return ordered[:limit]


async def test_pages_newest_first_without_gaps_or_repeats() -> None:
    service = AdminUserService(FakeLister([make_user(i) for i in range(5)]))

    first = await service.list_users(2, None)
    assert [u.identifier for u in first.items] == ["user-4", "user-3"]
    assert first.next_cursor is not None
    second = await service.list_users(2, first.next_cursor)
    assert [u.identifier for u in second.items] == ["user-2", "user-1"]
    assert second.next_cursor is not None
    last = await service.list_users(2, second.next_cursor)
    assert [u.identifier for u in last.items] == ["user-0"]
    assert last.next_cursor is None


async def test_an_exact_fit_has_no_next_cursor() -> None:
    service = AdminUserService(FakeLister([make_user(i) for i in range(2)]))

    page = await service.list_users(2, None)

    assert len(page.items) == 2
    assert page.next_cursor is None


def test_cursor_round_trips_and_rejects_garbage() -> None:
    cursor = UserCursor(BASE, uuid4())

    assert decode_cursor(encode_cursor(cursor)) == cursor
    for bad in ("not-a-cursor", "", "!!!!"):
        with pytest.raises(ApiError) as excinfo:
            decode_cursor(bad)
        assert excinfo.value.code == "CURSOR_INVALID"


def _client(role: UserRole | None, users: list[User]) -> TestClient:
    app = create_app(
        Settings(
            database_url="postgresql+asyncpg://postgres:postgres@localhost:5432/x",
        )
    )
    app.dependency_overrides[get_admin_user_service] = lambda: AdminUserService(
        FakeLister(users)
    )
    if role is not None:
        app.dependency_overrides[get_current_user] = lambda: make_user(99, role)
    return TestClient(app)


def test_the_route_pages_for_an_admin() -> None:
    client = _client(UserRole.ADMIN, [make_user(i) for i in range(3)])

    first = client.get("/api/v1/admin/users", params={"limit": 2})
    assert first.status_code == 200
    body = first.json()
    assert [u["identifier"] for u in body["items"]] == ["user-2", "user-1"]
    second = client.get(
        "/api/v1/admin/users", params={"limit": 2, "cursor": body["next_cursor"]}
    ).json()
    assert [u["identifier"] for u in second["items"]] == ["user-0"]
    assert second["next_cursor"] is None


def test_the_route_rejects_a_player_and_an_anonymous_caller() -> None:
    assert _client(UserRole.PLAYER, []).get("/api/v1/admin/users").status_code == 403
    assert _client(None, []).get("/api/v1/admin/users").status_code == 401


def test_the_route_validates_limit_and_cursor() -> None:
    client = _client(UserRole.ADMIN, [])

    assert client.get("/api/v1/admin/users", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/admin/users", params={"limit": 101}).status_code == 422
    bad = client.get("/api/v1/admin/users", params={"cursor": "garbage"})
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "CURSOR_INVALID"
