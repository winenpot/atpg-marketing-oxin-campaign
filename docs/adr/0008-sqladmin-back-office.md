# ADR-0008: SQLAdmin for the back office

**Status:** Accepted
**Date:** 2026-10-07
**Deciders:** Backend developer; Mehdi (main user)

## Context

Marketing and lounge staff need to manage challenges, approve social submissions, enter
tournament results, look up users and adjust coins with a reason. There is no time to build a
custom admin frontend, and Arman's time is reserved for the player app.

## Decision

Use **SQLAdmin** (version 0.32 at the time of writing), mounted at `/admin`, served on the same
VM but reachable only from allow-listed IPs (office, VPN, lounges) through nginx, with:

- separate `admin_users` (not player accounts), passwords hashed with a slow hash, roles: `owner`, `marketing`, `venue_staff`, `support`;
- read-only views for the ledger, codes and redemptions;
- custom actions for "approve/reject submission", "enter tournament results" and "adjust coins" that call the same application services as the API (never raw edits of balances);
- an audit log row for every admin write.

## Options considered

### Option A: SQLAdmin (chosen)

**Pros:** works with the existing SQLAlchemy models; list/search/filter for free; custom actions possible; a day to set up.
**Cons:** custom workflows need code; styling is generic (fine for staff).

### Option B: custom admin pages in the PWA

Rejected: competes with player features for Arman's time.

### Option C: direct database access (psql, DBeaver) for staff

Rejected: no roles, no audit, one typo away from a disaster.

## Trade-off analysis

The admin panel is a security boundary as much as a convenience: the roles, IP allow-list
and audit log are the point, not the forms.

## Consequences

- Easier: Mehdi self-serves; you stop being the bottleneck for every approval.
- Harder: every custom action must reuse the application services so the ledger rules hold.
- Revisit: a purpose-built reviewer screen if submission volume exceeds what one person approves comfortably.

## Action items

1. [ ] `admin_users`, `audit_log`, SQLAdmin views and actions, nginx allow-list (B20).
2. [ ] Train Mehdi and lounge staff (B30).
