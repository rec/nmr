"""Independent enumeration checks the rational counts and the entire ordering."""

from fractions import Fraction

import pytest

from nmr.types.tune import Note, Tune, duration_cost
from nmr.types.tune_count import tune_counts


def durations_through(cost: int) -> list[Fraction]:
    values = []
    for weight in range(cost + 1):
        for h in range(weight // 4 + 1):
            for b in (0, 1):
                a = weight - 4 * h - 3 * b
                if a < 0:
                    continue
                for u in range(2**h, 2 ** (h + 1)):
                    value = Fraction(u, 2**a * 3**b)
                    if value.numerator == u:
                        values.append(value)
    return values


def suffixes(cost: int, durations: list[Fraction]) -> list[list[Note]]:
    if cost == 0:
        return [[]]
    result = []
    steps = [0, *[s for i in range(1, cost + 2) for s in (i, -i)]]
    gaps = [Fraction(0), *durations]
    for step in steps:
        for gap in gaps:
            gap_weight = 1 + duration_cost(gap) if gap else 0
            for duration in durations:
                remaining = (
                    cost
                    - 1
                    - max(0, abs(step) - 2)
                    - gap_weight
                    - duration_cost(duration)
                )
                if remaining >= 0:
                    note = Note(step=step, gap=gap, duration=duration)
                    result.extend([[note, *s] for s in suffixes(remaining, durations)])
    return result


def test_rational_series_matches_every_small_tune_in_order() -> None:
    tables = tune_counts(5)
    index = 0
    for cost in range(1, 6):
        assert tables["starts"][cost] == index
        durations = durations_through(cost - 1)
        for duration in durations:
            rest = cost - 1 - duration_cost(duration)
            for suffix in suffixes(rest, durations):
                tune = Tune(notes=[Note(duration=duration), *suffix])
                assert tune.index() == index
                assert Tune.from_index(index) == tune
                index += 1
        assert tables["starts"][cost + 1] == index


def test_duration_rational_series_matches_independent_group_counts() -> None:
    tables = tune_counts(24)
    durations = durations_through(24)
    for cost in range(25):
        assert tables["duration"][cost] == sum(
            duration_cost(i) == cost for i in durations
        )
        assert tables["duration_starts"][cost] == sum(
            duration_cost(i) < cost for i in durations
        )


def test_more_simple_notes_outrank_fewer_complex_notes() -> None:
    repeated = Tune.from_text("@1 " * 8)
    assert repeated.index() < Tune.from_text("@128").index()
    assert repeated.index() < Tune.from_text("@1 12@1").index()


def test_out_of_limit_tunes_keep_their_indices_in_the_mathematical_order() -> None:
    tables = tune_counts(4096)
    # The first tune at cost 257 consists of 257 repeated one-beat notes.
    with pytest.raises(ValueError, match="256 attacked"):
        Tune.from_index(tables["starts"][257])
    # Last first-duration block at cost 514 starts with duration weight 513.
    index = tables["starts"][514] + tables["after_gap"][513] - tables["duration"][513]
    with pytest.raises(ValueError, match="duration weight"):
        Tune.from_index(index)
