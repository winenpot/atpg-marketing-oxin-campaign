"""Port for the per-account invalid-code attempt throttle.

The application layer records each CODE_INVALID outcome and checks the count
before a new attempt.  This keeps the throttle independent of the HTTP layer
and testable with a fake.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


class FailureThrottle(Protocol):
    """Append-only log of invalid-code attempts, queryable by window."""

    async def record(self, user_id: UUID, occurred_at: datetime) -> None:
        """Record one CODE_INVALID outcome for the given user."""
        ...

    async def count_in_window(self, user_id: UUID, window_start: datetime) -> int:
        """Return the number of failures recorded since ``window_start`` (inclusive)."""
        ...


class NullFailureThrottle:
    """No-op implementation: never throttles.  Use in development or unit tests
    that don't want to exercise throttle logic."""

    async def record(self, user_id: UUID, occurred_at: datetime) -> None:
        pass

    async def count_in_window(self, user_id: UUID, window_start: datetime) -> int:
        return 0


@dataclass(frozen=True, slots=True)
class ThrottleSettings:
    """How many invalid attempts before we block, and how wide the window is."""

    max_attempts: int = 10
    window_seconds: int = 3600
