# ADR-0003: Unit of work and an append-only coin ledger

**Status:** Accepted
**Date:** 2026-10-07
**Deciders:** Backend developer

## Context

Each repository in the first version opened its own database session. Redemption therefore
committed the code claim and the passport credit in **two separate transactions**: a crash
or timeout between them burned the code without crediting the user, and there was no record
of why a total had its value. Coins add more writers (challenges, tournaments, approvals,
adjustments, later the prize store), and real prizes mean disputes will happen.

## Decision

- Any use case that writes more than one table runs inside one **unit of work** (one session, one transaction, explicit `commit()`, rollback otherwise).
- Coins live in an **append-only ledger** (`coin_ledger_entries`) with a unique `idempotency_key` per logical award; `wallets.balance` is a cached sum updated in the same transaction and guarded by `CHECK (balance >= 0)`. A database trigger rejects UPDATE and DELETE on the ledger.
- Per-user rules (daily caps, future spending) lock the user's wallet row first.

## Options considered

### Option A: unit of work + ledger (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Medium (ports, fakes, one adapter); implemented |
| Correctness | Atomic; double awards impossible at the database level |
| Auditability | Every coin has a row with a reason and a source |
| Performance | Microseconds per entry; wallet lock contention only within one user |

### Option B: mutable counters (`UPDATE users SET coins = coins + 10`)

Simple, but no history, no idempotency, and no way to answer "why does this player have 4,300 coins".

### Option C: SERIALIZABLE isolation everywhere

Correct, but every transaction needs a retry loop and side effects must be retry-safe. The
invariants here are single-row or constraint-shaped, so READ COMMITTED + constraints +
conditional updates is enough and simpler.

## Trade-off analysis

The ledger costs one extra insert per award and buys disputes answered from data, corrections
without editing history, and leaderboards computed from the same source of truth.

## Consequences

- Easier: refunds, adjustments, leaderboards, fraud investigations, reconciliation.
- Harder: corrections must be compensating entries (by design); admin tools must never edit balances directly.
- Revisit: if the leaderboard query gets slow, add a weekly totals table maintained in the same unit of work.

## Action items

1. [x] Unit of work port and SQLAlchemy adapter; ledger and wallet tables; tests.
2. [ ] Challenges, tournaments and adjustments write through the unit of work (B17, B20, B22).
3. [ ] Daily reconciliation query in monitoring ([OPERATIONS.md](../OPERATIONS.md#daily-checks)).
