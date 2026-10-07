#!/usr/bin/env bash
# Deploy a tagged release on this VM.
#
#   sudo deploy/deploy.sh v2026.10.12-1      # a git tag (or commit)
#
# Steps: check out the ref, build the image, start PostgreSQL, run migrations,
# restart the stack, wait until /ready answers. Roll back by deploying the
# previous tag: during the campaign migrations are additive, so older code
# keeps working on the newer schema.
set -euo pipefail

ref="${1:?usage: deploy.sh <git-tag-or-commit>}"
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
compose=(docker compose -f "$repo_dir/deploy/compose.prod.yml")

cd "$repo_dir"
git fetch --tags --quiet origin
git checkout --quiet --detach "$ref"
RELEASE="$(git rev-parse --short HEAD)"
export RELEASE

echo "building $ref ($RELEASE)"
"${compose[@]}" build api

echo "starting postgres"
"${compose[@]}" up -d --wait postgres

echo "running migrations"
"${compose[@]}" run --rm --no-deps api alembic upgrade head

echo "restarting services"
"${compose[@]}" up -d --remove-orphans

for _ in $(seq 1 30); do
    if "${compose[@]}" exec -T api python -c \
        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)" \
        >/dev/null 2>&1; then
        echo "deployed $ref ($RELEASE): ready"
        exit 0
    fi
    sleep 2
done

echo "deployed $ref ($RELEASE) but /ready is failing; check logs:" >&2
echo "  ${compose[*]} logs --tail=100 api" >&2
echo "roll back with: deploy/deploy.sh <previous tag>" >&2
exit 1
