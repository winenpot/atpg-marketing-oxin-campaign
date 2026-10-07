---
type: adr
---

# Decisions — implementation-session log

Short-form, dated. Formal ADRs for architecture-level choices live in
`../adr/`; this is the lighter day-to-day decision trail for things ADRs
don't cover (process, scope, open questions resolved in chat).

## 2026-10-07 — code length left open; built a pluggable format instead

Neither 10 (repo default, `../../app/domain/codes.py` pre-change) nor 8
(the user's earlier preference per HANDOFF.md) was agreed by the team.
Decision: build a `CodeFormat` registry (any alphabet/length/grouping) with
export, freeze and event tracking, so the actual length can be decided
later without another migration. See `../../app/domain/codes.py` and
`../../alembic/versions/0006_batch_format_tracking.py`.

## 2026-10-07 — QR link stays path form (`/r/CODE`)

Chosen because it is the more common pattern and the repo docs
(`../../docs/CODES.md:29`) and Arman's planned route (`../../docs/TODO.md:88`)
already assume it. The handoff's alternative (fragment form, `/r#CODE`, to
keep codes out of server logs) was not picked. Mitigation: redact `/r/*`
paths from nginx access logs as part of the security pass (B25).

## 2026-10-07 — Postgres-only stays, behind a port

ADR 0004 (`../adr/0004-postgres-only-no-redis-for-mvp.md`) is accepted as
written. The user wants the ability to turn on Redis later without a
rewrite if the SMS/job queue proves too slow or a second API server
appears, so the job queue will sit behind an application port
(`QUEUE_BACKEND=postgres|redis` switch), Postgres-backed implementation
shipping first.

## 2026-10-07 — phone + SMS OTP only, no email sign-in

Confirms ADR 0005. Email auth path in the current code is to be removed
when B10 (phone OTP) is implemented.

## 2026-10-07 — commit hooks and HANDOFF.md

`core.hooksPath` set to `.githooks` (committed, enforces gitmoji +
conventional-commit subjects). `HANDOFF.md` (written by a prior session,
superseded by this vault + the plan file) is gitignored and will be
deleted once this vault is confirmed to carry everything load-bearing from it.
