"""Write app.openapi() to docs/openapi.json (committed snapshot).

Usage::

    uv run python -m scripts.export_openapi

A test (tests/unit/test_openapi_parity.py) fails if the committed file drifts
from what the app actually serves, the same pattern as the codes.js/
code-test-vectors.json parity check (CLAUDE.md: keep generated docs in sync
with the code in the same commit).
"""

import json
from pathlib import Path

from app.app import create_app
from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = REPO_ROOT / "docs" / "openapi.json"


def current_schema() -> dict[str, object]:
    # A throwaway Settings: production-only fields (pepper) just need to be
    # present so create_app() doesn't fail; nothing here talks to a database.
    settings = Settings(redemption_code_pepper="x" * 32)  # type: ignore[arg-type]
    application = create_app(settings)
    return application.openapi()


def main() -> None:
    schema = current_schema()
    OPENAPI_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OPENAPI_PATH}")


if __name__ == "__main__":
    main()
