"""Printed product code format (v2): city prefix + Crockford Base32 + check.

Layout of a canonical code (11 characters, no separators)::

    TO 7KQ2M9XH 4
    ^^ ^^^^^^^^ ^
    |  |        +-- check character (Luhn mod 32 over city index + body)
    |  +----------- 8 random Crockford Base32 characters = 40 bits
    +-------------- city prefix, one per SKU (see ``CityCode``)

Printed form groups the characters for humans: ``TO-7KQ-2M9-XH4``.

Why this shape (details in ``docs/CODES.md``):

* 40 random bits make guessing impractical: with 50,000 codes printed for one
  city, about 1 in 22 million random guesses hits a valid code (1 in 2.2
  million if 500,000 are printed). The v1 format (2 letters + 7 digits with
  500,000 codes) gave 1 in 20. Failed-attempt rate limiting is still required;
  see ``docs/SECURITY.md``.
* Crockford Base32 has no I, L, O or U, so the characters people confuse on
  a printed cap are folded together on input (O->0, I/L->1).
* The check character lets the client and server say "you mistyped a
  character" without a database lookup. It is not a secret and adds no
  security; it only improves the experience of someone typing by hand.

Everything in this module is pure and framework-free. Changing the alphabet,
the city indexes or the check algorithm invalidates every code already
printed, so treat them as frozen once a batch has gone to the printer.

Known limit of the check character: Luhn mod N does not detect the adjacent
transposition of the first and last alphabet symbols (``0`` and ``Z``).
Single-character substitutions and a swapped city prefix are always caught.
"""

import secrets
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from app.domain.passports import CityCode

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
BASE = len(ALPHABET)  # 32
BODY_LENGTH = 8
PREFIX_LENGTH = 2
CANONICAL_LENGTH = PREFIX_LENGTH + BODY_LENGTH + 1

_VALUE_OF = {character: index for index, character in enumerate(ALPHABET)}
# Characters people type for the ones Crockford Base32 leaves out.
_BODY_ALIASES = {"O": "0", "I": "1", "L": "1"}

# Frozen: the check character mixes in the city, so these numbers are part of
# every printed code. Never renumber; only append new cities.
CITY_CHECK_INDEX: dict[CityCode, int] = {
    CityCode.PARIS: 1,
    CityCode.BERLIN: 2,
    CityCode.PATTAYA: 3,
    CityCode.MEXICO: 4,
    CityCode.MADRID: 5,
    CityCode.TOKYO: 6,
    CityCode.MOSCOW: 7,
}

_CITY_BY_PREFIX = {city.value: city for city in CityCode}

# Persian (U+06F0..U+06F9) and Arabic-Indic (U+0660..U+0669) digits are not
# folded to ASCII by NFKC, and Iranian keyboards produce them by default.
_DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


class CodeProblem(StrEnum):
    """Why a typed code was rejected before any database lookup."""

    MALFORMED = "malformed"
    MISTYPED = "mistyped"


class CodeFormatError(ValueError):
    """Raised when user input cannot be a valid v2 code."""

    def __init__(self, problem: CodeProblem) -> None:
        super().__init__(problem.value)
        self.problem = problem


@dataclass(frozen=True, slots=True)
class ParsedCode:
    """A syntactically valid code whose check character matches."""

    city: CityCode
    canonical: str

    @property
    def printed(self) -> str:
        """Human-friendly grouping used on packaging, e.g. ``TO-7KQ-2M9-XH4``."""
        return format_printed(self.canonical)


def _luhn_mod_n_sum(values: list[int], start_factor: int) -> int:
    factor = start_factor
    total = 0
    for value in reversed(values):
        addend = factor * value
        addend = addend // BASE + addend % BASE
        total += addend
        factor = 1 if factor == 2 else 2
    return total


def compute_check_value(city: CityCode, body: str) -> int:
    """Return the Luhn mod 32 check value for ``city`` + ``body``.

    The city index is mixed in as a leading symbol so that a typo in the
    prefix (``MO`` instead of ``TO``) is also caught.
    """
    values = [CITY_CHECK_INDEX[city], *(_VALUE_OF[c] for c in body)]
    total = _luhn_mod_n_sum(values, start_factor=2)
    return (BASE - total % BASE) % BASE


def check_is_valid(city: CityCode, body: str, check: str) -> bool:
    """True when ``check`` is the correct check character for the code."""
    values = [
        CITY_CHECK_INDEX[city],
        *(_VALUE_OF[c] for c in body),
        _VALUE_OF[check],
    ]
    return _luhn_mod_n_sum(values, start_factor=1) % BASE == 0


def generate_code(city: CityCode) -> str:
    """Return a new canonical code using the OS CSPRNG."""
    body = "".join(secrets.choice(ALPHABET) for _ in range(BODY_LENGTH))
    check = ALPHABET[compute_check_value(city, body)]
    return f"{city.value}{body}{check}"


def format_printed(canonical: str) -> str:
    """Group a canonical code as ``PP-XXX-XXX-XXX`` for printing."""
    rest = canonical[PREFIX_LENGTH:]
    return f"{canonical[:PREFIX_LENGTH]}-{rest[:3]}-{rest[3:6]}-{rest[6:]}"


def _strip_separators(text: str) -> str:
    kept: list[str] = []
    for character in text:
        category = unicodedata.category(character)
        # Zs: spaces incl. NBSP; Pd: every dash; Cf: ZWNJ, ZWJ, BOM, bidi marks.
        if category in {"Zs", "Pd", "Cf"} or character in "\t\r\n_.":
            continue
        kept.append(character)
    return "".join(kept)


def normalize_input(raw: str) -> str:
    """Fold whatever a person typed or scanned into canonical characters.

    The result is not guaranteed to be valid; use :func:`parse_code`.
    """
    text = unicodedata.normalize("NFKC", raw).translate(_DIGIT_TRANSLATION)
    return _strip_separators(text).upper()


def parse_code(raw: str) -> ParsedCode:
    """Parse user input into a :class:`ParsedCode` or raise ``CodeFormatError``.

    ``MALFORMED`` means the input cannot be a code at all (wrong length,
    unknown city, characters outside the alphabet). ``MISTYPED`` means the
    shape is right but the check character does not match, which almost
    always means one character was misread from the packaging.
    """
    text = normalize_input(raw)
    if len(text) != CANONICAL_LENGTH or not text.isascii():
        raise CodeFormatError(CodeProblem.MALFORMED)

    # "0" in the prefix is a typo for "O" (TO, MO); prefixes are letters only.
    prefix = text[:PREFIX_LENGTH].replace("0", "O")
    city = _CITY_BY_PREFIX.get(prefix)
    if city is None:
        raise CodeFormatError(CodeProblem.MALFORMED)

    tail = "".join(_BODY_ALIASES.get(c, c) for c in text[PREFIX_LENGTH:])
    if any(c not in _VALUE_OF for c in tail):
        raise CodeFormatError(CodeProblem.MALFORMED)

    body, check = tail[:BODY_LENGTH], tail[BODY_LENGTH:]
    if not check_is_valid(city, body, check):
        raise CodeFormatError(CodeProblem.MISTYPED)
    return ParsedCode(city=city, canonical=f"{prefix}{body}{check}")
