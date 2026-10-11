# Parked: city passport

Status: **parked** on 2026-10-10 (ADR 0009). Not in the MVP. Expected to return soon,
so nothing below has been deleted from the code.

## What it was

Seven city drinks (Paris, Berlin, Pattaya, Mexico, Madrid, Tokyo, Moscow). Each redeemed
code added one entry to that city's trip draw and showed a stamp in the player's
passport. Tables: `passport_progress` (user, campaign, points). Code: `app/domain/passports.py`,
`app/application/passports.py`, `GET /api/v1/me/passports`.

## State while parked

- The backend keeps writing `passport_progress` on every redemption (same transaction as
  the coin ledger). Data keeps accumulating, so turning the feature back on loses nothing.
- `GET /api/v1/me/passports` stays live but is **not** part of the player contract
  (`docs/API_CONTRACT.md`). The frontend must not depend on it.
- `GET /api/v1/config` does not publish `cities` during the MVP.
- Codes keep their campaign/city prefix inside the code format, so batches printed now are
  passport-compatible later.

## Contract to restore when un-parking

```http
GET /api/v1/me/passports
200 [{"campaign": "tokyo", "points": 3, "updated_at": "2026-10-10T08:30:00Z"}]
```

Only cities with at least one entry appear; render all cities from `/config.cities`
(`[{"campaign": "tokyo", "prefix": "TO"}]`, in passport order) and fill in the ones present.
The redemption response gains back `city`, `entries_added`, `city_entries`.

## Before un-parking

1. Legal opinion on city trip draws (ROADMAP CP5).
2. A passport screen in the frontend (the 2026-10-10 demo has none).
3. Decide how city entries relate to the weekly PS5 tickets (separate draws, or not).
4. Re-add the passport rows to ROADMAP "Must" and to API_CONTRACT.md.
