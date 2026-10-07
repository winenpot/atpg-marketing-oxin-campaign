"""Redeeming a printed code: one lottery entry for its city plus coins.

The whole use case runs in one database transaction (see
``app.application.unit_of_work``):

1. lock the user's wallet row (serializes this user's redemptions)
2. claim the code with a conditional UPDATE (serializes rival users)
3. enforce the per-user daily cap, counted in the campaign time zone
4. add the city entry, record the coin award, update the balance
5. commit

Re-submitting a code you already redeemed returns the original result with
``replayed=True`` instead of an error, so clients can retry after a timeout
without double-crediting (the ledger's unique idempotency key guarantees it
even if this code had a bug).
"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, time
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo

from app.application.authentication import Clock
from app.application.unit_of_work import ClaimedCode, UnitOfWork, UnitOfWorkFactory
from app.domain.codes import CodeFormatError, CodeProblem, parse_code
from app.domain.ledger import LedgerReason, NewLedgerEntry
from app.domain.passports import CAMPAIGN_BY_CITY, ENTRIES_PER_CODE, CityCode


class RedemptionErrorCode(StrEnum):
    """Stable error codes the frontend maps to user-facing copy."""

    NOT_CONFIGURED = "REDEMPTION_NOT_CONFIGURED"
    MALFORMED = "CODE_MALFORMED"
    MISTYPED = "CODE_MISTYPED"
    INVALID = "CODE_INVALID"
    ALREADY_REDEEMED = "CODE_ALREADY_REDEEMED"
    DAILY_LIMIT = "REDEMPTION_DAILY_LIMIT"


class RedemptionError(Exception):
    def __init__(self, code: RedemptionErrorCode) -> None:
        super().__init__(code.value)
        self.code = code


@dataclass(frozen=True, slots=True)
class RedemptionResult:
    city: CityCode
    entries_added: int
    city_entries: int
    coins_awarded: int
    coin_balance: int
    replayed: bool


def hash_redemption_code(code: str, pepper: str) -> str:
    """Keyed hash of a canonical code; the pepper never lives in the database.

    A plain SHA-256 would let anyone holding a database dump enumerate the
    whole code space offline. With HMAC they also need the pepper.
    """
    return hmac.new(
        pepper.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def redemption_idempotency_key(code_id: UUID) -> str:
    return f"{LedgerReason.CODE_REDEMPTION.value}:{code_id}"


def start_of_local_day(moment: datetime, zone: ZoneInfo) -> datetime:
    """UTC-aware instant of the most recent local midnight in ``zone``."""
    local = moment.astimezone(zone)
    return datetime.combine(local.date(), time.min, tzinfo=zone)


class RedemptionService:
    def __init__(
        self,
        unit_of_work: UnitOfWorkFactory,
        clock: Clock,
        pepper: str | None,
        daily_limit: int,
        campaign_zone: ZoneInfo,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._pepper = pepper
        self._daily_limit = daily_limit
        self._campaign_zone = campaign_zone

    async def redeem(self, user_id: UUID, raw_code: str) -> RedemptionResult:
        if self._pepper is None:
            raise RedemptionError(RedemptionErrorCode.NOT_CONFIGURED)
        try:
            parsed = parse_code(raw_code)
        except CodeFormatError as error:
            code = (
                RedemptionErrorCode.MISTYPED
                if error.problem is CodeProblem.MISTYPED
                else RedemptionErrorCode.MALFORMED
            )
            raise RedemptionError(code) from error

        code_hash = hash_redemption_code(parsed.canonical, self._pepper)
        now = self._clock.now()
        async with self._unit_of_work() as uow:
            balance = await uow.ledger.lock_wallet(user_id, now)
            claimed = await uow.codes.claim(code_hash, user_id, now)
            if claimed is None:
                return await self._resolve_unclaimed(uow, code_hash, user_id, balance)
            result = await self._apply_claim(uow, claimed, user_id, balance, now)
            await uow.commit()
            return result

    async def _apply_claim(
        self,
        uow: UnitOfWork,
        claimed: ClaimedCode,
        user_id: UUID,
        balance: int,
        now: datetime,
    ) -> RedemptionResult:
        since = start_of_local_day(now, self._campaign_zone)
        if await uow.codes.count_redeemed_since(user_id, since) > self._daily_limit:
            # Raising before commit rolls the claim back: the code stays usable.
            raise RedemptionError(RedemptionErrorCode.DAILY_LIMIT)

        progress = await uow.passports.add_entries(
            user_id, CAMPAIGN_BY_CITY[claimed.city], ENTRIES_PER_CODE, now
        )
        if claimed.coins_per_code > 0:
            balance = await uow.ledger.record(
                NewLedgerEntry(
                    user_id=user_id,
                    amount=claimed.coins_per_code,
                    reason=LedgerReason.CODE_REDEMPTION,
                    idempotency_key=redemption_idempotency_key(claimed.code_id),
                    created_at=now,
                    source_id=str(claimed.code_id),
                )
            )
        return RedemptionResult(
            city=claimed.city,
            entries_added=ENTRIES_PER_CODE,
            city_entries=progress.points,
            coins_awarded=claimed.coins_per_code,
            coin_balance=balance,
            replayed=False,
        )

    async def _resolve_unclaimed(
        self, uow: UnitOfWork, code_hash: str, user_id: UUID, balance: int
    ) -> RedemptionResult:
        found = await uow.codes.lookup(code_hash)
        if found is None or found.redeemed_by_user_id is None:
            # Unknown code, or a code whose batch is not active (not yet
            # released, or voided). Deliberately indistinguishable.
            raise RedemptionError(RedemptionErrorCode.INVALID)
        if found.redeemed_by_user_id != user_id:
            raise RedemptionError(RedemptionErrorCode.ALREADY_REDEEMED)

        progress = await uow.passports.get(user_id, CAMPAIGN_BY_CITY[found.city])
        coins = await uow.ledger.amount_for_key(
            redemption_idempotency_key(found.code_id)
        )
        return RedemptionResult(
            city=found.city,
            entries_added=ENTRIES_PER_CODE,
            city_entries=progress.points if progress else 0,
            coins_awarded=coins or 0,
            coin_balance=balance,
            replayed=True,
        )
