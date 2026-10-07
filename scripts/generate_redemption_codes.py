"""Generate one print run of product redemption codes.

Reads a per-city quantity plan, generates unique random v2 codes (see
``app/domain/codes.py``), stores only the keyed hash of each code in the
database, and writes the plaintext codes to a CSV for the manufacturer.

The CSV is the ONLY plaintext copy. Hand it to the printer, keep one
encrypted copy offline (printers lose files and disputes happen), and delete
every other copy. The application never reads plaintext codes again.

Order of operations is chosen so a failure can never leave codes in the
database that nobody holds the plaintext of:

1. generate every code in memory
2. write the CSV to a temporary file next to the output and fsync it
3. insert all hashes in ONE database transaction
4. rename the temporary file to its final name

Usage:
    uv run python scripts/generate_redemption_codes.py \\
        --counts counts.json \\
        --batch 2026-10-A \\
        --base-url https://play.example.com/r \\
        --output var/redemption-codes/2026-10-A.csv

counts.json shape: {"paris": 50000, "tokyo": 50000, ...}
(keys are CityCode names, case-insensitive)

The QR payload is ``<base-url>#<CODE>``. The code sits after ``#`` on purpose:
browsers never send the fragment to the server, so codes stay out of access
logs, proxies and Referer headers, and every QR points at the same cacheable
static page.
"""

import argparse
import asyncio
import csv
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.application.redemption_codes import hash_redemption_code
from app.core.config import get_settings
from app.domain.codes import format_printed, generate_code
from app.domain.passports import CityCode
from app.domain.redemption_codes import RedemptionCode
from app.infrastructure.postgres.database import PostgreSQLAdapter
from app.infrastructure.postgres.repositories import PostgreSQLRedemptionStore

MAX_CODES_PER_CITY = 1_000_000
CSV_HEADER = ["city", "code", "qr_url"]


def load_counts(path: Path) -> dict[CityCode, int]:
    raw = json.loads(path.read_text())
    counts: dict[CityCode, int] = {}
    for name, count in raw.items():
        city = CityCode[name.upper()]
        if not isinstance(count, int) or not 0 < count <= MAX_CODES_PER_CITY:
            raise ValueError(
                f"count for {name} must be an integer between 1 and "
                f"{MAX_CODES_PER_CITY}"
            )
        counts[city] = count
    return counts


def generate_codes_for_city(city: CityCode, count: int) -> list[str]:
    """Return ``count`` distinct canonical codes for ``city``."""
    codes: set[str] = set()
    while len(codes) < count:
        codes.add(generate_code(city))
    return sorted(codes)


def qr_url(base_url: str, canonical_code: str) -> str:
    return f"{base_url.rstrip('#')}#{canonical_code}"


def build_run(
    counts: dict[CityCode, int],
    pepper: str,
    batch: str,
    base_url: str,
    now: datetime,
) -> tuple[list[RedemptionCode], list[list[str]]]:
    records: list[RedemptionCode] = []
    rows: list[list[str]] = []
    seen: set[str] = set()
    for city, count in counts.items():
        for code in generate_codes_for_city(city, count):
            if code in seen:  # across cities the prefix differs; belt and braces
                raise RuntimeError("duplicate code generated")
            seen.add(code)
            records.append(
                RedemptionCode(
                    id=uuid4(),
                    city=city,
                    code_hash=hash_redemption_code(code, pepper),
                    created_at=now,
                    redeemed_at=None,
                    redeemed_by_user_id=None,
                    batch=batch,
                )
            )
            rows.append([city.name, format_printed(code), qr_url(base_url, code)])
    return records, rows


def write_csv_durably(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())


async def run(
    counts: dict[CityCode, int], batch: str, base_url: str, output_path: Path
) -> None:
    settings = get_settings()
    pepper = settings.redemption_code_pepper
    if pepper is None:
        raise SystemExit("REDEMPTION_CODE_PEPPER must be set to generate codes")
    if output_path.exists():
        raise SystemExit(f"refusing to overwrite existing file: {output_path}")

    records, rows = build_run(
        counts, pepper.get_secret_value(), batch, base_url, datetime.now(UTC)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = output_path.with_name(output_path.name + ".partial")
    write_csv_durably(partial_path, rows)

    database = PostgreSQLAdapter(settings)
    try:
        await PostgreSQLRedemptionStore(database.session_factory).bulk_insert(records)
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise
    finally:
        await database.dispose()

    partial_path.rename(output_path)
    for city, count in counts.items():
        print(f"{city.name}: {count} codes", file=sys.stderr)
    print(
        f"done: {len(records)} codes in batch {batch!r} written to {output_path}",
        file=sys.stderr,
    )
    print(
        "this file holds the only plaintext copy of these codes: send it to the "
        "manufacturer, keep one encrypted offline copy, delete the rest",
        file=sys.stderr,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", type=Path, required=True)
    parser.add_argument("--batch", required=True, help="print-run label, max 40 chars")
    parser.add_argument(
        "--base-url", required=True, help="QR landing page, e.g. https://play.x.ir/r"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.batch) > 40:
        raise SystemExit("--batch must be at most 40 characters")
    if not args.base_url.startswith("https://"):
        raise SystemExit("--base-url must start with https://")
    asyncio.run(run(load_counts(args.counts), args.batch, args.base_url, args.output))


if __name__ == "__main__":
    main()
