"""The vectors Arman's tests use must keep matching the server's parser.

If this fails after a change to app/domain/codes.py, the browser-side copy in
docs/frontend/codes.js is out of date too: update both and regenerate the
vectors, or printed codes will be judged differently by the app and the API.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.domain.codes import (
    DEFAULT_FORMAT_ID,
    FORMATS,
    CodeFormatError,
    parse_code,
)

FRONTEND = Path(__file__).parents[2] / "docs/frontend"
VECTORS = json.loads((FRONTEND / "code-test-vectors.json").read_text(encoding="utf-8"))
FORMATS_JSON = json.loads((FRONTEND / "code-formats.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("vector", VECTORS, ids=[v["note"] for v in VECTORS])
def test_frontend_vectors_match_the_server_parser(vector: dict[str, object]) -> None:
    raw = str(vector["input"])
    if vector["ok"]:
        parsed = parse_code(raw)
        assert parsed.canonical == vector["canonical"]
        assert parsed.format_id == vector["format_id"]
    else:
        with pytest.raises(CodeFormatError) as raised:
            parse_code(raw)
        assert raised.value.problem.value == vector["problem"]


def test_every_registered_format_has_valid_vectors() -> None:
    covered = {v["format_id"] for v in VECTORS if v["ok"]}
    assert covered == set(FORMATS)


def test_frontend_format_registry_matches_the_server() -> None:
    assert FORMATS_JSON["default_format_id"] == DEFAULT_FORMAT_ID
    assert set(FORMATS_JSON["formats"]) == set(FORMATS)
    for format_id, code_format in FORMATS.items():
        published = dict(FORMATS_JSON["formats"][format_id])
        assert published.pop("fingerprint") == code_format.fingerprint()
        assert published.pop("entropy_bits") == pytest.approx(code_format.entropy_bits)
        assert published == code_format.spec()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_browser_validator_passes_the_vectors() -> None:
    result = subprocess.run(
        ["node", str(FRONTEND / "codes.test.mjs")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
