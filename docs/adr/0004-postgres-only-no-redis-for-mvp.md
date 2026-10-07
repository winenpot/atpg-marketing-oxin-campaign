# ADR-0004: PostgreSQL only for the MVP (jobs table, no Redis, no Celery)

**Status:** Accepted
**Date:** 2026-10-07
**Deciders:** Backend developer

## Context

The MVP needs background work (SMS sending is slow and unreliable), rate limiting, and some
caching. The usual answers are Redis plus Celery or arq. The team is one backend developer
who prefers the simplest thing that works, on one VM, and the expected load is modest
([ARCHITECTURE.md](../ARCHITECTURE.md#capacity-estimate)).

## Decision

- Background work uses a `jobs` table in PostgreSQL, claimed with `FOR UPDATE SKIP LOCKED` by one worker process. Enqueueing can happen in the same transaction as the business write.
- Per-IP rate limits live in nginx (`limit_req`), which is shared by all API workers. Per-account limits (OTP cooldown, redemption failures, daily caps) are enforced in PostgreSQL inside the relevant transaction.
- Caches are in-process with short TTLs, and never for correctness-critical data.
- The existing in-process rate-limit middleware stays only as a high backstop.

## Options considered

### Option A: PostgreSQL only (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Low: no new service to deploy, back up, monitor or secure |
| Cost | ~100 lines for the jobs loop |
| Scalability | Database queues are fine to thousands of jobs per second; we need a few per second |
| Team familiarity | High |

### Option B: Redis + arq (or Celery)

| Dimension | Assessment |
|---|---|
| Complexity | Medium: another container, persistence settings, monitoring |
| Cost | Setup and failure modes to learn under deadline |
| Scalability | Higher than needed |
| Team familiarity | Medium |

**Cons that matter here:** jobs and data cannot commit atomically (dual write); one more thing that can be down at 2 a.m.

## Trade-off analysis

The jobs table gives transactional enqueue and one backup for everything. Its operational
cost is table churn: delete finished jobs promptly and keep autovacuum aggressive on that table.

## Consequences

- Easier: one datastore to run, back up and reason about.
- Harder: if a second API server is added, IP rate limits must move to a shared store (Redis) or a load balancer.
- Revisit when: a second API VM appears, leaderboard reads need a shared cache, or job volume exceeds hundreds per second.

## Action items

1. [ ] `jobs` table, worker loop, reaper, deletion of finished jobs (B11).
2. [ ] nginx `limit_req` zones with lounge IP allow-list (B25).
