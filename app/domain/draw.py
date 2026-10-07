"""Reproducible weighted draw (procedure in docs/DRAW.md).

Anyone holding the published entry snapshot and the published seed can rerun
this and get the same winners, which is the point: nobody has to trust us.

* Each participant's chance is proportional to their entries in that city.
* Winners are drawn without replacement (one prize per person per draw);
  the first ``count`` are winners, any further ones are the reserve list.
* Randomness comes only from ``HMAC-SHA256(seed, label:round:counter)``;
  rejection sampling removes modulo bias.
"""

import hashlib
import hmac
from collections.abc import Sequence

Entry = tuple[str, int]  # (participant id as published, number of entries)


def snapshot_digest(entries: Sequence[Entry]) -> str:
    """SHA-256 of the canonical snapshot, published BEFORE the seed is known."""
    canonical = "".join(f"{pid},{weight}\n" for pid, weight in sorted(entries))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def uniform_below(bound: int, seed: bytes, label: str) -> int:
    """Unbiased integer in ``[0, bound)`` derived from the seed and a label."""
    if bound <= 0:
        raise ValueError("bound must be positive")
    space = 1 << 256
    limit = space - space % bound  # values >= limit would bias the result
    counter = 0
    while True:
        digest = hmac.new(seed, f"{label}:{counter}".encode(), hashlib.sha256).digest()
        value = int.from_bytes(digest, "big")
        if value < limit:
            return value % bound
        counter += 1


def draw_winners(
    entries: Sequence[Entry], seed: bytes, label: str, count: int
) -> list[str]:
    """Draw up to ``count`` distinct participants, weighted by entries.

    ``label`` names the draw (for example ``"tokyo-1405-aban"``) so one seed can
    serve several draws without correlating them. Duplicate participant IDs
    are rejected because they would make the snapshot ambiguous.
    """
    ids = [pid for pid, _ in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("participant ids must be unique")
    if any(weight < 0 for _, weight in entries):
        raise ValueError("weights must not be negative")

    pool = [(pid, weight) for pid, weight in sorted(entries) if weight > 0]
    winners: list[str] = []
    for round_number in range(min(count, len(pool))):
        total = sum(weight for _, weight in pool)
        ticket = uniform_below(total, seed, f"{label}:{round_number}")
        cumulative = 0
        for index, (pid, weight) in enumerate(pool):
            cumulative += weight
            if ticket < cumulative:
                winners.append(pid)
                pool.pop(index)
                break
    return winners
