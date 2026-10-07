"""The format registry: adding, validating and selecting code formats."""

from collections.abc import Iterator

import pytest

from app.domain.codes import (
    V2_B10,
    CodeFormat,
    CodeFormatError,
    CodeProblem,
    FormatRegistryError,
    compute_check_value,
    format_printed,
    generate_code,
    get_format,
    parse_code,
    register_format,
    unregister_format,
    verify_frozen_formats,
)
from app.domain.passports import CityCode


@pytest.fixture
def narrow_format() -> Iterator[CodeFormat]:
    """A short, binary-alphabet format registered only for this test module."""
    fmt = CodeFormat(format_id="test-b4", body_length=4, grouping=(2, 2, 1))
    register_format(fmt)
    yield fmt
    unregister_format(fmt.format_id)


def test_default_format_is_v2_b10() -> None:
    assert get_format() is V2_B10
    assert get_format("v2-b10") is V2_B10


def test_unknown_format_raises() -> None:
    with pytest.raises(FormatRegistryError):
        get_format("does-not-exist")


def test_registering_the_same_format_twice_is_a_noop(narrow_format: CodeFormat) -> None:
    assert register_format(narrow_format) is narrow_format


def test_registering_a_different_format_with_the_same_id_fails() -> None:
    register_format(CodeFormat(format_id="dup", body_length=5, grouping=(3, 3)))
    try:
        with pytest.raises(FormatRegistryError):
            register_format(CodeFormat(format_id="dup", body_length=6, grouping=(3, 4)))
    finally:
        unregister_format("dup")


def test_registering_a_format_with_a_colliding_length_fails(
    narrow_format: CodeFormat,
) -> None:
    with pytest.raises(FormatRegistryError):
        register_format(
            CodeFormat(format_id="also-b4", body_length=4, grouping=(2, 2, 1))
        )


def test_default_format_cannot_be_unregistered() -> None:
    with pytest.raises(FormatRegistryError):
        unregister_format("v2-b10")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"format_id": "", "body_length": 4, "grouping": (2, 3)},
        {"format_id": "x", "body_length": 0, "grouping": (1,)},
        {"format_id": "x", "body_length": 4, "grouping": (2, 2)},  # sums to 4, need 5
        {"format_id": "x", "body_length": 4, "grouping": (2, 2, 1), "alphabet": "AA"},
        {"format_id": "x", "body_length": 4, "grouping": (2, 2, 1), "alphabet": "ab"},
        {
            "format_id": "x",
            "body_length": 4,
            "grouping": (2, 2, 1),
            "aliases": {"0": "1"},  # "0" is already in the default alphabet
        },
        {"format_id": "x", "body_length": 4, "grouping": (2, 2, 1), "alphabet": "01"},
    ],
)
def test_invalid_format_specs_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(FormatRegistryError):
        CodeFormat(**kwargs)  # type: ignore[arg-type]


def test_generate_and_parse_round_trip_on_a_registered_format(
    narrow_format: CodeFormat,
) -> None:
    for city in CityCode:
        code = generate_code(city, narrow_format)
        parsed = parse_code(code)

        assert parsed.city is city
        assert parsed.format_id == narrow_format.format_id
        assert len(code) == narrow_format.canonical_length


def test_printed_grouping_follows_the_format(narrow_format: CodeFormat) -> None:
    code = generate_code(CityCode.TOKYO, narrow_format)

    printed = format_printed(code, narrow_format)

    body = code[2:]
    assert printed == f"TO-{body[:2]}-{body[2:4]}-{body[4:]}"
    assert parse_code(printed).canonical == code


def test_two_formats_of_different_lengths_both_parse(narrow_format: CodeFormat) -> None:
    short_code = generate_code(CityCode.PARIS, narrow_format)
    long_code = generate_code(CityCode.PARIS, V2_B10)

    assert parse_code(short_code).format_id == narrow_format.format_id
    assert parse_code(long_code).format_id == V2_B10.format_id


def test_fingerprint_is_stable_and_changes_with_the_spec() -> None:
    same_shape = CodeFormat(format_id="v2-b10", body_length=10, grouping=(4, 4, 3))
    different = CodeFormat(format_id="v2-b10-x", body_length=10, grouping=(4, 4, 3))

    assert V2_B10.fingerprint() == same_shape.fingerprint()
    assert V2_B10.fingerprint() != different.fingerprint()


def test_entropy_bits_scales_with_body_length() -> None:
    narrow = CodeFormat(format_id="entropy-b2", body_length=2, grouping=(2, 1))

    assert narrow.entropy_bits == pytest.approx(2 * 5.0)  # log2(32) == 5
    assert V2_B10.entropy_bits == pytest.approx(10 * 5.0)


def test_check_character_still_catches_typos_on_a_small_alphabet(
    narrow_format: CodeFormat,
) -> None:
    code = generate_code(CityCode.BERLIN, narrow_format)
    body = code[2:-1]
    next_check = compute_check_value(CityCode.BERLIN, body, narrow_format) + 1
    wrong_check_value = next_check % narrow_format.base
    tampered = code[:-1] + narrow_format.alphabet[wrong_check_value]

    with pytest.raises(CodeFormatError) as raised:
        parse_code(tampered)
    assert raised.value.problem is CodeProblem.MISTYPED


def test_verify_frozen_formats_accepts_a_matching_fingerprint() -> None:
    verify_frozen_formats([(V2_B10.format_id, V2_B10.fingerprint())])


def test_verify_frozen_formats_rejects_a_changed_spec() -> None:
    with pytest.raises(FormatRegistryError, match="has changed since it was frozen"):
        verify_frozen_formats([(V2_B10.format_id, "0" * 64)])


def test_verify_frozen_formats_rejects_an_unregistered_format() -> None:
    with pytest.raises(FormatRegistryError):
        verify_frozen_formats([("gone-missing", "0" * 64)])


def test_verify_frozen_formats_accepts_an_empty_list() -> None:
    verify_frozen_formats([])
