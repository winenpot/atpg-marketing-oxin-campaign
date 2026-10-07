from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.coins import CoinLedgerEntry


class WalletRepository(Protocol):
    async def get_balance(self, user_id: UUID) -> int: ...

    async def list_entries(self, user_id: UUID, limit: int) -> list[CoinLedgerEntry]:
        """Newest first."""


@dataclass(frozen=True, slots=True)
class WalletSummary:
    balance: int
    entries: list[CoinLedgerEntry]


class WalletService:
    HISTORY_LIMIT = 50

    def __init__(self, wallets: WalletRepository) -> None:
        self._wallets = wallets

    async def summary(self, user_id: UUID) -> WalletSummary:
        return WalletSummary(
            balance=await self._wallets.get_balance(user_id),
            entries=await self._wallets.list_entries(user_id, self.HISTORY_LIMIT),
        )
