from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.ledger import LedgerEntry, Wallet


class WalletReader(Protocol):
    async def get(self, user_id: UUID) -> Wallet | None: ...

    async def recent_entries(self, user_id: UUID, limit: int) -> list[LedgerEntry]: ...


@dataclass(frozen=True, slots=True)
class WalletView:
    balance: int
    lifetime_earned: int
    recent: list[LedgerEntry]


class WalletService:
    """Read side of coins. Writes only ever go through a unit of work."""

    def __init__(self, wallets: WalletReader, history_limit: int = 20) -> None:
        self._wallets = wallets
        self._history_limit = history_limit

    async def view(self, user_id: UUID) -> WalletView:
        wallet = await self._wallets.get(user_id)
        recent = await self._wallets.recent_entries(user_id, self._history_limit)
        if wallet is None:
            return WalletView(balance=0, lifetime_earned=0, recent=recent)
        return WalletView(
            balance=wallet.balance,
            lifetime_earned=wallet.lifetime_earned,
            recent=recent,
        )
