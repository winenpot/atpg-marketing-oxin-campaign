"""The vectors Arman's tests use must keep matching the server's parser.

If this fails after a change to app/domain/codes.py, the browser-side copy in
docs/frontend/codes.js is out of date too: update both and regenerate the
vectors, or printed codes will be judged differently by the app and the API.
"""

import json
from pathlib import Path

import pytest

from app.domain.codes import CodeFormatError, parse_code

VECTORS = json.loads(
    (Path(__file__).parents[2] / "docs/frontend/code-test-vectors.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("vector", VECTORS, ids=[v["note"] for v in VECTORS])
def test_frontend_vectors_match_the_server_parser(vector: dict[str, object]) -> None:
    raw = str(vector["input"])
    if vector["ok"]:
        assert parse_code(raw).canonical == vector["canonical"]
    else:
        with pytest.raises(CodeFormatError) as raised:
            parse_code(raw)
        assert raised.value.problem.value == vector["problem"]
