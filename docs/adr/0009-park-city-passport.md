# ADR 0009: Park the city passport for the MVP

Date: 2026-10-10. Status: accepted.

## Context

The frontend demo (TorshX × Oxin, 2026-10-10) is built around scanning, mini-games,
streaks, a daily wheel, a reward shop and a weekly PS5 ticket draw. It has no city
passport screen. The passport also depends on a legal opinion for city trip draws (CP5).

## Decision

The city passport is out of the MVP player contract. The backend keeps recording
`passport_progress` on redemption, so the data exists if the feature returns. Details and
the restore checklist: [docs/parked/CITY_PASSPORT.md](../parked/CITY_PASSPORT.md).

## Consequences

- `/me/passports` and `config.cities` leave the player contract; the endpoint stays live.
- The redemption response no longer promises city fields.
- Printed code formats keep their city prefix, so nothing printed now blocks a return.
