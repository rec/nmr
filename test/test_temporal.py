import io
import json
from datetime import datetime, timedelta

import pytest

from nmr._main import Main
from nmr.nmr import Nmr
from nmr.registry import ROOT
from nmr.types import temporal
from nmr.web import bridge


@pytest.mark.parametrize(
    "codec,value,index",
    [
        (temporal.Date, "2027-01-01", 0),
        (temporal.Date, "2027-01-02", 1),
        (temporal.Date, "2027-01-03", 2),
        (temporal.Date, "2026-12-31", 3),
        (temporal.Date, "2027-01-04", 4),
        (temporal.Date, "2027-01-05", 5),
        (temporal.Date, "2026-12-30", 6),
        (temporal.Date, "2027-01-06", 7),
        (temporal.Date, "2027-01-07", 8),
        (temporal.Date, "2026-12-29", 9),
        (temporal.DateTime, "2027-01-01T00:00:00", 0),
        (temporal.DateTime, "2027-01-01T00:00:01", 1),
        (temporal.DateTime, "2027-01-01T00:00:02", 2),
        (temporal.DateTime, "2026-12-31T23:59:59", 3),
        (temporal.DateTime, "2027-01-01T00:00:03", 4),
        (temporal.DateTime, "2027-01-01T00:00:04", 5),
        (temporal.DateTime, "2026-12-31T23:59:58", 6),
        (temporal.DateTime, "2027-01-01T00:00:05", 7),
        (temporal.DateTime, "2027-01-01T00:00:06", 8),
        (temporal.DateTime, "2026-12-31T23:59:57", 9),
        (temporal.DateTime, "2027-01-02T00:00:00", 3 * temporal.DAY // 2 - 1),
        (temporal.DateTime, "2026-12-31T00:00:00", 3 * temporal.DAY),
    ],
)
def test_zoot_and_nearby_values_use_factor_three_order(
    codec: type[temporal.Date] | type[temporal.DateTime], value: str, index: int
) -> None:
    assert codec.str_to_index(value) == index
    assert codec.index_to_str(index) == value


@pytest.mark.parametrize("codec", [temporal.Date, temporal.DateTime])
def test_centered_calendar_indices_round_trip_without_gaps(
    codec: type[temporal.Date] | type[temporal.DateTime],
) -> None:
    for i in range(384):
        assert codec.str_to_index(codec.index_to_str(i)) == i


@pytest.mark.parametrize("start", ["2026-12-31T12:00:00", "2027-01-01T12:00:00"])
@pytest.mark.parametrize("interval", [1, 5, 15])
def test_clock_offsets_visit_every_registered_type(start: str, interval: int) -> None:
    start_time = datetime.fromisoformat(start)
    visited = {
        ROOT.resolve(
            temporal.DateTime.str_to_index(
                (start_time + timedelta(seconds=i * interval)).isoformat()
            ),
            browse=True,
        )[0].label
        for i in range(128)
    }
    assert visited == {c.label for _, _, c in ROOT.leaves()}


@pytest.mark.parametrize("center_on_zoot", [True, False])
@pytest.mark.parametrize(
    "kind,value",
    [
        ("date", "0001-01-01"),
        ("date", "9999-12-31"),
        ("date", "2000-02-29"),
        ("datetime", "0001-01-01T00:00:00"),
        ("datetime", "9999-12-31T23:59:59"),
        ("datetime", "2000-02-29T23:59:59"),
    ],
)
def test_calendar_extremes_and_leap_days_round_trip_in_both_modes(
    center_on_zoot: bool, kind: str, value: str
) -> None:
    engine = Nmr(center_on_zoot=center_on_zoot)
    for scope in [None, ""]:
        result = engine.encode(value, kind, scope)
        assert engine.decode(result.truename).value == value
        assert engine.decode(result.truename, browse=True).canonical


@pytest.mark.parametrize(
    "codec,scale", [(temporal.Date, 1), (temporal.DateTime, temporal.DAY)]
)
def test_centered_calendar_overflow_is_rejected_or_browsed_into_range(
    codec: type[temporal.Date] | type[temporal.DateTime], scale: int
) -> None:
    before = 3 * (temporal.ZOOT * scale + 1)
    after_offset = (temporal.DAYS - temporal.ZOOT) * scale
    after = after_offset + (after_offset - 1) // 2
    first = "0001-01-01" + ("T00:00:00" if scale > 1 else "")
    last = "9999-12-31" + ("T23:59:59" if scale > 1 else "")
    for index in [before, after, -1]:
        with pytest.raises(ValueError):
            codec.index_to_str(index)
    assert codec.index_to_str(before, browse=True) == last
    assert codec.index_to_str(after, browse=True) == first
    with pytest.raises(ValueError):
        codec.index_to_str(-1, browse=True)


def test_centering_is_per_engine_and_leaves_other_types_unchanged() -> None:
    centered = Nmr()
    uncentered = Nmr(center_on_zoot=False)
    for kind, epoch, first in [
        ("date", "2027-01-01", "0001-01-01"),
        ("datetime", "2027-01-01T00:00:00", "0001-01-01T00:00:00"),
    ]:
        assert centered.encode(epoch, kind).truename == kind + ":the"
        assert uncentered.encode(first, kind).truename == kind + ":the"
        assert centered.decode(kind + ":the").value == epoch
        assert uncentered.decode(kind + ":the").value == first
    for kind, value in [("int", "42"), ("time", "23:59:59")]:
        assert centered.encode(value, kind) == uncentered.encode(value, kind)


def test_cli_can_disable_zoot_centering() -> None:
    output, errors = io.StringIO(), io.StringIO()
    status = Main(
        operation="encode", type_name="date", value="0001-01-01", center_on_zoot=False
    ).run(io.StringIO(), output, errors)
    assert status == 0
    assert output.getvalue().strip() == "date:the"


@pytest.mark.parametrize("center_on_zoot", [True, False])
def test_browser_configuration_selects_the_date_enumeration(
    monkeypatch: pytest.MonkeyPatch, center_on_zoot: bool
) -> None:
    monkeypatch.setattr(bridge, "_engine", Nmr())
    bridge.configure(json.dumps({"center_on_zoot": center_on_zoot}))
    result = json.loads(bridge.convert('{"operation":"decode","value":"datetime:the"}'))
    assert result["value"] == (
        "2027-01-01T00:00:00" if center_on_zoot else "0001-01-01T00:00:00"
    )
