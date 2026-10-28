"""Recognize unlabelled details without guessing ambiguous date formats."""

import json

import pytest

from nmr.nmr import Nmr
from nmr.recognition import describe_input
from nmr.types.tune import Tune
from nmr.web import bridge


@pytest.mark.parametrize("position,anchor", [("start", 0), ("middle", 1), ("end", -1)])
def test_every_browser_preview_respects_the_selected_pitch_position(
    position: str, anchor: int
) -> None:
    text = "@1 2@1 2@1"
    settings = {"root": 53, "bpm": 180, "position": position}
    truename = Nmr().encode(text, "tune").truename
    results = [
        bridge.preview(json.dumps({"value": text, **settings})),
        bridge.preview_truename(json.dumps({"value": truename, **settings})),
        bridge.preview_item(
            json.dumps(
                {"operation": "encode", "type_name": "tune", "value": text, **settings}
            )
        ),
    ]
    for result in results:
        rendered = json.loads(result)
        assert rendered["playback"][anchor]["pitch"] == 53
        assert int(rendered["events"][anchor]["pitch"]) == 53


@pytest.mark.parametrize(
    "value,kind",
    [
        ("42", "int"),
        ("-42", "int"),
        ("9780306406157", "int"),
        ("+1", "phone"),
        ("+44 (0)20 7946 0958", "phone"),
        ("8/5", "frac"),
        ("0/0", "frac"),
        ("2000-02-29", "date"),
        ("12:34", "time"),
        ("51.5, -0.12", "latlong"),
        ("123e4567-e89b-12d3-a456-426614174000", "uuid"),
        ("192.168.1.1", "ip"),
        ("2001:db8::1", "ip"),
        ("1.2.3", "semver"),
        ("12s", "string"),
        ("2000-02-29T12:34", "datetime"),
        ("1.25", "float"),
        ("1e10", "float"),
        ("978-0-306-40615-7", "isbn"),
        ("@1 2@1", "tune"),
        ("9x9:D4 E4", "go"),
        ("e4 e5 Nf3", "chess"),
    ],
)
def test_details_are_encoded_without_type_prefixes(value: str, kind: str) -> None:
    engine = Nmr()
    result = describe_input(value, engine)
    assert result.kind == kind
    assert result.truename == engine.encode(value, kind).truename


def test_slash_pair_is_a_fraction_and_iso_date_is_required() -> None:
    result = describe_input("8/5", Nmr())
    assert result.kind == "frac"
    assert "YYYY-MM-DD" in result.message
    invalid = describe_input("2023-02-29", Nmr())
    assert invalid.truename is None
    assert invalid.kind == "date"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "+",
        "@",
        "1.",
        "1/",
        "1e-",
        "1.2.",
        "v1",
        "1/+",
        "1.2,-",
        "N",
    ],
)
def test_incomplete_explicit_type_waits_for_more_input(value: str) -> None:
    assert describe_input(value, Nmr()).truename is None


@pytest.mark.parametrize("value", ["Tom", "the THE", "the unknownword", "THE OF"])
def test_description_words_remain_literal_text(value: str) -> None:
    engine = Nmr()
    result = describe_input(value, engine)
    assert result.kind == "string"
    assert engine.decode(result.truename).value == value


@pytest.mark.parametrize(
    "value,kind,expected",
    [
        ('string: "123"', "string", "123"),
        ('STRING: "  Tom R  "', "string", "  Tom R  "),
        ('string: ""', "string", ""),
        ("upc: 036000291452", "upc", "036000291452"),
        ("date: 2000-02-29", "date", "2000-02-29"),
        ("chess: ", "chess", ""),
    ],
)
def test_typed_descriptions_preserve_objects_when_swapping(
    value: str, kind: str, expected: str
) -> None:
    engine = Nmr()
    result = describe_input(value, engine)
    assert result.kind == kind
    assert engine.decode(result.truename).value == expected


@pytest.mark.parametrize(
    "value", ["string: 123", 'string: "unfinished', "date: invalid"]
)
def test_invalid_typed_descriptions_do_not_become_other_types(value: str) -> None:
    result = describe_input(value, Nmr())
    assert result.truename is None
    assert result.message


def test_unassigned_truenames_are_playable_without_browsing_to_another_truename() -> (
    None
):
    engine = Nmr()
    truename = " ".join(engine.to_truename(15))
    with pytest.raises(ValueError):
        engine.decode(truename)
    assert engine.truename_index(truename) == 15
    result = json.loads(bridge.preview_truename(json.dumps({"value": truename})))
    assert result["value"] == Tune.from_index(15).text()


def test_truename_playback_defaults_to_relative_with_explicit_absolute_option() -> None:
    engine = Nmr()
    truename = engine.encode("2", "int").truename
    relative = json.loads(bridge.preview_truename(json.dumps({"value": truename})))
    absolute = json.loads(
        bridge.preview_truename(json.dumps({"value": truename, "absolute": True}))
    )
    assert relative["value"] == engine.to_tune(truename).text()
    assert absolute["value"] == engine.to_tune(truename, absolute=True).text()
    assert relative["value"] != absolute["value"]
    with pytest.raises(ValueError, match="prefix"):
        engine.truename_index(":the")


def test_ode_to_joy_truename_plays_the_original_melody_by_default() -> None:
    result = json.loads(
        bridge.preview_truename('{"value":"tune:post were","root":53,"bpm":180}')
    )
    assert result["value"] == "@1 @1 1@1 2@1 @1 -2@1 -1@1 -2@1"
    assert len(result["playback"]) == 8
    assert result["playback"][0]["duration"] == 1 / 3


