"""Scores preserve the exact events used by audio, regardless of bar layout."""

import json
from fractions import Fraction
from typing import Literal

import pytest
from pydantic import ValidationError

from nmr.nmr import Nmr
from nmr.types.tune import Tune
from nmr.web import bridge
from nmr.web.music_notation import TimeSignature, score_plan


@pytest.mark.parametrize("bottom", [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64])
@pytest.mark.parametrize("position", ["start", "middle", "end"])
def test_scores_preserve_attacks_pitches_rests_and_exact_timing(
    bottom: int, position: Literal["start", "middle", "end"]
) -> None:
    tune = Tune.from_text("@5 2@3/2 r@1/3 -1@2/3 @1/16 4@1/32")
    meter = TimeSignature(top=3, bottom=bottom)
    score = score_plan(tune, 53, position, meter)
    cursor = Fraction(0)
    attacks = []
    for measure in score["measures"]:
        length = Fraction(0)
        for symbol in measure:
            duration = Fraction(symbol["duration"])
            written = Fraction(4, int(symbol["glyph"])) * sum(
                (Fraction(1, 2**i) for i in range(symbol["dots"] + 1)),
                Fraction(0),
            )
            assert written / Fraction(*symbol["ratio"]) == duration
            if symbol["pitch"] is not None:
                if symbol["tie"]:
                    assert attacks[-1]["pitch"] == symbol["pitch"]
                    assert attacks[-1]["onset"] + attacks[-1]["duration"] == cursor
                    attacks[-1]["duration"] += duration
                else:
                    attacks.append(
                        {
                            "pitch": symbol["pitch"],
                            "onset": cursor,
                            "duration": duration,
                        }
                    )
            cursor += duration
            length += duration
        assert length <= Fraction(4 * meter.top, bottom)
    expected = [
        dict(
            pitch=i["pitch"],
            onset=Fraction(i["onset"]),
            duration=Fraction(i["duration"]),
        )
        for i in tune.events(53, position)
    ]
    assert attacks == expected
    playback = tune.playback(53, 180, position)
    for actual, audio in zip(attacks, playback, strict=True):
        assert actual["pitch"] == audio["pitch"]
        assert float(actual["onset"] / 3) == pytest.approx(audio["onset"])
        assert float(actual["duration"] / 3) == pytest.approx(audio["duration"])


def test_meter_defaults_and_validation() -> None:
    assert TimeSignature().model_dump() == {"top": 4, "bottom": 4}
    assert TimeSignature(top=10**100).top == 10**100
    for parameters in [{"top": 0}, {"top": -1}, {"bottom": 5}]:
        with pytest.raises(ValidationError):
            TimeSignature(**parameters)


def test_preview_limits_report_instead_of_rounding() -> None:
    tune = Tune.from_text("@1 r@1/1048576 @1")
    with pytest.raises(ValueError, match="tuplet ratio"):
        score_plan(tune, 53, "middle", TimeSignature())


def test_count_score_matches_the_full_index_tune_played_by_count() -> None:
    engine = Nmr()
    index = engine.truename_index(engine.encode("@1 2@1", "tune", scope="").truename)
    result = json.loads(
        bridge.count(
            json.dumps(
                {
                    "value": str(index),
                    "root": 55,
                    "position": "end",
                    "time_signature": {"top": 7, "bottom": 8},
                }
            )
        )
    )
    assert result["display"]["kind"] == "tune"
    assert result["display"]["score"] == score_plan(
        Tune.from_index(index), 55, "end", TimeSignature(top=7, bottom=8)
    )
