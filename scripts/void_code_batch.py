"""Void every not-yet-redeemed code in a print run (leak / misprint response).

Redemptions that already happened are kept: they are legitimate history.
Voided codes behave exactly like unknown codes ("code_invalid").

Usage:
    uv run python scripts/void_code_batch.py --batch 2026-10-A
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime

from app.core.config import get_settings
from app.infrastructure.postgres.database import PostgreSQLAdapter
from app.infrastructure.postgres.repositories import PostgreSQLRedemptionStore


async def run(batch: str) -> None:
    database = PostgreSQLAdapter(get_settings())
    try:
        store = PostgreSQLRedemptionStore(database.session_factory)
        voided = await store.void_batch(batch, datetime.now(UTC))
    finally:
        await database.dispose()
    print(f"voided {voided} unredeemed codes in batch {batch!r}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.batch))


if __name__ == "__main__":
    main()
