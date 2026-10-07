from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.passports import CityCode


@dataclass(slots=True)
class RedemptionCode:
    """One printed code. Only its keyed hash is stored, never the plaintext."""

    id: UUID
    city: CityCode
    code_hash: str
    created_at: datetime
    redeemed_at: datetime | None
    redeemed_by_user_id: UUID | None
    batch_id: UUID | None = None
