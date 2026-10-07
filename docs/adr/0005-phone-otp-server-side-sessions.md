# ADR-0005: Phone number + SMS code sign-in, server-side sessions in an HttpOnly cookie

**Status:** Accepted
**Date:** 2026-10-07
**Deciders:** Backend developer; Mehdi (the SMS sender and template)

## Context

Players are Iranian teens and young adults on phones. Email is little used by this audience;
passwords add friction and support load. The existing code has passwordless sign-in by email
with server-side sessions (random token, hashed in the database, sent as an HttpOnly cookie).

## Decision

- Identify players by their **mobile number** (stored as `+989XXXXXXXXX`) and a 6-digit SMS code, sent through the provider's OTP/verify route with an approved template whose last line is `@<domain> #<code>` (enables WebOTP autofill on Android and `one-time-code` on iPhone).
- Keep **server-side sessions** in an HttpOnly, Secure, SameSite=Lax cookie, with the API on the same origin as the PWA.
- Abuse controls: OTP lifetime 2–3 minutes, 5 attempts per code, 60 s resend cooldown and a daily cap per number, keyed OTP hashes.

## Options considered

### Option A: phone OTP + server-side sessions (chosen)

**Pros:** lowest friction for the audience; one person ≈ one SIM; sessions revocable instantly (logout, ban); no token storage in JavaScript.
**Cons:** SMS cost and provider dependency; SIM swap and recycled numbers (acceptable for a game, not for money).

### Option B: JWT access + refresh tokens

**Pros:** stateless verification.
**Cons:** revocation needs a denylist anyway; tokens end up in `localStorage` (XSS theft); more code. No benefit at this scale.

### Option C: email magic links (existing)

Rejected for this audience.

## Trade-off analysis

SMS cost is small next to prizes; the real risk is **SMS pumping** (attackers triggering
messages to burn credit), handled by per-number and per-IP limits plus a daily spend alarm.

## Consequences

- Easier: account recovery is "sign in again"; banning a user revokes sessions immediately.
- Harder: SMS provider outages block new sign-ins (existing sessions keep working) → second provider.
- Revisit: before prizes are claimed, add an identity check (mobile number matched to national ID) at claim time, not at sign-up.

## Action items

1. [ ] Replace the email identifier with phone normalization (B10).
2. [ ] Jobs + SMS adapter + fallback provider (B11).
3. [ ] Template approval with both providers (B09).
