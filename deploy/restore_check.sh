#!/usr/bin/env bash
# Restore the latest backup into a throwaway PostgreSQL container and check it.
# Run weekly, and always before launch. Prints how long the restore took: that
# number is your recovery time (RTO) for the database part.
set -euo pipefail

deploy_dir="$(cd "$(dirname "$0")" && pwd)"
set -a
# shellcheck source=/dev/null
source "$deploy_dir/backup.env"
set +a

work="$(mktemp -d)"
container="lp-restore-check-$$"
cleanup() {
    docker rm -f "$container" >/dev/null 2>&1 || true
    rm -rf "$work"
}
trap cleanup EXIT

started="$(date +%s)"
restic dump --tag db latest "$DUMP_DIR/lottery_passport.dump" >"$work/db.dump"

docker run -d --name "$container" -e POSTGRES_PASSWORD=restore-check \
    -v "$work:/restore:ro" postgres:16-bookworm >/dev/null
for _ in $(seq 1 30); do
    docker exec "$container" pg_isready -U postgres >/dev/null 2>&1 && break
    sleep 1
done
docker exec "$container" createdb -U postgres check
docker exec "$container" pg_restore -U postgres -d check --no-owner --exit-on-error /restore/db.dump

query() { docker exec "$container" psql -U postgres -d check -At -c "$1"; }
users="$(query 'SELECT count(*) FROM users')"
codes="$(query 'SELECT count(*) FROM redemption_codes')"
redeemed="$(query 'SELECT count(*) FROM redemption_codes WHERE redeemed_at IS NOT NULL')"
mismatched="$(query "SELECT count(*) FROM wallets w LEFT JOIN (SELECT user_id, sum(amount) AS total FROM coin_ledger_entries GROUP BY user_id) l USING (user_id) WHERE w.balance <> coalesce(l.total, 0)")"
finished="$(date +%s)"

echo "users=$users codes=$codes redeemed=$redeemed wallet_mismatches=$mismatched"
echo "restore took $((finished - started)) s"
if [ "$mismatched" != "0" ]; then
    echo "wallet balances do not match the ledger: investigate before trusting this backup" >&2
    exit 1
fi
