from collections import Counter

import pytest

from app.domain.draw import draw_winners, snapshot_digest, uniform_below

ENTRIES = [("u-1", 1), ("u-2", 3), ("u-3", 6), ("u-4", 0)]


def test_same_snapshot_and_seed_give_the_same_winners() -> None:
    first = draw_winners(ENTRIES, b"published-seed", "tokyo-1", 3)
    second = draw_winners(list(reversed(ENTRIES)), b"published-seed", "tokyo-1", 3)

    assert first == second


def test_a_different_seed_or_label_changes_the_result() -> None:
    results = {
        tuple(draw_winners(ENTRIES, seed, label, 3))
        for seed in (b"seed-a", b"seed-b", b"seed-c", b"seed-d")
        for label in ("tokyo-1", "moscow-1")
    }

    assert len(results) > 1


def test_winners_are_distinct_and_zero_entries_never_win() -> None:
    winners = draw_winners(ENTRIES, b"seed", "tokyo-1", 10)

    assert sorted(winners) == ["u-1", "u-2", "u-3"]
    assert "u-4" not in winners


def test_chances_follow_the_number_of_entries() -> None:
    # 3,000 single-winner draws with different seeds: u-3 holds 60% of the entries.
    wins = Counter(
        draw_winners(ENTRIES, f"seed-{n}".encode(), "check", 1)[0] for n in range(3_000)
    )

    assert 0.55 < wins["u-3"] / 3_000 < 0.65
    assert 0.26 < wins["u-2"] / 3_000 < 0.34
    assert 0.07 < wins["u-1"] / 3_000 < 0.13


def test_uniform_below_stays_in_range_and_is_deterministic() -> None:
    values = [uniform_below(7, b"seed", f"label-{n}") for n in range(500)]

    assert all(0 <= value < 7 for value in values)
    assert set(values) == set(range(7))
    assert values == [uniform_below(7, b"seed", f"label-{n}") for n in range(500)]


def test_snapshot_digest_ignores_order_but_not_content() -> None:
    assert snapshot_digest(ENTRIES) == snapshot_digest(list(reversed(ENTRIES)))
    assert snapshot_digest(ENTRIES) != snapshot_digest([*ENTRIES[:-1], ("u-4", 1)])


def test_ambiguous_snapshots_are_rejected() -> None:
    with pytest.raises(ValueError):
        draw_winners([("u-1", 1), ("u-1", 2)], b"seed", "x", 1)
    with pytest.raises(ValueError):
        draw_winners([("u-1", -1)], b"seed", "x", 1)
