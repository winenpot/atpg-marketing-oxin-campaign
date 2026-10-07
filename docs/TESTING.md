# Testing

What we test, how, and what "good enough for launch" means. The rule: business rules that
can cost money or trust are tested against **real PostgreSQL**, including concurrency;
everything else gets a fast unit test or a manual check on a real phone.

## Contents

- [Running the tests](#running-the-tests)
- [What exists today](#what-exists-today)
- [Test plan by area](#test-plan-by-area)
- [Frontend](#frontend)
- [Manual test script (real phones)](#manual-test-script-real-phones)
- [Load test](#load-test)
- [CI gates](#ci-gates)

## Running the tests

```bash
uv sync
uv run pytest                     # unit + API tests; integration tests skip without a database

# integration tests (concurrency, constraints, migrations) need a migrated PostgreSQL:
docker compose up -d postgres
export DATABASE_URL=postgresql+asyncpg://lottery_passport:local_development_only@localhost:5432/lottery_passport
export TEST_DATABASE_URL=$DATABASE_URL
uv run alembic upgrade head
uv run pytest

uv run ruff check . && uv run ruff format --check . && uv run mypy app main.py scripts
```

On Windows PowerShell use `$env:TEST_DATABASE_URL = "..."` instead of `export`.

## What exists today

| Layer | Files | What they prove |
|---|---|---|
| Unit: code format | `tests/unit/test_codes.py` | Every single-character typo and every wrong city prefix is caught; Persian/Arabic digits, dashes, lowercase, O/0 and I/L/1 are folded; garbage never crashes the parser |
| Unit: redemption rules | `tests/unit/test_redemption_service.py` | Entries per city, coins per batch, replay, daily cap with rollback, Tehran midnight, lottery-only batches, missing pepper fails closed |
| Unit: generator helpers | `tests/unit/test_redemption_codes.py` | Unique codes, collision-tolerant generation, URL format |
| Integration: redemption | `tests/integration/test_redemption_flow.py` | Atomic commit; **12 users racing for one code → exactly one wins**; deterministic lock-wait race; double submit is idempotent; daily cap holds under concurrency; batch activate/void; ledger is append-only; idempotency key unique; balance never negative; full HTTP flow with error envelope |
| Integration: generator | `tests/integration/test_generate_codes.py` | Batches spanning chunks; only hashes stored; CSV mode 0600 + checksum; existing codes are not duplicated; refuses to overwrite a file |
| Integration: auth (existing) | `tests/integration/test_authentication_api.py` | Passwordless flow, sessions, logout |
| Integration: load-test helper | `tests/integration/test_loadtest_sessions.py` | Sessions work; revocation works; refuses production |

Mutation check done once: removing `redeemed_at IS NULL` from the claim makes four
integration tests fail. Repeat that kind of check for each new invariant (break the guard,
watch the test go red, restore it).

## Test plan by area

Coverage target: every invariant in [ARCHITECTURE.md](ARCHITECTURE.md#invariants-and-how-they-are-enforced)
has an integration test that fails if its guard is removed. No percentage gate on adapters.

| Area (item) | Unit tests | Integration tests (PostgreSQL) | Security/abuse tests |
|---|---|---|---|
| Phone normalization (B10) | `09xx`, `+98`, `0098`, `98`, Persian digits, spaces/dashes; reject landlines, short, long, non-Iranian | | |
| OTP sign-in (B10) | cooldown and cap math; hash keyed; expiry | two concurrent requests for one number create one challenge and one job; consume is single-use under concurrency | 6th attempt refused; new code does not reset the daily cap; response identical for known and unknown numbers |
| Jobs and SMS (B11) | backoff with full jitter stays under the cap; expired OTP jobs are dropped | two workers never claim the same job (SKIP LOCKED); a job abandoned by a dead worker is reclaimed by the reaper; finished jobs are deleted; OTP wiped after send | provider returns 4xx: no retry; 5xx/timeout: retry then fallback provider |
| Challenges (B17) | progress for `redeem_count` and `distinct_cities`; Tehran day/week keys at boundaries (23:59 / 00:00, Friday → Saturday) | claim pays once under concurrent double claim; claim after period end refused | cannot claim another user's progress |
| Submissions (B18) | URL parser accepts `/p/` and `/reel/`, rejects everything else (`javascript:`, other domains, look-alike domains) | approve twice pays once; reject then resubmit in the same period | |
| Leaderboard (B21) | tie-break by time reached; spends and admin adjustments excluded | query result equals a hand-computed fixture | nickname with bidi override cannot be saved, so it cannot appear |
| Tournaments (B22) | prize table validation | results entered twice pay once; payout only to existing users | venue staff cannot edit another lounge's tournament |
| Admin (B20) | role checks | every write creates an audit row | unauthenticated `/admin` returns login; wrong role returns 403 |
| Nickname (B15) | allow-list, ZWNJ placement, bidi/zero-width rejection, Arabic→Persian letter folding for uniqueness | uniqueness under concurrent PATCH (unique index) | |

Write the concurrency tests the way `test_redemption_flow.py` does: real database, real
transactions, `asyncio.gather` for volume and a gated commit for a deterministic race.

## Frontend

For Arman, in his repository:

- **Unit/component tests** (Vitest + Testing Library): code input grouping and local check-character validation (use the same test vectors as `tests/unit/test_codes.py`), phone input normalization, error-code → Persian message mapping (every code in [API_CONTRACT.md](API_CONTRACT.md#errors) has a message).
- **API mocks** (Mock Service Worker) for planned endpoints, built from the shapes in the contract; delete each mock when the real endpoint ships.
- **One end-to-end smoke test** (Playwright) against staging: open `/r/<test code>` signed out → sign in (staging allows a fixed test number) → success screen → passport shows the entry.
- **Manual accessibility pass**: tap targets, contrast in the dark theme, screen reader labels on the code and OTP inputs.

## Manual test script (real phones)

Run on D13 (dry run) and before each release, on one Android phone (Chrome) and one iPhone
(Safari), once on lounge Wi-Fi and once on mobile data:

1. Scan a printed test code's QR with the camera app → the site opens on the redeem screen.
2. Sign in with a new number; the SMS code fills itself (Android) or is offered above the keyboard (iPhone).
3. Success screen shows the city, +1 entry and coins; the URL bar no longer contains the code.
4. Press back: nothing is submitted again.
5. Type a code by hand with one wrong character → "check this character" before sending.
6. Redeem the same code again → same success, no extra coins (`replayed`).
7. Redeem a code already used by another account → "already used".
8. Reach the daily limit (on staging, set it to 3) → friendly message.
9. Complete and claim a daily challenge; submit an Instagram URL; approve it in admin; coins appear.
10. Leaderboard shows your nickname with the right weekly coins; switch lounge tabs.
11. Airplane mode mid-redeem, then back online, retry → exactly one credit.
12. Sign out → protected pages send you to sign-in.

## Load test

Measure before launch (B27), on **staging**, from a machine inside Iran, with
[`loadtest/redeem.js`](../loadtest/redeem.js) (k6). The script uses the
**constant-arrival-rate** executor: requests leave on a fixed schedule regardless of how fast
the server answers, so a slow server shows up as high latency instead of quietly reducing the
load (the "coordinated omission" trap of closed-loop tools such as `wrk` or `ab`).

```bash
uv run python -m scripts.loadtest_sessions --count 2000 --output loadtest/sessions.csv
uv run python -m scripts.generate_codes --city tokyo --quantity 20000 --label "load test" \
    --base-url https://staging.play.<domain> --output loadtest/codes.csv
uv run python -m scripts.code_batches activate <batch-id>
# add the load generator's IP to lounge_ips.conf on staging, then:
k6 run -e BASE_URL=https://staging.play.<domain> -e REDEEM_RPS=50 -e READ_RPS=400 -e DURATION=10m loadtest/redeem.js
uv run python -m scripts.loadtest_sessions --deactivate
```

Targets (5x the estimated peak): redemption p99 under 500 ms, reads p99 under 300 ms, failed
requests under 1%, **zero dropped iterations** (dropped iterations mean the generator could
not keep the schedule, so the run is invalid). Report p50, p95, p99, p99.9 and max **with the
request rate and duration**, plus the database CPU and connection count during the run.

A local smoke run of this script (laptop-class sandbox, 2 API workers, 30 redemptions/s +
150 reads/s for 15 s) gave 0 failures and redemption p99 around 40 ms. That proves the script
and the stack work together; it says nothing about the staging VM. Measure there.

## CI gates

`.github/workflows/ci.yml` runs on every pull request and push to `main`: Ruff lint and format,
mypy (strict), Alembic migrations against PostgreSQL 16, the full test suite with integration
tests required, a check that `requirements.txt` matches `uv.lock`, and a Docker build. Planned
additions with B25: `gitleaks` (secrets in history) and `pip-audit` (known-vulnerable
dependencies), both blocking.
