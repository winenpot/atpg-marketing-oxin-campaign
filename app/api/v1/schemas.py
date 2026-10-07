from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.redemption_codes import RedemptionOutcome, RedemptionStatus
from app.application.wallets import WalletSummary
from app.domain.coins import CoinLedgerEntry
from app.domain.passports import CAMPAIGN_BY_CITY, PassportProgress
from app.domain.users import User


class AuthenticationRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)


class AuthenticationVerification(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class AuthenticationRequested(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: UUID
    identifier: str
    display_name: str | None
    account_status: str
    verification_status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            identifier=user.identifier,
            display_name=user.display_name,
            account_status=user.account_status.value,
            verification_status=user.verification_status.value,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)


class PassportProgressResponse(BaseModel):
    campaign: str
    points: int
    updated_at: datetime

    @classmethod
    def from_domain(cls, progress: PassportProgress) -> "PassportProgressResponse":
        return cls(
            campaign=progress.campaign.value,
            points=progress.points,
            updated_at=progress.updated_at,
        )


class RedeemCodeRequest(BaseModel):
    # Generous upper bound: people paste codes with spaces, dashes and
    # Persian digits. Real validation lives in app.domain.codes.parse_code.
    code: str = Field(min_length=1, max_length=64)


class RedeemResponse(BaseModel):
    city: str
    coins_awarded: int
    entries_in_city: int
    coin_balance: int
    replayed: bool

    @classmethod
    def from_outcome(cls, outcome: RedemptionOutcome) -> "RedeemResponse":
        if outcome.city is None:
            raise ValueError("a successful redemption always has a city")
        return cls(
            city=CAMPAIGN_BY_CITY[outcome.city].value,
            coins_awarded=outcome.coins_awarded,
            entries_in_city=outcome.entries_in_city,
            coin_balance=outcome.coin_balance,
            replayed=outcome.status is RedemptionStatus.REPLAYED,
        )


class CoinEntryResponse(BaseModel):
    amount: int
    reason: str
    balance_after: int
    created_at: datetime

    @classmethod
    def from_domain(cls, entry: CoinLedgerEntry) -> "CoinEntryResponse":
        return cls(
            amount=entry.amount,
            reason=entry.reason.value,
            balance_after=entry.balance_after,
            created_at=entry.created_at,
        )


class WalletResponse(BaseModel):
    balance: int
    entries: list[CoinEntryResponse]

    @classmethod
    def from_summary(cls, summary: WalletSummary) -> "WalletResponse":
        return cls(
            balance=summary.balance,
            entries=[CoinEntryResponse.from_domain(e) for e in summary.entries],
        )
