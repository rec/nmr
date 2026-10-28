"""Exact, transposition-independent melodies and rhythms in reference beats."""

from __future__ import annotations

import re
from bisect import bisect_right
from fractions import Fraction
from typing import ClassVar, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from ..type_name import TypeNamer
from . import tune_count
from .integer import signed_index, signed_value


class Note(BaseModel, frozen=True):
    step: int = 0
    duration: Fraction = Fraction(1)
    gap: Fraction = Fraction(0)

    @field_validator("duration", "gap")
    @classmethod
    def validate_rhythm(cls, value: Fraction, info: ValidationInfo) -> Fraction:
        if value == 0 and info.field_name == "gap":
            return value
        duration_parts(value)
        return value


class Tune(BaseModel, TypeNamer, frozen=True):
    notes: list[Note] = Field(min_length=1, max_length=256)
    label: ClassVar[str] = "tune"
    description: ClassVar[str] = "Melody and rhythm: @1 2@1/2 r@1/3 -1@2/3"

    @model_validator(mode="after")
    def validate_phrase(self) -> Tune:
        if self.notes[0].step or self.notes[0].gap:
            raise ValueError("The first note must have zero relative pitch and no gap")
        return self

    @classmethod
    def from_text(cls, value: str) -> Tune:
        if len(value) > MAX_TEXT:
            raise ValueError("Tune work limit: at most 20000 input characters")
        tokens = value.split()
        if not tokens or not tokens[0].startswith("@"):
            raise ValueError("A tune must start with @duration, without an offset")
        notes: list[Note] = []
        gap = Fraction(0)
        for token in tokens:
            match = re.fullmatch(r"(r|-?[0-9]*)@([0-9]+(?:/[0-9]+|\.[0-9]+)?)", token)
            if match is None:
                raise ValueError(f"Expected step@duration or r@duration: {token}")
            step, text = match.groups()
            if len(text) > MAX_WEIGHT:
                raise ValueError("Tune work limit: duration text is too large")
            try:
                duration = Fraction(text)
            except ZeroDivisionError as error:
                raise ValueError("A duration cannot have a zero denominator") from error
            duration_parts(duration)
            if step == "r":
                gap += duration
            else:
                notes.append(Note(step=int(step or "0"), duration=duration, gap=gap))
                gap = Fraction(0)
                if len(notes) > MAX_NOTES:
                    raise ValueError("Tune work limit: at most 256 attacked notes")
        # Trailing rests are outside the phrase, just as leading performance silence is.
        return cls(notes=notes)

    @classmethod
    def from_pitches(
        cls, pitches: list[int], durations: list[Fraction], gaps: list[Fraction]
    ) -> Tune:
        """Normalize absolute pitches and leading silence, retaining every attack."""
        if not pitches or len(pitches) != len(durations) or len(pitches) != len(gaps):
            raise ValueError(
                "Expected equally sized, nonempty pitch/duration/gap lists"
            )
        return cls(
            notes=[
                Note(
                    step=p - pitches[i - 1] if i else 0,
                    duration=d,
                    gap=g if i else Fraction(0),
                )
                for i, (p, d, g) in enumerate(
                    zip(pitches, durations, gaps, strict=True)
                )
            ]
        )

    def text(self) -> str:
        tokens = []
        for note in self.notes:
            if note.gap:
                tokens.append(f"r@{note.gap}")
            tokens.append(f"{note.step or ''}@{note.duration}")
        return " ".join(tokens)

    def index(self) -> int:
        cost = len(self.notes) * tune_count.ATTACK_COST
        cost += sum(duration_cost(i.duration) for i in self.notes)
        cost += sum(
            tune_count.pitch_cost(i.step) + gap_cost(i.gap) for i in self.notes[1:]
        )
        if cost > MAX_COST:
            raise ValueError("Tune work limit: total complexity exceeds 4096")
        tables = tune_count.tune_counts(MAX_COST)
        remaining = cost - tune_count.ATTACK_COST
        rank, remaining = rank_duration(
            self.notes[0].duration, remaining, tables["suffix"]
        )
        for note in self.notes[1:]:
            remaining -= tune_count.ATTACK_COST
            # Pitch order is 0,+1,-1,+2,-2,... within the remaining budget.
            for i in range(signed_index(note.step)):
                weight = tune_count.pitch_cost(signed_value(i))
                rank += tables["after_step"][remaining - weight]
            remaining -= tune_count.pitch_cost(note.step)
            if note.gap:
                rank += tables["after_gap"][remaining]
                addition, remaining = rank_duration(
                    note.gap, remaining - tune_count.REST_COST, tables["after_gap"]
                )
                rank += addition
            addition, remaining = rank_duration(
                note.duration, remaining, tables["suffix"]
            )
            rank += addition
        assert remaining == 0
        index = tables["starts"][cost] + rank
        check_index(index)
        return index

    def tie(self, index: int) -> Tune:
        """Replace two contiguous same-pitch notes with one sustained note."""
        if not 1 <= index < len(self.notes):
            raise ValueError("Choose a later note to tie to its predecessor")
        note, previous = self.notes[index], self.notes[index - 1]
        if note.step or note.gap:
            raise ValueError("Tied notes must share a pitch with no intervening gap")
        sustained = Note(
            step=previous.step,
            duration=previous.duration + note.duration,
            gap=previous.gap,
        )
        return Tune(
            notes=[*self.notes[: index - 1], sustained, *self.notes[index + 1 :]]
        )

    @classmethod
    def from_index(cls, index: int) -> Tune:
        check_index(index)
        tables = tune_count.tune_counts(MAX_COST)
        if index >= tables["starts"][-1]:
            raise ValueError("Tune work limit: total complexity exceeds 4096")
        cost = bisect_right(tables["starts"], index) - 1
        rank = index - tables["starts"][cost]
        duration, rank, remaining = unrank_duration(
            rank, cost - tune_count.ATTACK_COST, tables["suffix"]
        )
        notes = [Note(duration=duration)]
        while remaining:
            if len(notes) >= MAX_NOTES:
                raise ValueError("Tune work limit: at most 256 attacked notes")
            remaining -= tune_count.ATTACK_COST
            for step_index in range(
                2 * (tune_count.FREE_STEPS + remaining // tune_count.STEP_COST) + 1
            ):
                step = signed_value(step_index)
                weight = tune_count.pitch_cost(step)
                count = (
                    tables["after_step"][remaining - weight]
                    if weight <= remaining
                    else 0
                )
                if rank < count:
                    remaining -= weight
                    break
                rank -= count
            else:
                raise AssertionError("Pitch completion count is inconsistent")
            count = tables["after_gap"][remaining]
            gap = Fraction(0)
            if rank >= count:
                gap, rank, remaining = unrank_duration(
                    rank - count, remaining - tune_count.REST_COST, tables["after_gap"]
                )
            duration, rank, remaining = unrank_duration(
                rank, remaining, tables["suffix"]
            )
            notes.append(Note(step=step, gap=gap, duration=duration))
        assert rank == 0
        return cls(notes=notes)

    def events(
        self, root: int = 60, position: Literal["start", "middle", "end"] = "middle"
    ) -> list[dict[str, int | str]]:
        """Exact onsets, durations and positioned MIDI pitches, before device limits."""
        pitches = []
        pitch = 0
        for note in self.notes:
            pitch += note.step
            pitches.append(pitch)
        if position == "start":
            center = pitches[0]
        elif position == "end":
            center = pitches[-1]
        elif position == "middle":
            total = sum(pitches)
            center = (2 * abs(total) + len(pitches)) // (2 * len(pitches))
            if total < 0:
                center = -center
        else:
            raise ValueError("Position must be start, middle, or end")
        onset = Fraction(0)
        events = []
        for note, pitch in zip(self.notes, pitches, strict=True):
            onset += note.gap
            events.append(
                {
                    "pitch": root + pitch - center,
                    "onset": str(onset),
                    "duration": str(note.duration),
                }
            )
            onset += note.duration
        return events

    def playback(
        self,
        root: int = 60,
        bpm: int = 120,
        position: Literal["start", "middle", "end"] = "middle",
    ) -> list[dict[str, float | int]]:
        """Convert exact events only after checking the browser's preview limits."""
        if not 20 <= bpm <= 400:
            raise ValueError("Playback tempo must be between 20 and 400 BPM")
        events = self.events(root, position)
        result = []
        for event in events:
            pitch = int(event["pitch"])
            onset = Fraction(str(event["onset"])) * 60 / bpm
            duration = Fraction(str(event["duration"])) * 60 / bpm
            if not 0 <= pitch <= 127:
                raise ValueError(
                    "Playback requires all positioned pitches in MIDI range 0..127"
                )
            if onset + duration > 120 or duration < Fraction(1, 100):
                raise ValueError(
                    "Playback limit: at most 120 seconds, "
                    "with notes at least 0.01 seconds long"
                )
            result.append(
                {"pitch": pitch, "onset": float(onset), "duration": float(duration)}
            )
        return result

    @staticmethod
    def str_to_index(value: str) -> int:
        return Tune.from_text(value).index()

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return Tune.from_index(index).text()


def check_index(index: int) -> None:
    if index < 0:
        raise ValueError("Expected a nonnegative tune index")
    if index.bit_length() > MAX_INDEX_BITS:
        raise ValueError("Tune work limit: index exceeds 4096 bits")


def duration_cost(value: Fraction) -> int:
    _, a, b, h = duration_parts(value)
    return (
        tune_count.NUMERATOR_COST * h
        + tune_count.BINARY_COST * a
        + tune_count.THIRD_COST * b
    )


def gap_cost(value: Fraction) -> int:
    return tune_count.REST_COST + duration_cost(value) if value else 0


def rank_duration(
    value: Fraction, budget: int, completions: list[int]
) -> tuple[int, int]:
    tables = tune_count.tune_counts(MAX_COST)
    weight = duration_cost(value)
    rank = sum(tables["duration"][i] * completions[budget - i] for i in range(weight))
    ordinal = duration_index(value) - tables["duration_starts"][weight]
    remaining = budget - weight
    return rank + ordinal * completions[remaining], remaining


def unrank_duration(
    rank: int, budget: int, completions: list[int]
) -> tuple[Fraction, int, int]:
    tables = tune_count.tune_counts(MAX_COST)
    for weight in range(budget + 1):
        suffixes = completions[budget - weight]
        count = tables["duration"][weight] * suffixes
        if rank >= count:
            rank -= count
            continue
        ordinal, rank = divmod(rank, suffixes)
        if weight > MAX_WEIGHT:
            raise ValueError("Tune work limit: duration weight exceeds 512")
        return (
            duration_value(tables["duration_starts"][weight] + ordinal),
            rank,
            budget - weight,
        )
    raise AssertionError("Duration completion count is inconsistent")


def duration_parts(value: Fraction) -> tuple[int, int, int, int]:
    if value <= 0:
        raise ValueError("Durations must be positive")
    denominator = value.denominator
    a = (denominator & -denominator).bit_length() - 1
    denominator >>= a
    b = int(denominator % 3 == 0)
    if denominator != 3**b:
        raise ValueError(
            "Reduced denominators allow only powers of two "
            "and at most one factor of three"
        )
    u = value.numerator
    h = u.bit_length() - 1
    if (
        tune_count.NUMERATOR_COST * h
        + tune_count.BINARY_COST * a
        + tune_count.THIRD_COST * b
        > MAX_WEIGHT
    ):
        raise ValueError("Tune work limit: duration weight exceeds 512")
    return u, a, b, h


def group_count(lower: int, upper: int, a: int, b: int) -> int:
    count = upper - lower + 1
    if a:
        count -= upper // 2 - (lower - 1) // 2
    if b:
        count -= upper // 3 - (lower - 1) // 3
    if a and b:
        count += upper // 6 - (lower - 1) // 6
    return count


def duration_index(value: Fraction) -> int:
    u, a, b, h = duration_parts(value)
    weight = duration_cost(value)
    index = tune_count.tune_counts(MAX_COST)["duration_starts"][weight]
    for i in range(h + 1):
        for j in (0, 1):
            exponent, remainder = divmod(
                weight - tune_count.NUMERATOR_COST * i - tune_count.THIRD_COST * j,
                tune_count.BINARY_COST,
            )
            if exponent < 0 or remainder:
                continue
            if (i, j) == (h, b):
                return index + group_count(1 << h, u - 1, a, b)
            index += group_count(1 << i, (1 << (i + 1)) - 1, exponent, j)
    raise AssertionError("Reduced duration group is missing")


def duration_value(index: int) -> Fraction:
    if index < 0:
        raise ValueError("Expected a nonnegative duration index")
    layers = tune_count.tune_counts(MAX_COST)["duration_starts"]
    if index >= layers[MAX_WEIGHT + 1]:
        raise ValueError("Tune work limit: duration weight exceeds 512")
    lower, upper = (
        0,
        min(MAX_WEIGHT + 1, tune_count.NUMERATOR_COST * (index + 1).bit_length() + 1),
    )
    while upper - lower > 1:
        middle = (lower + upper) // 2
        if layers[middle] <= index:
            lower = middle
        else:
            upper = middle
    weight = lower
    index -= layers[weight]
    for h in range(weight // tune_count.NUMERATOR_COST + 1):
        for b in (0, 1):
            a, remainder = divmod(
                weight - tune_count.NUMERATOR_COST * h - tune_count.THIRD_COST * b,
                tune_count.BINARY_COST,
            )
            if a < 0 or remainder:
                continue
            start, end = 1 << h, (1 << (h + 1)) - 1
            count = group_count(start, end, a, b)
            if index >= count:
                index -= count
                continue
            lower, upper = start - 1, end
            while upper - lower > 1:
                middle = (lower + upper) // 2
                if group_count(start, middle, a, b) <= index:
                    lower = middle
                else:
                    upper = middle
            return Fraction(upper, (1 << a) * 3**b)
    raise AssertionError("Duration index has no group")


MAX_NOTES = 256
MAX_WEIGHT = 512
MAX_INDEX_BITS = 4096
MAX_TEXT = 20000
MAX_COST = 4096
