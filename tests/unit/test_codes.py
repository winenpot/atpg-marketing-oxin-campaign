import pytest

from app.domain.codes import (
    ALPHABET,
    BODY_LENGTH,
    CANONICAL_LENGTH,
    CodeFormatError,
    CodeProblem,
    check_is_valid,
    compute_check_value,
    format_printed,
    generate_code,
    normalize_input,
    parse_code,
)
from app.domain.passports import CityCode

# A fixed, valid Tokyo code used across tests (body chosen by hand).
TOKYO_BODY = "7KQ2M9XH4R"
TOKYO_CODE = (
    f"TO{TOKYO_BODY}{ALPHABET[compute_check_value(CityCode.TOKYO, TOKYO_BODY)]}"
)


def test_generated_codes_have_the_v2_shape_and_parse_back() -> None:
    for city in CityCode:
        code = generate_code(city)

        assert len(code) == CANONICAL_LENGTH
        assert code.startswith(city.value)
        assert all(character in ALPHABET for character in code[2:])
        assert parse_code(code).canonical == code
        assert parse_code(code).city is city


def test_generated_codes_do_not_repeat_in_a_large_sample() -> None:
    sample = {generate_code(CityCode.PARIS) for _ in range(20_000)}

    assert len(sample) == 20_000


def test_printed_form_groups_characters_and_parses_back() -> None:
    printed = format_printed(TOKYO_CODE)

    assert printed == f"TO-{TOKYO_CODE[2:6]}-{TOKYO_CODE[6:10]}-{TOKYO_CODE[10:]}"
    assert parse_code(printed).canonical == TOKYO_CODE


@pytest.mark.parametrize(
    "typed",
    [
        TOKYO_CODE.lower(),
        f"  {format_printed(TOKYO_CODE)}  ",
        TOKYO_CODE.replace("TO", "T0", 1),  # zero typed for the O in the prefix
        " ".join(TOKYO_CODE),
        format_printed(TOKYO_CODE).replace("-", "–"),  # en dash from autocorrect
        f"‌{TOKYO_CODE}‏",  # ZWNJ and RLM pasted from a Persian chat
    ],
)
def test_parse_tolerates_how_people_actually_type(typed: str) -> None:
    assert parse_code(typed).canonical == TOKYO_CODE


def test_persian_and_arabic_digits_are_folded_to_ascii() -> None:
    persian = TOKYO_CODE.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    arabic = TOKYO_CODE.translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))

    assert parse_code(persian).canonical == TOKYO_CODE
    assert parse_code(arabic).canonical == TOKYO_CODE


def test_letters_crockford_leaves_out_are_read_as_digits() -> None:
    body = "0110000000"
    code = f"PR{body}{ALPHABET[compute_check_value(CityCode.PARIS, body)]}"
    typed = "PR" + "OIL" + code[5:]  # O->0, I->1, L->1

    assert parse_code(typed).canonical == code


@pytest.mark.parametrize(
    "typed",
    [
        "",
        "TO123",
        TOKYO_CODE + "X",
        "XX" + TOKYO_CODE[2:],  # unknown city
        TOKYO_CODE[:5] + "U" + TOKYO_CODE[6:],  # U is not in the alphabet
        TOKYO_CODE[:5] + "@" + TOKYO_CODE[6:],
        "TO7KQ2M9XH4R6١٢",  # too long after digit folding
    ],
)
def test_malformed_input_is_rejected_as_malformed(typed: str) -> None:
    with pytest.raises(CodeFormatError) as raised:
        parse_code(typed)

    assert raised.value.problem is CodeProblem.MALFORMED


def test_every_single_character_typo_is_reported_as_mistyped() -> None:
    tail = TOKYO_CODE[2:]
    for position in range(len(tail)):
        for character in ALPHABET:
            if character == tail[position]:
                continue
            typo = f"TO{tail[:position]}{character}{tail[position + 1 :]}"
            with pytest.raises(CodeFormatError) as raised:
                parse_code(typo)
            assert raised.value.problem is CodeProblem.MISTYPED


def test_a_code_typed_with_the_wrong_city_prefix_fails_the_check() -> None:
    for city in CityCode:
        if city is CityCode.TOKYO:
            continue
        with pytest.raises(CodeFormatError):
            parse_code(city.value + TOKYO_CODE[2:])


def test_adjacent_swaps_are_caught_except_zero_and_z() -> None:
    # Luhn mod 32 misses exactly one adjacent transposition: values 0 and 31.
    tail = TOKYO_CODE[2:]
    for position in range(len(tail) - 1):
        a, b = tail[position], tail[position + 1]
        if a == b or {a, b} == {"0", "Z"}:
            continue
        swapped = tail[:position] + b + a + tail[position + 2 :]
        assert not check_is_valid(
            CityCode.TOKYO, swapped[:BODY_LENGTH], swapped[BODY_LENGTH:]
        )


def test_normalize_input_never_raises_on_garbage() -> None:
    assert normalize_input("\x00‮💥 to-1") == "\x00💥TO1"
