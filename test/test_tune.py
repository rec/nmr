from fractions import Fraction

import pytest

from nmr.nmr import Nmr
from nmr.types.tune import Note, Tune, duration_index, duration_value


@pytest.mark.parametrize(
    "index,text",
    list(
        enumerate(
            [
                "1",
                "1/2",
                "1/4",
                "1/8",
                "1/3",
                "1/16",
                "1/6",
                "2",
                "3",
                "1/32",
                "1/12",
                "3/2",
            ]
        )
    ),
)
def test_duration_order(index: int, text: str) -> None:
    assert duration_index(Fraction(text)) == index
    assert duration_value(index) == Fraction(text)


def test_duration_layers_match_independent_reduced_enumeration() -> None:
    values = []
    for weight in range(25):
        for h in range(weight // 4 + 1):
            for b in (0, 1):
                a = weight - 4 * h - 3 * b
                if a < 0:
                    continue
                for u in range(2**h, 2 ** (h + 1)):
                    value = Fraction(u, 2**a * 3**b)
                    if value.numerator == u:
                        values.append(value)
    assert len(set(values)) == len(values)
    for index, value in enumerate(values):
        assert duration_index(value) == index
        assert duration_value(index) == value
    for index in [2**80, 2**120 + 17]:
        assert duration_index(duration_value(index)) == index
    for value in [Fraction(1, 2**512), Fraction(2**128)]:
        assert duration_value(duration_index(value)) == value


@pytest.mark.parametrize(
    "text",
    [
        "@0",
        "@-1",
        "@1/0",
        "@1/5",
        "@1/9",
        "@1/18",
        "",
        "r@1",
        "0@1",
        "2@1",
        "@1 +2@1",
        "@1 nonsense",
    ],
)
def test_invalid_phrases_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        Tune.from_text(text)


def test_normalization_preserves_attacks_and_merges_rests() -> None:
    tune = Tune.from_text(" @3/9 0@2/4 r@1/3 r@1/6 -2@1 r@4 ")
    assert tune.text() == "@1/3 @1/2 r@1/2 -2@1"
    assert Tune.from_text("@1 @1").tie(1).text() == "@2"
    assert Tune.from_text("@1 @1").index() != Tune.from_text("@2").index()
    for text in ["@1 1@1", "@1 r@1 @1"]:
        with pytest.raises(ValueError, match="Tied"):
            Tune.from_text(text).tie(1)
    with pytest.raises(ValueError, match="later"):
        tune.tie(0)


@pytest.mark.parametrize(
    "index,text",
    [
        (0, "@1"),
        (1, "@1 @1"),
        (2, "@1/2"),
        (3, "@1 @1 @1"),
        (4, "@1 @1/2"),
        (5, "@1 r@1 @1"),
        (6, "@1 1@1"),
        (7, "@1 -1@1"),
        (8, "@1/2 @1"),
        (9, "@1/4"),
    ],
)
def test_tune_index_fixtures(index: int, text: str) -> None:
    assert Tune.from_index(index).text() == text
    assert Tune.from_text(text).index() == index


def test_arbitrary_indices_have_exact_inverses() -> None:
    for index in [*range(500), 2**120, 2**255 - 1, ((2**1200 + 1) << 15) - 1]:
        tune = Tune.from_index(index)
        assert tune.index() == index
        assert Tune.from_text(tune.text()) == tune


def test_centering_uses_cumulative_pitches_and_exact_events() -> None:
    tune = Tune.from_text("@1 2@1/2 2@1/2 r@1/3 -1@2/3 @1")
    events = tune.events()
    assert [i["pitch"] for i in events] == [58, 60, 62, 61, 61]
    assert [i["onset"] for i in events] == ["0", "1", "3/2", "7/3", "3"]
    assert [i["duration"] for i in events] == ["1", "1/2", "1/2", "2/3", "1"]
    assert [i["pitch"] for i in tune.events(72)] == [70, 72, 74, 73, 73]
    assert (
        Tune.from_pitches(
            [58, 60, 62, 61, 61],
            [i.duration for i in tune.notes],
            [i.gap for i in tune.notes],
        )
        == tune
    )
    for step, pitches in [(1, [59, 60]), (-1, [61, 60])]:
        assert [i["pitch"] for i in Tune.from_text(f"@1 {step}@8").events()] == pitches


@pytest.mark.parametrize("scope", ["", "play", "play:music", "play:music:tune"])
def test_names_round_trip_in_all_scopes_and_vocabularies(scope: str) -> None:
    for engine in [Nmr(), Nmr([f"word{i}" for i in range(32)])]:
        result = engine.encode("@1 2@1/2 r@1/3 -1@2/3", "tune", scope)
        assert engine.decode(result.name) == result
        assert engine.decode(result.name, browse=True) == result


@pytest.mark.parametrize("count", [4, 8, 16])
def test_personal_motif_name_lengths(count: int) -> None:
    # The opening of Twinkle, with a rest and exact dotted/triplet rhythms.
    pitches = [0, 0, 7, 7, 9, 9, 7, 5, 5, 4, 4, 2, 2, 0, 7, 7][:count]
    durations = [
        Fraction(i) for i in ["1", "1/2", "1/2", "3/2", "1/3", "2/3", "1", "2"]
    ]
    tune = Tune.from_pitches(
        pitches,
        (durations * 2)[:count],
        [Fraction(1, 3) if i == 4 else Fraction(0) for i in range(count)],
    )
    result = Nmr().encode(tune.text(), "tune")
    assert Nmr().decode(result.name).value == tune.text()
    words = len(result.name.rsplit(":", 1)[-1].split())
    print(f"{count} notes: {words} payload words; {result.name}")


def test_playback_preserves_events_and_refuses_unrenderable_tunes() -> None:
    tune = Tune.from_text("@1 2@1/2 r@1/3 -1@2/3")
    for root, bpm in [(60, 120), (72, 60)]:
        events = tune.events(root)
        played = tune.playback(root, bpm)
        for exact, audible in zip(events, played, strict=True):
            assert audible["pitch"] == exact["pitch"]
            assert audible["onset"] == float(Fraction(str(exact["onset"])) * 60 / bpm)
            assert audible["duration"] == float(
                Fraction(str(exact["duration"])) * 60 / bpm
            )
    for text in ["@1 200@1", "@1000", "@1/1024"]:
        other = Tune.from_text(text)
        with pytest.raises(ValueError, match="Playback"):
            other.playback()
        assert Tune.from_index(other.index()) == other
    with pytest.raises(ValueError, match="tempo"):
        tune.playback(bpm=0)


def test_work_limits_do_not_repair_the_tune() -> None:
    for index in [-1, 2**4096]:
        with pytest.raises(ValueError):
            Tune.from_index(index)
    for value in [Fraction(1, 2**513), Fraction(2**129)]:
        with pytest.raises(ValueError, match="work limit"):
            duration_index(value)
    with pytest.raises(ValueError, match="work limit"):
        duration_value(2**140)
    with pytest.raises(ValueError):
        Tune(notes=[Note(step=1)])
    with pytest.raises(ValueError):
        Tune.from_pitches([], [], [])
    with pytest.raises(ValueError, match="work limit"):
        Tune.from_text("@1 " * 257)
    with pytest.raises(ValueError, match="work limit"):
        Tune.from_text("@1 " * 7000)
    with pytest.raises(ValueError, match="work limit"):
        Tune.from_text("@" + "1" * 513)
    with pytest.raises(ValueError, match="work limit"):
        Tune(notes=[Note(), Note(step=2**4096)]).index()
    with pytest.raises(ValueError, match="work limit"):
        Tune(notes=[Note(), Note(step=2**2000)]).index()


def test_name_capacity_is_explicit() -> None:
    with pytest.raises(ValueError, match="[Cc]apacity|vocabulary|[Ll]arge|[Ww]ords"):
        Nmr(["one", "two"]).encode("@1 12@1", "tune")
