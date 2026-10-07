# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
releases are git tags `vYYYY.MM.DD-N` ([docs/OPERATIONS.md](docs/OPERATIONS.md#deploying-a-release)).

## [Unreleased]

### Added

- Printed code format v2: city prefix + 10 random Crockford Base32 characters + Luhn mod 32
  check character; tolerant input normalization (Persian/Arabic digits, dashes, case, O/0, I/L/1).
- Code batches (`generated`, `active`, `void`) with `python -m scripts.generate_codes` and
  `python -m scripts.code_batches`; the generator writes a 0600 CSV with QR URLs and a SHA-256 file.
- Unit of work for multi-table writes; atomic redemption with idempotent replay and a per-user
  daily cap counted in Tehran days.
- Append-only coin ledger and wallets; `GET /api/v1/me/wallet`.
- `POST /api/v1/redemptions` with stable error codes in an `{"error": {"code", "message"}}`
  envelope (also used for 401, 429 and 500).
- Reproducible weighted draw (`app/domain/draw.py`) and its procedure (`docs/DRAW.md`).
- Production deployment: `deploy/compose.prod.yml`, nginx config with lounge-aware rate limits,
  `deploy.sh`, `backup.sh` (restic), `restore_check.sh`.
- Load testing: `loadtest/redeem.js` (k6, open model) and `python -m scripts.loadtest_sessions`.
- Frontend helpers: `docs/frontend/codes.js` and shared test vectors.
- Documentation: roadmap, per-person TODOs, architecture, ADRs 0001–0008, API contract,
  security, operations, testing, codes, draw, game design, team, gotchas, code review.
- Settings: `REDEMPTION_DAILY_LIMIT_PER_USER`, `CAMPAIGN_TIMEZONE`, `DB_STATEMENT_TIMEOUT_MS`.

### Changed

- The Docker image installs hash-locked `requirements.txt` (any PyPI mirror can be used safely)
  instead of copying `uv` from ghcr.io; CI checks the file matches `uv.lock`.
- Production may use a Compose service name as the database host; the pepper must be 32+
  characters outside development; blank secrets count as unset.
- CI type-checks `scripts/` and pins the `uv` version.

### Removed

- `POST /api/v1/me/redeem` (replaced by `POST /api/v1/redemptions`).
- `scripts/generate_redemption_codes.py` (v1 format).
- The non-transactional `PassportRepository.add_points` and `PostgreSQLRedemptionCodeRepository`.

### Fixed

- A crash between claiming a code and crediting it could burn the code without credit.
- Documented script invocation (`python scripts/...`) failed with `No module named 'app'`.
