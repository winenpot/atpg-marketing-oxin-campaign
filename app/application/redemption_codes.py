import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.application.authentication import Clock
from app.domain.codes import CodeFormatError, CodeProblem, parse_code
from app.domain.passports import CityCode
from app.domain.redemption_codes import RedemptionCode


class RedemptionFailure(StrEnum):
    """Stable, client-visible reasons a redemption did not happen."""

    INVALID = "code_invalid"
    MISTYPED = "code_mistyped"
    ALREADY_REDEEMED = "code_already_redeemed"
    UNAVAILABLE = "redemption_unavailable"


class RedemptionError(Exception):
    def __init__(self, failure: RedemptionFailure) -> None:
        super().__init__(failure.value)
        self.failure = failure


class RedemptionStatus(StrEnum):
    CREDITED = "credited"
    REPLAYED = "replayed"
    NOT_FOUND = "not_found"
    ALREADY_REDEEMED = "already_redeemed"


@dataclass(frozen=True, slots=True)
class RedemptionOutcome:
    """What the store did with one redemption attempt.

    ``REPLAYED`` means this same user had already redeemed this code (for
    example a client retry after a network timeout): nothing new was credited
    and the original award is reported again.
    """

    status: RedemptionStatus
    city: CityCode | None = None
    coins_awarded: int = 0
    entries_in_city: int = 0
    coin_balance: int = 0


class RedemptionStore(Protocol):
    async def bulk_insert(self, codes: list[RedemptionCode]) -> None:
        """Insert all codes in one transaction or none of them."""

    async def void_batch(self, batch: str, now: datetime) -> int:
        """Void unredeemed codes of a print run; return how many were voided."""

    async def redeem(
        self, code_hash: str, user_id: UUID, coins: int, now: datetime
    ) -> RedemptionOutcome:
        """Atomically claim the code, record the redemption and credit coins.

        Either every effect (code claimed, redemption row, per-city entry,
        coin ledger entry, wallet balance) is committed together or none is.
        Two concurrent calls for the same code can never both be credited.
        """


def hash_redemption_code(code: str, pepper: str) -> str:
    return hmac.new(
        pepper.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
    ).hexdigest()


class RedemptionService:
    def __init__(
        self,
        store: RedemptionStore,
        clock: Clock,
        pepper: str | None,
        coins_per_redemption: int,
    ) -> None:
        self._store = store
        self._clock = clock
        self._pepper = pepper
        self._coins = coins_per_redemption

    async def redeem(self, user_id: UUID, raw_code: str) -> RedemptionOutcome:
        if self._pepper is None:
            raise RedemptionError(RedemptionFailure.UNAVAILABLE)

        try:
            parsed = parse_code(raw_code)
        except CodeFormatError as error:
            failure = (
                RedemptionFailure.MISTYPED
                if error.problem is CodeProblem.MISTYPED
                else RedemptionFailure.INVALID
            )
            raise RedemptionError(failure) from error

        outcome = await self._store.redeem(
            hash_redemption_code(parsed.canonical, self._pepper),
            user_id,
            self._coins,
            self._clock.now(),
        )
        if outcome.status is RedemptionStatus.NOT_FOUND:
            raise RedemptionError(RedemptionFailure.INVALID)
        if outcome.status is RedemptionStatus.ALREADY_REDEEMED:
            raise RedemptionError(RedemptionFailure.ALREADY_REDEEMED)
        return outcome
