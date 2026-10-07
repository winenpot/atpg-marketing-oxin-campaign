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

# One redeemed code is one lottery entry in that city's passport. A user's
# chance for a city's prize is proportional to their entries in that city.
ENTRIES_PER_CODE = 1


@dataclass(slots=True)
class PassportProgress:
    id: UUID
    user_id: UUID
    campaign: Campaign
    points: int
    created_at: datetime
    updated_at: datetime
