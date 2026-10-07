# ADR-0001: Keep the FastAPI modular monolith

**Status:** Accepted
**Date:** 2026-10-07
**Deciders:** Backend developer; CEO informed

## Context

The repository already contains a working FastAPI backend: typed settings, async SQLAlchemy,
Alembic migrations, CI, server-side sessions, hashed codes, and a hexagonal layout. The scope
grew from "redeem printed codes" to a gamified platform (coins, challenges, tournaments,
leaderboards, admin). There are 15 days and one backend developer, who knows both Django and
FastAPI. The question was whether to restart in Django for its admin and ORM batteries.

## Decision

Keep FastAPI and the modular monolith. Add SQLAdmin for the back office
([ADR-0008](0008-sqladmin-back-office.md)). Keep hexagonal boundaries for multi-table writes
(unit of work) and relax them for simple reads and CRUD.

## Options considered

### Option A: keep FastAPI (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Low: code, migrations, CI already exist |
| Cost | Zero rewrite time |
| Scalability | Async I/O; far beyond the expected load on one VM |
| Team familiarity | High |

**Pros:** no rewrite; async fits slow external calls; existing tests and CI.
**Cons:** no built-in admin; more wiring by hand than Django.

### Option B: rewrite in Django + DRF

| Dimension | Assessment |
|---|---|
| Complexity | Medium: rewrite auth, models, migrations, tests |
| Cost | 2–4 of the 11 working days |
| Scalability | Adequate |
| Team familiarity | High |

**Pros:** Django admin, mature ecosystem.
**Cons:** burns a quarter of the schedule re-creating what exists.

## Trade-off analysis

Django's admin is the only real advantage, and SQLAdmin closes most of that gap in a day.
A rewrite would spend the schedule's only buffer before any new feature exists.

## Consequences

- Easier: building on tested code from day 1; async SMS and HTTP calls.
- Harder: admin features beyond CRUD (custom actions, approvals) need some code in SQLAdmin.
- Revisit: never for this campaign; reconsider only for a new product.

## Action items

1. [x] Merge `feature/mvp-foundation` (codes v2, unit of work, ledger).
2. [ ] Add SQLAdmin with admin auth and audit (B20).
