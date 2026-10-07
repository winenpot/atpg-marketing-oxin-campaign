from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.domain.passports import CityCode


class BatchStatus(StrEnum):
    """Lifecycle of one print run of codes.

    ``generated``: codes exist in the database and in the printer file, but
    cannot be redeemed yet. Activate the batch when the product is on shelves.
    ``active``: codes can be redeemed.
    ``void``: kill switch for a leaked or misprinted batch; unredeemed codes
    stop working immediately, already-redeemed ones stay redeemed.
    """

    GENERATED = "generated"
    ACTIVE = "active"
    VOID = "void"


@dataclass(slots=True)
class CodeBatch:
    id: UUID
    city: CityCode
    label: str
    quantity: int
    coins_per_code: int
    status: BatchStatus
    created_at: datetime
    activated_at: datetime | None
    voided_at: datetime | None
