from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.redemption_codes import RedemptionResult
from app.application.wallets import WalletView
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
    """Raw user input or the code from the QR URL; the server normalizes it."""

    code: str = Field(min_length=1, max_length=64, examples=["TO-7KQ2-M9XH-4R6"])


class RedemptionResponse(BaseModel):
    city: str
    entries_added: int
    city_entries: int
    coins_awarded: int
    coin_balance: int
    replayed: bool

    @classmethod
    def from_result(cls, result: RedemptionResult) -> "RedemptionResponse":
        return cls(
            city=CAMPAIGN_BY_CITY[result.city].value,
            entries_added=result.entries_added,
            city_entries=result.city_entries,
            coins_awarded=result.coins_awarded,
            coin_balance=result.coin_balance,
            replayed=result.replayed,
        )


class LedgerEntryResponse(BaseModel):
    id: int
    amount: int
    reason: str
    created_at: datetime


class WalletResponse(BaseModel):
    balance: int
    lifetime_earned: int
    recent: list[LedgerEntryResponse]

    @classmethod
    def from_view(cls, view: WalletView) -> "WalletResponse":
        return cls(
            balance=view.balance,
            lifetime_earned=view.lifetime_earned,
            recent=[
                LedgerEntryResponse(
                    id=entry.id,
                    amount=entry.amount,
                    reason=entry.reason.value,
                    created_at=entry.created_at,
                )
                for entry in view.recent
            ],
        )
