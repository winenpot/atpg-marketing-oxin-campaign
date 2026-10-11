---
type: moc
---

# Lottery Passport — Project Vault

Backend-only brand-awareness gamification platform (FastAPI, hexagonal
architecture, async SQLAlchemy, Alembic, uv, Python 3.13+), built for an
FMCG company's drink-lottery campaign at gaming lounges.

## Navigation

- [[People]] — the team, who owns what, how to work with each person
- [[Decisions]] — running log of decisions made during implementation
- [[Findings]] — technical investigations and measurements (server benchmarks,
  load tests, API research, demo review); placeholders for pending work
- Architecture, security, operations docs stay in `../ARCHITECTURE.md`,
  `../SECURITY.md`, `../OPERATIONS.md` (repo root `docs/`), not duplicated here

## Why this vault exists

CLAUDE.md and ROADMAP.md are durable project docs (git-tracked, read by
every session). This vault holds things that don't fit a spec doc: who the
people are and how to deal with them, and a short-form decision trail with
dates and reasoning, kept close to the code per the project's own
`docs/vault/` convention (see the global vault's Memory Policy).

Team roles and the acceptance/scope docs are specified in
`../TEAM.md:1-31` (RACI table) and `../ROADMAP.md`. This vault does not
repeat that; it adds the interpersonal and decision-trail layer.
