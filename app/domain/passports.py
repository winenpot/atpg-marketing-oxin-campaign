from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Campaign(StrEnum):
    PARIS = "paris"
    BERLIN = "berlin"
    PATTAYA = "pattaya"
    MEXICO = "mexico"
    MADRID = "madrid"
    TOKYO = "tokyo"
    MOSCOW = "moscow"


class CityCode(StrEnum):
    PARIS = "PR"
    BERLIN = "BE"
    PATTAYA = "PA"
    MEXICO = "ME"
    MADRID = "MA"
    TOKYO = "TO"
    MOSCOW = "MO"


CAMPAIGN_BY_CITY: dict[CityCode, Campaign] = {
    CityCode.PARIS: Campaign.PARIS,
    CityCode.BERLIN: Campaign.BERLIN,
    CityCode.PATTAYA: Campaign.PATTAYA,
    CityCode.MEXICO: Campaign.MEXICO,
    CityCode.MADRID: Campaign.MADRID,
    CityCode.TOKYO: Campaign.TOKYO,
    CityCode.MOSCOW: Campaign.MOSCOW,
}

# One redeemed code is one entry in that city's draw. If marketing ever wants
# bonus entries, record them as their own rows rather than changing this.
ENTRIES_PER_CODE = 1


@dataclass(slots=True)
class PassportProgress:
    """Entries a user holds in one city's draw (``points`` == entries)."""

    id: UUID
    user_id: UUID
    campaign: Campaign
    points: int
    created_at: datetime
    updated_at: datetime
