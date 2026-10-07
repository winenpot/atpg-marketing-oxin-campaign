# API contract (player app)

The agreement between the backend and the PWA. **Live** endpoints exist in the code today;
**planned** ones have their final shapes here so the frontend can be built against mocks now
(for example with Mock Service Worker) and switched to the real API when the backend item ships.
The live OpenAPI document is at `/docs` in development (disabled in production).

If something here is wrong or missing, change this file in a pull request first; code follows the contract.

## Contents

- [Conventions](#conventions)
- [Errors](#errors)
- [Authentication](#authentication)
- [Profile and configuration](#profile-and-configuration)
- [Codes, passport and wallet](#codes-passport-and-wallet)
- [Challenges and submissions](#challenges-and-submissions)
- [Leaderboards](#leaderboards)
- [Tournaments](#tournaments)
- [Health](#health)
- [Frontend recipes](#frontend-recipes)

## Conventions

| Topic | Rule |
|---|---|
| Base URL | Same origin as the PWA: `https://play.<domain>/api/v1/...`. No CORS in production. |
| Format | JSON in and out, UTF-8. Field names in `snake_case`. |
| Authentication | Session cookie set by `POST /auth/verify` (HttpOnly, Secure, SameSite=Lax). The browser sends it automatically on same-origin `fetch`. JavaScript never sees or stores a token. |
| Time | ISO 8601 in UTC, for example `2026-10-10T08:30:00Z`. Convert to Tehran time / Jalali for display. "Today" and "this week" come from `GET /config`, never from the phone's clock. |
| IDs | UUID strings unless stated. |
| Retries | `POST /redemptions` and `POST /challenges/{id}/claim` are safe to retry with the same body; a repeat returns the first result with `"replayed": true`. |
| Rate limits | `429` with a `Retry-After` header (seconds). Show a countdown; do not retry automatically before it. |
| Versioning | Additive changes (new fields, new endpoints) stay in `/api/v1`. Ignore unknown fields. Breaking changes go to `/api/v2`. |
| Local development | Proxy `/api` from the Vite dev server to staging (`server.proxy`), so cookies and paths behave like production. If the Secure cookie does not stick on `http://localhost`, run the dev server over HTTPS. |

## Errors

Every error from new endpoints has this shape (the auth endpoints move to it with B10):

```json
{"error": {"code": "CODE_MISTYPED", "message": "One character looks mistyped; check the code on the package."}}
```

Switch on `code`; show your own Persian copy. `message` is for developers and logs.

| Code | HTTP | Meaning | What the app should do |
|---|---|---|---|
| `AUTH_REQUIRED` | 401 | No or expired session | Go to sign-in, then come back |
| `PHONE_INVALID` | 422 | Not an Iranian mobile number | Highlight the field |
| `OTP_COOLDOWN` | 429 | A code was sent less than a minute ago | Countdown from `Retry-After` |
| `OTP_DAILY_LIMIT` | 429 | Too many codes for this number today | "Try again tomorrow" |
| `OTP_INVALID` | 401 | Wrong, expired, used, or too many attempts | "Wrong code"; offer resend |
| `CODE_MALFORMED` | 400 | Not a product code at all | "This is not a code from our drinks" |
| `CODE_MISTYPED` | 400 | Right shape, one character wrong | "Check the characters, especially 0/O and 1/I" |
| `CODE_INVALID` | 404 | Unknown code, or not released yet | "Code not valid" |
| `CODE_ALREADY_REDEEMED` | 409 | Another account redeemed it | "Already used"; link to support |
| `REDEMPTION_DAILY_LIMIT` | 429 | Daily redemption limit reached | "Come back tomorrow" |
| `REDEMPTION_THROTTLED` | 429 | Too many invalid codes recently | Countdown from `Retry-After` |
| `REDEMPTION_NOT_CONFIGURED` | 503 | Server misconfiguration | Generic error; we get alerted |
| `NICKNAME_INVALID` | 422 | Length or characters not allowed | Show the rule |
| `NICKNAME_TAKEN` | 409 | Someone has it | Suggest another |
| `VENUE_UNKNOWN` | 422 | Bad lounge id | Reload `/config` |
| `TERMS_NOT_ACCEPTED` | 403 | Action needs accepted T&Cs | Show the T&C screen |
| `CHALLENGE_NOT_ACTIVE` | 409 | Challenge ended or not started | Refresh the list |
| `CHALLENGE_NOT_COMPLETED` | 409 | Target not reached yet | Show progress |
| `SUBMISSION_EXISTS` | 409 | Already submitted for this period | Show its status |
| `URL_INVALID` | 422 | Not an accepted Instagram post/reel URL | Show the accepted format |
| `RATE_LIMITED` | 429 | Generic limit (nginx or API) | Countdown from `Retry-After` |
| `INTERNAL_ERROR` | 500 | Bug | Generic error; we get alerted |

## Authentication

### `POST /api/v1/auth/request` (planned shape, B10)

Today this endpoint is **live with email** (`{"identifier": "user@example.com"}`); B10 switches it to phone.

```http
POST /api/v1/auth/request
{"phone": "۰۹۱۲ ۳۴۵ ۶۷۸۹"}
```

Accepts Persian or Latin digits, spaces, `+98`, `0098`, `98` or a leading `0`.

```http
202 Accepted
{"resend_after_seconds": 60, "expires_in_seconds": 150, "code_length": 6}
```

The response is the same whether the number is new or known.

### `POST /api/v1/auth/verify` (planned shape, B10)

```http
POST /api/v1/auth/verify
{"phone": "09123456789", "code": "483920"}
```

```http
200 OK
Set-Cookie: lottery_passport_session=...; HttpOnly; Secure; SameSite=Lax; Path=/
{"id": "4b0c...", "phone_masked": "0912***6789", "nickname": null, "home_venue": null, "terms_accepted": false}
```

The first successful verify creates the account. If `nickname` is null or `terms_accepted`
is false, send the player to the profile screen before anything else.

### `POST /api/v1/auth/logout` (live)

`204 No Content`; the cookie is cleared.

## Profile and configuration

### `GET /api/v1/config` (planned, B15; no authentication)

```json
{
  "server_time": "2026-10-10T08:30:00Z",
  "timezone": "Asia/Tehran",
  "day_key": "D:2026-10-10",
  "week_key": "W:2026-10-10",
  "week_starts_at": "2026-10-09T20:30:00Z",
  "week_ends_at": "2026-10-16T20:30:00Z",
  "terms_version": "2026-10-01",
  "limits": {"redemptions_per_day": 20},
  "cities": [
    {"campaign": "tokyo", "prefix": "TO"},
    {"campaign": "moscow", "prefix": "MO"}
  ],
  "venues": [{"id": 1, "name": "..."}]
}
```

Cities are listed in the order the passport shows them. Persian city names and artwork live in the frontend.

### `GET /api/v1/me` (live; shape changes with B15)

Live today: `{"id", "identifier", "display_name", "account_status", "verification_status", "created_at", "updated_at"}`.
Target (B15): the object returned by `/auth/verify` above.

### `PATCH /api/v1/me` (live for `display_name`; target fields with B15)

```json
{"nickname": "Shadow_Fiend", "home_venue_id": 1, "accept_terms_version": "2026-10-01"}
```

All fields optional. Nickname rules: 3–20 characters; Latin letters, digits, `_` `.` `-`,
Persian letters and the zero-width non-joiner; unique ignoring case and Arabic/Persian letter
variants. Errors: `NICKNAME_INVALID`, `NICKNAME_TAKEN`, `VENUE_UNKNOWN`.

## Codes, passport and wallet

### `POST /api/v1/redemptions` (live)

```http
POST /api/v1/redemptions
{"code": "TO-7KQ2-M9XH-4R6"}
```

Send exactly what the user typed or what came in the QR URL; the server normalizes it.

```http
200 OK
{"city": "tokyo", "entries_added": 1, "city_entries": 3, "coins_awarded": 10, "coin_balance": 140, "replayed": false}
```

`replayed: true` means this account had already redeemed this code: show the same success
screen without new confetti. Errors: `CODE_MALFORMED`, `CODE_MISTYPED`, `CODE_INVALID`,
`CODE_ALREADY_REDEEMED`, `REDEMPTION_DAILY_LIMIT`, `REDEMPTION_THROTTLED` (B19), `AUTH_REQUIRED`.

### `GET /api/v1/me/passports` (live)

```json
[{"campaign": "tokyo", "points": 3, "updated_at": "2026-10-10T08:30:00Z"}]
```

Only cities with at least one entry appear; render all cities from `/config` and fill in the
ones present. `points` is the number of entries in that city's draw.

### `GET /api/v1/me/wallet` (live)

```json
{
  "balance": 140,
  "lifetime_earned": 160,
  "recent": [
    {"id": 812, "amount": 10, "reason": "code_redemption", "created_at": "2026-10-10T08:30:00Z"},
    {"id": 640, "amount": -20, "reason": "store_purchase", "created_at": "2026-10-09T17:02:11Z"}
  ]
}
```

`reason` values: `code_redemption`, `challenge_reward`, `tournament_prize`,
`social_post_reward`, `admin_adjustment`, `store_purchase`.

## Challenges and submissions

### `GET /api/v1/challenges` (planned, B17)

```json
{
  "day_key": "D:2026-10-10",
  "week_key": "W:2026-10-10",
  "items": [
    {
      "id": "8d1f...", "kind": "redeem_count", "period": "day",
      "title": "...", "description": "...",
      "target": 2, "progress": 1, "reward_coins": 15,
      "status": "in_progress", "ends_at": "2026-10-10T20:30:00Z"
    },
    {
      "id": "c2aa...", "kind": "social_post", "period": "week",
      "title": "...", "description": "...",
      "target": 1, "progress": 0, "reward_coins": 50,
      "status": "pending_review", "ends_at": "2026-10-16T20:30:00Z",
      "submission": {"id": "f00d...", "status": "pending", "url": "https://www.instagram.com/p/...", "reason": null}
    }
  ]
}
```

`status`: `in_progress`, `claimable`, `claimed`, `pending_review`, `rejected`.
`kind`: `redeem_count` (redeem N codes in the period), `distinct_cities` (N different cities
in the period), `social_post` (URL reviewed by marketing), `manual` (staff confirms in admin).
Titles and descriptions come from the admin panel in Persian.

### `POST /api/v1/challenges/{id}/claim` (planned, B17)

`200 {"coins_awarded": 15, "coin_balance": 155, "replayed": false}`.
Errors: `CHALLENGE_NOT_COMPLETED`, `CHALLENGE_NOT_ACTIVE`.

### `POST /api/v1/challenges/{id}/submissions` (planned, B18)

```json
{"url": "https://www.instagram.com/p/C9xyz123/"}
```

`201 {"id": "f00d...", "status": "pending"}`. Accepted URLs: `https://(www.)instagram.com/p/<id>/`
and `/reel/<id>/`, with or without query strings (stripped server-side).
Errors: `URL_INVALID`, `SUBMISSION_EXISTS`, `CHALLENGE_NOT_ACTIVE`, `TERMS_NOT_ACCEPTED`.

### `GET /api/v1/me/submissions` (planned, B18)

List of `{"id", "challenge_id", "url", "status", "reason", "created_at", "reviewed_at"}`, newest first.

## Leaderboards

### `GET /api/v1/leaderboards/weekly?venue=all|<venue_id>` (planned, B21)

```json
{
  "week_key": "W:2026-10-10",
  "venue": {"id": 1, "name": "..."},
  "updated_at": "2026-10-10T08:30:00Z",
  "entries": [{"rank": 1, "nickname": "Shadow_Fiend", "coins": 420, "is_me": false}],
  "me": {"rank": 57, "coins": 95}
}
```

Ranked by coins **earned** this week (spending does not lower your rank; admin adjustments do
not count). Ties: whoever reached the score first ranks higher. Top 50; `me` is null if you
earned nothing this week. Cached up to 60 seconds: show `updated_at`.

## Tournaments

### `GET /api/v1/tournaments?status=upcoming|finished` (planned, B22)

```json
[
  {
    "id": "a1b2...", "title": "...", "game": "FC 26", "venue": {"id": 2, "name": "..."},
    "starts_at": "2026-10-15T15:30:00Z", "status": "finished",
    "prizes": [{"place": 1, "coins": 300}, {"place": 2, "coins": 150}, {"place": 3, "coins": 75}],
    "results": [{"place": 1, "nickname": "Shadow_Fiend", "coins": 300}]
  }
]
```

## Health

`GET /health` → `{"status": "ok"}` (process up). `GET /ready` → `{"status": "ready"}` or 503
(database reachable). Not under `/api/v1`; used by monitoring.

## Frontend recipes

**QR landing (`/r/:code`)**

1. Read `code` from the path. If signed out, save it in `sessionStorage` and go to sign-in.
2. After sign-in (or immediately), `POST /api/v1/redemptions` with the saved code.
3. Call `history.replaceState(null, "", "/passport")` so the code does not stay in the URL bar or history.
4. Remove the code from `sessionStorage` after any final answer (success or error).

**OTP input that fills itself**

```html
<input name="otp" autocomplete="one-time-code" inputmode="numeric" pattern="[0-9]*" maxlength="6" dir="ltr">
```

```js
// Android Chrome: reads the SMS whose last line is "@play.<domain> #123456".
if ("OTPCredential" in window) {
  const abort = new AbortController();
  navigator.credentials
    .get({ otp: { transport: ["sms"] }, signal: abort.signal })
    .then((otp) => { input.value = otp.code; form.requestSubmit(); })
    .catch(() => {}); // user dismissed or unsupported: manual entry still works
  // call abort.abort() if the user leaves the screen
}
```

iPhone Safari does not run this API, but `autocomplete="one-time-code"` offers the code above
the keyboard from the same SMS.

**Typed codes**

Use `dir="ltr" autocapitalize="characters" autocomplete="off" spellcheck="false"`, show the
grouping `TO-XXXX-XXXX-XXX` as the user types, and validate the check character locally
before sending ([CODES.md](CODES.md#validating-codes-in-the-browser)).
