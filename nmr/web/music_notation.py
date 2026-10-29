"""Exact engraving plans in quarter-note beats, shared with tune playback."""

from fractions import Fraction
from typing import Literal

from pydantic import BaseModel, Field

from ..types.tune import Tune


class TimeSignature(BaseModel, frozen=True):
    top: int = Field(default=4, gt=0)
    bottom: Literal[1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64] = 4


def score_plan(
    tune: Tune,
    root: int,
    position: Literal["start", "middle", "end"],
    meter: TimeSignature,
) -> dict[str, object]:
    """Engrave playback events one octave higher without changing their timing.

    Preview limits bound the number of SVG elements, not the accepted meter.
    Unusually tiny durations use an explicit tuplet rather than rounding.
    """
    tune.playback(root=root, bpm=180, position=position)
    events = tune.events(root=root, position=position)
    measures: list[list[dict[str, object]]] = [[]]
    bar = Fraction(4 * meter.top, meter.bottom)
    cursor = Fraction(0)
    end = Fraction(0)
    count = 0
    for attack, event in enumerate(events):
        onset = Fraction(str(event["onset"]))
        spans = [
            (onset - end, None),
            (Fraction(str(event["duration"])), event["pitch"]),
        ]
        for duration, pitch in spans:
            continuation = False
            while duration:
                if cursor == bar:
                    measures.append([])
                    cursor = Fraction(0)
                if len(measures) > 512 or count >= 4096:
                    raise ValueError(
                        "This score exceeds the notation preview limit "
                        "(512 bars or 4096 symbols)."
                    )
                remaining = min(duration, bar - cursor)
                ratio = [3, 2] if remaining.denominator % 3 == 0 else [1, 1]
                written = remaining * Fraction(*ratio)
                candidates = [i for i in GLYPHS if i[0] <= written]
                if candidates:
                    length, glyph, dots = max(candidates)
                    actual = length / Fraction(*ratio)
                else:
                    glyph, dots = "128", 0
                    actual = remaining
                    multiplier = Fraction(1, 32) / actual
                    ratio = [multiplier.numerator, multiplier.denominator]
                    if max(ratio) > 1024:
                        raise ValueError(
                            "This score needs a tuplet ratio too large "
                            "for the notation preview."
                        )
                measures[-1].append(
                    {
                        "pitch": int(pitch) + 12 if pitch is not None else None,
                        "duration": str(actual),
                        "glyph": glyph,
                        "dots": dots,
                        "ratio": ratio,
                        "attack": attack if pitch is not None else None,
                        "tie": continuation,
                    }
                )
                continuation = pitch is not None
                duration -= actual
                cursor += actual
                count += 1
        end = onset + Fraction(str(event["duration"]))
    return {
        "top": str(meter.top),
        "bottom": meter.bottom,
        "clef": "treble",
        "measures": measures,
    }


GLYPHS = [
    (Fraction(4, 2**k) * Fraction(2 ** (d + 1) - 1, 2**d), str(2**k), d)
    for k in range(8)
    for d in range(3)
]
