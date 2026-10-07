from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class CoinReason(StrEnum):
    """Why a ledger entry exists. Extend as new ways to earn or spend appear."""

    CODE_REDEMPTION = "code_redemption"


@dataclass(frozen=True, slots=True)
class CoinLedgerEntry:
    """One immutable change to a user's coin balance."""

    id: UUID
    user_id: UUID
    amount: int
    reason: CoinReason
    balance_after: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Wallet:
    user_id: UUID
    balance: int
