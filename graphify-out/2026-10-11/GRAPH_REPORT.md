# Graph Report - lottery-passport  (2026-10-11)

## Corpus Check
- 123 files · ~62,745 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .conf 5, (none) 4, .example 3)

## Summary
- 1055 nodes · 2795 edges · 78 communities (52 shown, 26 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 382 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- API Dependency Wiring
- Config and Domain Enums
- Passport and Repository Layer
- Rate Limit Middleware
- Code Hashing and Error Codes
- Database Unit of Work
- Code Format Registry
- Failure Throttle Port
- Architecture Decisions
- Database Migrations
- Load Test Scripts
- Postgres Throttle Adapter
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 71
- Community 72
- Community 73
- Community 74

## God Nodes (most connected - your core abstractions)
1. `PostgreSQLAdapter` - 62 edges
2. `Settings` - 61 edges
3. `CityCode` - 60 edges
4. `create_app()` - 50 edges
5. `User` - 39 edges
6. `AuthenticationService` - 29 edges
7. `CodeFormat` - 29 edges
8. `parse_code()` - 28 edges
9. `PassportProgress` - 28 edges
10. `RedemptionService` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Layered Architecture Spec (API→Service→Domain→Repo)` --semantically_similar_to--> `Hexagonal Architecture (Ports & Adapters)`  [INFERRED] [semantically similar]
  docs/BUILD_SPEC.md → CLAUDE.md
- `v2 Code Format Feature (Base32 + Luhn)` --conceptually_related_to--> `Code Format v2: 2-letter city + 10 Base32 chars + Luhn`  [INFERRED]
  CHANGELOG.md → docs/CODES.md
- `Legal Traps (purchase-linked draw, travel prizes)` --semantically_similar_to--> `Critical Path: codes, SMS, domain, servers, legal`  [INFERRED] [semantically similar]
  docs/GOTCHAS.md → ROADMAP.md
- `create_sessions()` --uses--> `AuthenticationService`  [INFERRED]
  scripts/loadtest_sessions.py → app/application/authentication.py
- `test_readiness_checker_accepts_available_dependency()` --uses--> `ReadinessChecker`  [INFERRED]
  tests/unit/test_readiness.py → app/application/ports.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Coin Correctness Guarantees (ledger, UoW, invariants)** — claude_coin_ledger, claude_unit_of_work, docs_architecture_invariants, docs_architecture_redemption_flow, docs_operations_daily_checks [INFERRED 0.95]
- **Production Infrastructure Stack (nginx + API + PostgreSQL + Worker)** — deploy_compose_prod_nginx, deploy_compose_prod_api, deploy_compose_prod_worker, docs_architecture_postgresql, docs_operations_nginx [EXTRACTED 1.00]
- **Code Format Security Chain (v2 format + HMAC + batch activation)** — docs_codes_format_v2, docs_codes_hmac_storage, docs_codes_batch_lifecycle, docs_security_code_guessing, docs_codes_why_v2 [INFERRED 0.95]
- **MVP Architecture Decision Records (ADR-0001 through ADR-0009)** — docs_adr_0001_keep_fastapi_modular_monolith_adr, docs_adr_0002_random_codes_hmac_storage_batches_adr, docs_adr_0003_unit_of_work_and_append_only_ledger_adr, docs_adr_0004_postgres_only_no_redis_for_mvp_adr, docs_adr_0005_phone_otp_server_side_sessions_adr, docs_adr_0006_domestic_single_vm_docker_compose_adr, docs_adr_0007_static_pwa_same_origin_adr, docs_adr_0008_sqladmin_back_office_adr, docs_adr_0009_park_city_passport_adr [EXTRACTED 1.00]
- **MVP Simplicity Principle: Fewest Moving Parts Under a 15-Day Deadline** — docs_adr_0004_postgres_only_no_redis_for_mvp_single_datastore_rationale, docs_adr_0006_domestic_single_vm_docker_compose_domestic_hosting_rationale, docs_adr_0001_keep_fastapi_modular_monolith_fastapi_rationale [INFERRED 0.85]

## Communities (78 total, 26 thin omitted)

### Community 0 - "API Dependency Wiring"
Cohesion: 0.06
Nodes (68): get_authentication_service(), get_current_user(), get_passport_service(), get_readiness_checker(), get_redemption_service(), get_wallet_service(), Depends, Request (+60 more)

### Community 1 - "Config and Domain Enums"
Cohesion: 0.06
Nodes (81): get_settings(), BatchEventType, BatchStatus, StrEnum, Lifecycle of one print run of codes. ``generated``: codes exist in the database…, One append-only history row per thing that happened to a batch. Recorded in…, CodeBatchEventModel, CodeBatchModel (+73 more)

### Community 2 - "Passport and Repository Layer"
Cohesion: 0.06
Nodes (31): PassportRepository, Protocol, UUID, Read side of passports. Entries are only added inside a unit of work., CodeLookup, LedgerInTransaction, PassportsInTransaction, datetime (+23 more)

### Community 3 - "Rate Limit Middleware"
Cohesion: 0.08
Nodes (27): RateLimitMiddleware, RequestLoggingMiddleware, draw_winners(), Reproducible weighted draw (procedure in docs/DRAW.md). Anyone holding the…, SHA-256 of the canonical snapshot, published BEFORE the seed is known., Unbiased integer in ``[0, bound)`` derived from the seed and a label., Draw up to ``count`` distinct participants, weighted by entries. ``label``…, snapshot_digest() (+19 more)

### Community 4 - "Code Hashing and Error Codes"
Cohesion: 0.15
Nodes (34): hash_redemption_code(), StrEnum, Stable error codes the frontend maps to user-facing copy., Keyed hash of a canonical code; the pepper never lives in the database. A plain…, RedemptionErrorCode, compute_check_value(), generate_code(), Return the Luhn mod N check value for ``city`` + ``body``. The city index is… (+26 more)

### Community 5 - "Database Unit of Work"
Cohesion: 0.20
Nodes (26): Any, PostgreSQLAdapter, create_batch(), create_user(), database(), ledger_rows_for(), make_service(), datetime (+18 more)

### Community 6 - "Code Format Registry"
Cohesion: 0.11
Nodes (30): FormatRegistryError, get_format(), Add a format. Parsing picks the format by length, so lengths differ., Remove a format. For tests only: never unregister a printed format., Return a registered format; empty means the default one., Fail loudly if a frozen batch's format no longer matches the code. ``frozen``…, Raised when a format spec is invalid, unknown or clashes with another., register_format() (+22 more)

### Community 7 - "Failure Throttle Port"
Cohesion: 0.14
Nodes (22): Clock, FailureThrottle, Protocol, Port for the per-account invalid-code attempt throttle. The application layer…, Append-only log of invalid-code attempts, queryable by window., How many invalid attempts before we block, and how wide the window is., ThrottleSettings, datetime (+14 more)

### Community 8 - "Architecture Decisions"
Cohesion: 0.09
Nodes (27): ADR-0001: Keep FastAPI Modular Monolith, FastAPI Over Django Rationale: No Rewrite on a 15-Day Schedule, ADR-0002: Random Codes, HMAC Storage, Batches with Kill Switch, Brute-Force Resistant Code Design: 50-bit Random + HMAC Pepper, ADR-0004: PostgreSQL Only for MVP (Jobs Table, No Redis/Celery), Single Datastore Simplicity Rationale: Transactional Enqueue, One Backup Target, ADR-0005: Phone OTP + Server-Side Sessions in HttpOnly Cookie, SMS Auth Rationale: Lowest Friction for Iranian Mobile-First Audience (+19 more)

### Community 9 - "Database Migrations"
Cohesion: 0.12
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 10 - "Load Test Scripts"
Cohesion: 0.14
Nodes (22): argparse, asyncio, csv, count_active_loadtest_users(), create_sessions(), deactivate(), main(), main_async() (+14 more)

### Community 11 - "Postgres Throttle Adapter"
Cohesion: 0.19
Nodes (18): PostgreSQL adapter for the per-account invalid-code attempt throttle., AuthenticationChallengeModel, Base, CoinLedgerEntryModel, PassportProgressModel, Append-only log of CODE_INVALID outcomes, used by the per-account throttle., RedemptionCodeModel, RedemptionFailureModel (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (6): AuthenticationChallengeRepository, AuthenticationCodeGenerator, datetime, Protocol, UUID, UserRepository

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (6): AuthenticationChallenge, FakeChallenges, FakeSessions, FakeUsers, datetime, UUID

### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (14): Settings, BaseSettings, field_validator, MonkeyPatch, test_blank_secrets_are_treated_as_unset(), test_demo_rejects_loopback_database(), test_demo_requires_api_key(), test_development_can_use_local_database() (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (18): CodeFormatError, CodeProblem, parse_code(), StrEnum, Parse user input into a :class:`ParsedCode` or raise ``CodeFormatError``. The…, Why a typed code was rejected before any database lookup., Raised when user input cannot be a valid code., parametrize (+10 more)

### Community 16 - "Community 16"
Cohesion: 0.16
Nodes (14): canonicalLength(), checkIsValid(), CITY_CHECK_INDEX, DEFAULT_FORMAT_ID, FORMATS, formatsByLength(), luhnModNSum(), normalizeCode() (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (8): FakeClock, FakeLedger, FakeUnitOfWork, BaseException, Self, TracebackType, Store, test_missing_pepper_fails_closed()

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (17): GitHub Actions CI Workflow, CI Quality Job (lint, types, tests, build), Production Docker Compose Stack, API Service (uvicorn, 4 workers), nginx Service (TLS, static PWA, rate limits), Worker Service (jobs loop, SMS sending), POST /api/v1/redemptions — Code Redemption Endpoint, Architecture Document (+9 more)

### Community 19 - "Community 19"
Cohesion: 0.19
Nodes (11): create_app(), lifespan(), unit_of_work(), EmailSender, DevelopmentEmailSender, UnavailableEmailSender, asyncio, test_me_requires_session() (+3 more)

### Community 20 - "Community 20"
Cohesion: 0.23
Nodes (13): AuthenticationError, AuthenticationSettings, Exception, Raised for any invalid authentication attempt., build_service(), FakeClock, FakeEmailSender, FixedCodeGenerator (+5 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (11): check_is_valid(), CodeFormat, Random bits per code: what a guesser is up against., The frozen part of the format, as plain JSON-able data., SHA-256 of :meth:`spec`; stored on a batch when it is frozen., True when ``check`` is the correct check character for the code., Everything that decides how a code looks and is checked. ``grouping`` splits…, _values() (+3 more)

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (6): User, PostgreSQLChallengeRepository, PostgreSQLUserRepository, datetime, UUID, user_from_model()

### Community 23 - "Community 23"
Cohesion: 0.27
Nodes (9): Protocol, UUID, WalletReader, LedgerEntry, LedgerReason, StrEnum, Coins: an append-only ledger plus a cached balance per user. The ledger is the…, Wallet (+1 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (10): ZoneInfo, configure_logging(), JsonFormatter, functools, json, LogRecord, pydantic, pydantic_settings (+2 more)

### Community 25 - "Community 25"
Cohesion: 0.25
Nodes (9): CodeBatch, Printed code batches: lifecycle, format tracking and append-only events., True once the batch's format can no longer change (post-export)., One printed code. Only its keyed hash is stored, never the plaintext., RedemptionCode, dataclasses, datetime, enum (+1 more)

### Community 26 - "Community 26"
Cohesion: 0.16
Nodes (15): API Contract (player app), OTP Authentication Flow (request+verify), GET /api/v1/config — Server Config Endpoint, Weekly PS5 Draw Endpoints, Stable JSON Error Code Envelope, Events and Tournaments Endpoints, Idempotency-Key Header Strategy, Leaderboard Endpoints (weekly, games) (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (15): Tehran Timezone (Asia/Tehran) Time Handling, Printed Codes Specification, Code Batch Lifecycle (generated→active→void), CodeFormat Registry in app/domain/codes.py, Code Format v2: 2-letter city + 10 Base32 chars + Luhn, Browser Code Validator (docs/frontend/codes.js), HMAC-SHA256(pepper, code) — No Plaintext in DB, Luhn mod 32 Check Character (+7 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (8): BaseException, Self, TracebackType, ``async with SqlAlchemyUnitOfWork(factory) as uow: ...; await uow.commit()``., SqlAlchemyUnitOfWork, Event, GatedCommitUnitOfWork, Holds its transaction open (row locks included) until ``gate`` is set.

### Community 29 - "Community 29"
Cohesion: 0.30
Nodes (5): AuthenticationService, VerificationResult, AccountStatus, StrEnum, VerificationStatus

### Community 30 - "Community 30"
Cohesion: 0.26
Nodes (5): ClaimedCode, A code this transaction has just marked as redeemed., FakeCodes, datetime, UUID

### Community 31 - "Community 31"
Cohesion: 0.21
Nodes (12): CHANGELOG, Append-only Coin Ledger and Wallets Feature, Unit of Work — Atomic Redemption Feature, v2 Code Format Feature (Base32 + Luhn), Lottery Passport Engineering Guide (CLAUDE.md), AuthenticationService (framework-free), Seven City Passports (Paris, Berlin, ...), Printed Code Format v2 (app/domain/codes.py) (+4 more)

### Community 32 - "Community 32"
Cohesion: 0.24
Nodes (12): Legal Traps (purchase-linked draw, travel prizes), Team Roles and Agreements, Arman — Frontend Developer (PWA, external), Backend Developer / Technical Lead, CEO — Scope and Budget Approver, Mehdi — Marketing Manager, Project README, MVP Roadmap (15 days) (+4 more)

### Community 33 - "Community 33"
Cohesion: 0.18
Nodes (11): app/api/ — FastAPI Routes and Schemas, app/application/ — Use Cases and Ports, app/app.py — Composition Root, app/domain/ — Pure Business Rules Layer, Hexagonal Architecture (Ports & Adapters), app/infrastructure/ — External Adapters, Backend Build Specification, Anti-abuse and Risk Engine Spec (+3 more)

### Community 34 - "Community 34"
Cohesion: 0.33
Nodes (4): SessionRepository, AuthenticatedSession, PostgreSQLSessionRepository, session_from_model()

### Community 35 - "Community 35"
Cohesion: 0.29
Nodes (6): NullFailureThrottle, datetime, UUID, Record one CODE_INVALID outcome for the given user., Return the number of failures recorded since ``window_start`` (inclusive)., No-op implementation: never throttles. Use in development or unit tests that…

### Community 36 - "Community 36"
Cohesion: 0.24
Nodes (10): Operations (DevOps) Runbook, Backup (pg_dump + restic, RPO 6h, RTO 2h), Daily SQL Wallet/Ledger Reconciliation Checks, Release Deployment (git tags, deploy.sh), Launch Checklist (D15), Monitoring with Uptime Kuma and GlitchTip, nginx Config (TLS, rate limits, lounge IPs), Incident Runbooks (SMS, DB, overload, leak) (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.28
Nodes (7): api_key_header, Depends, Security, require_api_key(), fastapi_security, secrets, test_api_key_is_checked_without_plaintext_logging()

### Community 38 - "Community 38"
Cohesion: 0.25
Nodes (8): _luhn_mod_n_sum(), normalize_input(), Printed product codes: a city prefix + random body + one check character. The…, Fold whatever a person typed or scanned into canonical characters. The result…, _strip_separators(), math, test_normalize_input_never_raises_on_garbage(), unicodedata

### Community 39 - "Community 39"
Cohesion: 0.22
Nodes (9): ADR-0003: Unit of Work + Append-Only Coin Ledger, Atomic Multi-Table Write Rationale: No Split Transaction Burns Codes Without Credit, Capacity Planning Cheatsheet (1/2/3 Domestic Servers), Server Sizing Decision Process: Inventory → Benchmark → Monitor → Traffic Model → Load Test → Failure Drill → ADR-0010, CI Pipeline (.github/workflows/ci.yml), Concurrency Testing Pattern (asyncio.gather + Gated Commit), k6 Load Test (Constant-Arrival-Rate), Manual Test Script (Real Phones) (+1 more)

### Community 40 - "Community 40"
Cohesion: 0.31
Nodes (6): pytest, AvailableDependency, asyncio, test_readiness_checker_accepts_available_dependency(), test_readiness_checker_rejects_unavailable_dependency(), UnavailableDependency

### Community 41 - "Community 41"
Cohesion: 0.32
Nodes (6): do_run_migrations(), run_async_migrations(), run_migrations_online(), Connection, logging_config, sqlalchemy_engine

### Community 42 - "Community 42"
Cohesion: 0.32
Nodes (6): InsufficientCoinsError, Exception, A debit would take the wallet below zero., NewLedgerEntry, A coin movement to record. ``amount`` is negative for spending.…, SqlLedger

### Community 43 - "Community 43"
Cohesion: 0.32
Nodes (5): PostgreSQLFailureThrottle, async_sessionmaker, AsyncSession, datetime, UUID

### Community 44 - "Community 44"
Cohesion: 0.32
Nodes (7): asUser(), codes, options, read(), redeem(), sessions, ref_k6

### Community 45 - "Community 45"
Cohesion: 0.25
Nodes (5): shutil, skipif, subprocess, The vectors Arman's tests use must keep matching the server's parser. If this…, test_browser_validator_passes_the_vectors()

### Community 46 - "Community 46"
Cohesion: 0.29
Nodes (6): format_printed(), ParsedCode, A syntactically valid code whose check character matches., Human-friendly grouping used on packaging, e.g. ``TO-7KQ2-M9XH-4R6``., Group a canonical code for printing, e.g. ``PP-XXXX-XXXX-XXX``., test_printed_grouping_follows_the_format()

### Community 47 - "Community 47"
Cohesion: 0.38
Nodes (3): datetime, SecureAuthenticationCodeGenerator, SystemClock

### Community 49 - "Community 49"
Cohesion: 0.33
Nodes (6): fastapi_testclient, os, client(), fixture, TestClient, test_database_url()

### Community 50 - "Community 50"
Cohesion: 0.53
Nodes (6): Challenges and Submissions Endpoints, Game Design Document, Challenge Types: redeem_count, social_post, manual, Coin Economy (default table), Target Audience: Competitive Gen Z Gamers, Game Loops (core / daily / weekly / season)

### Community 51 - "Community 51"
Cohesion: 0.53
Nodes (6): Security Threat Model and Controls, Admin Panel Security (IP allow-list, TOTP, roles), Secrets Inventory and Rotation Policy, Session Management: HttpOnly+Secure+SameSite Cookie, SMS Pumping Prevention (T6), Security Threat Model (T1–T20)

### Community 52 - "Community 52"
Cohesion: 0.40
Nodes (5): TestClient, test_cors_allows_configured_origin(), test_health_returns_ok(), test_rate_limit_excludes_health_and_limits_other_routes(), test_ready_reports_unavailable_database()

## Knowledge Gaps
- **44 isolated node(s):** `backup.sh script`, `deploy.sh script`, `CITY_CHECK_INDEX`, `vectors`, `registry` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 284 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Community 14` to `API Dependency Wiring`, `Config and Domain Enums`, `Community 37`, `Database Unit of Work`, `Load Test Scripts`, `Postgres Throttle Adapter`, `Community 49`, `Community 19`, `Community 52`, `Community 55`, `Community 24`, `Community 57`, `Community 56`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `create_app()` connect `Community 19` to `API Dependency Wiring`, `Config and Domain Enums`, `Passport and Repository Layer`, `Rate Limit Middleware`, `Database Unit of Work`, `Code Format Registry`, `Failure Throttle Port`, `Load Test Scripts`, `Community 14`, `Community 20`, `Community 22`, `Community 23`, `Community 24`, `Community 28`, `Community 29`, `Community 34`, `Community 43`, `Community 47`, `Community 49`, `Community 52`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `CityCode` connect `Code Hashing and Error Codes` to `Config and Domain Enums`, `Passport and Repository Layer`, `Database Unit of Work`, `Community 38`, `Failure Throttle Port`, `Code Format Registry`, `Postgres Throttle Adapter`, `Community 46`, `Community 15`, `Community 17`, `Community 21`, `Community 25`, `Community 30`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `PostgreSQLAdapter` (e.g. with `Settings` and `CodeBatchModel`) actually correct?**
  _`PostgreSQLAdapter` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `Settings` (e.g. with `require_api_key()` and `logout()`) actually correct?**
  _`Settings` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `CityCode` (e.g. with `RedemptionResult` and `ClaimedCode`) actually correct?**
  _`CityCode` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `create_app()` (e.g. with `api_error_handler()` and `ApiError`) actually correct?**
  _`create_app()` has 9 INFERRED edges - model-reasoned connections that need verification._