@pytest.mark.parametrize("value", ["42", "@1", "Tom R"])
def test_full_truename_has_no_prefix_and_preserves_the_absolute_number(
    value: str,
) -> None:
    engine = Nmr()
    result = json.loads(bridge.recognize(json.dumps({"value": value})))
    assert ":" not in result["full_truename"]
    assert engine.truename_index(result["full_truename"]) == engine.truename_index(
        result["truename"]
    )
    full = json.loads(
        bridge.preview_truename(json.dumps({"value": result["full_truename"]}))
    )
    absolute = json.loads(
        bridge.preview_truename(
            json.dumps({"value": result["truename"], "absolute": True})
        )
    )
    assert full == absolute


@pytest.mark.parametrize("value", ["T", "To", "Tom", "Tom ", "Tom R", "Tom Ritchford"])
def test_every_step_of_typing_a_persons_description_is_a_string(value: str) -> None:
    result = json.loads(bridge.recognize(json.dumps({"value": value})))
    assert result["kind"] == "string"
    assert result["full_truename"]
    assert Nmr().decode(result["truename"]).value == value


@pytest.mark.parametrize(
    "value", ["xyzzy", "  Hello, World!  ", ":the", "你好，世界！", "🎵"]
)
def test_unrecognized_text_uses_string_mode_without_losing_whitespace(
    value: str,
) -> None:
    engine = Nmr()
    result = describe_input(value, engine)
    assert result.kind == "string"
    assert result.truename == engine.encode(value, "string").truename
    assert engine.decode(result.truename).value == value


@pytest.mark.parametrize("value", ["name:THE OF", "NAME:the of"])
def test_name_prefix_explicitly_selects_truename_recognition(value: str) -> None:
    result = json.loads(
        bridge.recognize(json.dumps({"value": value, "mode": "truename"}))
    )
    assert result["kind"] == "truename"
    assert result["truename"] == value
    assert result["browsed"] == Nmr().decode(value, browse=True).model_dump()
    marked = json.loads(bridge.preview_truename(json.dumps({"value": value})))
    bare = json.loads(bridge.preview_truename('{"value":"the of"}'))
    assert marked == bare


@pytest.mark.parametrize(
    "value",
    [
        "name:",
        "missingword",
        "42",
        "name:unrecognizedword",
        "name:the THE",
        "name:42",
        "name:+1",
    ],
)
def test_invalid_explicit_name_input_is_not_treated_as_a_string(value: str) -> None:
    result = json.loads(
        bridge.recognize(json.dumps({"value": value, "mode": "truename"}))
    )
    assert result["truename"] is None
    assert result["kind"] == "truename"
    assert result["browse_error"]


def test_name_marker_preserves_an_existing_type_prefix() -> None:
    result = json.loads(bridge.recognize('{"value":"NAME:TUNE:THE","mode":"truename"}'))
    assert result["kind"] == "truename"
    assert result["truename"] == "NAME:TUNE:THE"
    assert result["browsed"]["type"] == "tune"
    assert result["browsed"]["value"] == "@1"


@pytest.mark.parametrize("value", ["date:this been", "tune:post were", "Tom"])
def test_truename_input_returns_its_browsed_object(value: str) -> None:
    result = json.loads(
        bridge.recognize(json.dumps({"value": value, "mode": "truename"}))
    )
    assert result["kind"] == "truename"
    assert result["browsed"] == Nmr().decode(value, browse=True).model_dump()


def test_truename_input_browses_unassigned_slots_instead_of_rejecting_them() -> None:
    engine = Nmr()
    value = "name:" + " ".join(engine.to_truename(4))
    result = json.loads(
        bridge.recognize(json.dumps({"value": value, "mode": "truename"}))
    )
    assert result["browsed"]["type"] == "int"
    assert result["browsed"]["value"] == "0"
    assert not result["browsed"]["canonical"]


@pytest.mark.parametrize(
    "value", ["name:missingword", "name:tune:" + " ".join(Nmr().to_truename(2**4096))]
)
def test_browsing_failures_are_reported_without_losing_truename_mode(
    value: str,
) -> None:
    result = json.loads(
        bridge.recognize(json.dumps({"value": value, "mode": "truename"}))
    )
    assert result["kind"] == "truename"
    assert result["browse_error"]
    assert "browsed" not in result


@pytest.mark.parametrize("value", ["2000-02-29T12:34:56Z", "2000-02-29T12:34:56+01:00"])
def test_datetime_with_timezone_remains_a_string(value: str) -> None:
    engine = Nmr()
    result = describe_input(value, engine)
    assert result.kind == "string"
    assert engine.decode(result.truename).value == value


def test_explicit_time_description_selects_the_type_instead_of_the_category() -> None:
    engine = Nmr()
    result = describe_input("time: 12:34", engine)
    assert result.kind == "time"
    assert engine.decode(result.truename).value == "12:34:00"
    assert result.truename.count(":") == 1


@pytest.mark.parametrize("value", ["[", "[]", '[{"type":"int","value":"1"}]'])
def test_bracketed_text_is_a_string_after_list_removal(value: str) -> None:
    engine = Nmr()
    result = describe_input(value, engine)
    assert result.kind == "string"
    assert engine.decode(result.truename).value == value
