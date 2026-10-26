"""Recognize unlabelled details without guessing ambiguous date formats."""

import json

import pytest

from nmr.nmr import Nmr
from nmr.recognition import recognize_input
from nmr.types.tune import Tune
from nmr.web import bridge


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
        ("12:34", "clock"),
        ("2000-02-29T12:34:56", "local"),
        ("2000-02-29T12:34:56Z", "instant"),
        ("51.5, -0.12", "latlong"),
        ("123e4567-e89b-12d3-a456-426614174000", "uuid"),
        ("192.168.1.1", "ipv4"),
        ("2001:db8::1", "ipv6"),
        ("1.2.3", "semver"),
        ("12s", "duration"),
        ("1.25", "float"),
        ("1e10", "float"),
        ("978-0-306-40615-7", "isbn"),
        ("@1 2@1", "tune"),
        ("9x9:D4 E4", "go"),
        ("e4 e5 Nf3", "chess"),
        ('[{"type":"int","value":"1"}]', "list"),
    ],
)
def test_details_are_encoded_without_type_prefixes(value: str, kind: str) -> None:
    engine = Nmr()
    result = recognize_input(value, engine)
    assert result.kind == kind
    assert result.truename == engine.encode(value, kind).truename


def test_slash_pair_is_a_fraction_and_iso_date_is_required() -> None:
    result = recognize_input("8/5", Nmr())
    assert result.kind == "frac"
    assert "YYYY-MM-DD" in result.message
    invalid = recognize_input("2023-02-29", Nmr())
    assert invalid.truename is None
    assert invalid.kind == "date"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "+",
        "@",
        "[",
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
    assert recognize_input(value, Nmr()).truename is None


def test_truenames_are_case_insensitive_and_can_be_qualified() -> None:
    engine = Nmr()
    assert recognize_input("ThE Of", engine).truename == "the of"
    result = recognize_input(":play:music:tune:ThE", engine)
    assert result.truename == "tune:the"
    assert result.kind == "truename"


@pytest.mark.parametrize("value", ["the unknownword", "the THE"])
def test_text_that_is_not_a_complete_unique_truename_becomes_a_string(
    value: str,
) -> None:
    engine = Nmr()
    result = recognize_input(value, engine)
    assert result.kind == "string"
    assert engine.decode(result.truename).value == value


def test_explicit_truenames_still_reject_duplicate_words() -> None:
    result = recognize_input("tune:the THE", Nmr())
    assert result.truename is None
    assert result.kind == "truename"
    assert result.message


def test_unassigned_truenames_are_playable_without_browsing_to_another_truename() -> (
    None
):
    engine = Nmr()
    truename = " ".join(engine.to_truename(15))
    with pytest.raises(ValueError):
        engine.decode(truename)
    assert recognize_input(truename, engine).truename == truename
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
        bridge.preview_truename('{"value":"tune:such like","root":53,"bpm":180}')
    )
    assert result["value"] == "@1 @1 1@1 2@1 @1 -2@1 -1@1 -2@1"
    assert len(result["playback"]) == 8
    assert result["playback"][0]["duration"] == 1 / 3


@pytest.mark.parametrize("value", ["42", "tune:such like", "THE OF"])
def test_full_truename_has_name_prefix_without_changing_the_absolute_number(
    value: str,
) -> None:
    engine = Nmr()
    result = json.loads(bridge.recognize(json.dumps({"value": value})))
    assert result["full_truename"].startswith("name:")
    assert result["full_truename"].count(":") == 1
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


@pytest.mark.parametrize(
    "value,kind",
    [
        ("T", "string"),
        ("To", "truename"),
        ("Tom", "truename"),
        ("Tom ", "truename"),
        ("Tom R", "string"),
        ("Tom Ri", "string"),
        ("Tom Ritchford", "string"),
    ],
)
def test_every_step_of_typing_a_persons_name_populates_both_lines(
    value: str, kind: str
) -> None:
    result = json.loads(bridge.recognize(json.dumps({"value": value})))
    assert result["kind"] == kind
    assert result["truename"] and result["full_truename"]
    if kind == "string":
        assert Nmr().decode(result["truename"]).value == value


@pytest.mark.parametrize(
    "value", ["xyzzy", "  Hello, World!  ", ":the", "你好，世界！", "🎵"]
)
def test_unrecognized_text_uses_string_mode_without_losing_whitespace(
    value: str,
) -> None:
    engine = Nmr()
    result = recognize_input(value, engine)
    assert result.kind == "string"
    assert result.truename == engine.encode(value, "string").truename
    assert engine.decode(result.truename).value == value


def test_unknown_text_can_become_a_word_or_type_as_it_is_edited() -> None:
    engine = Nmr()
    assert recognize_input("xyzzy", engine).kind == "string"
    assert recognize_input("the ", engine).kind == "truename"
    assert recognize_input("42", engine).kind == "int"
    assert recognize_input("@1", engine).kind == "tune"
    assert recognize_input("tune:unfinishedword", engine).truename is None


@pytest.mark.parametrize("value", ["name:THE OF", "NAME:the of"])
def test_name_prefix_explicitly_selects_truename_recognition(value: str) -> None:
    result = json.loads(bridge.recognize(json.dumps({"value": value})))
    assert result["kind"] == "truename"
    assert result["truename"] == "name:the of"
    assert result["full_truename"] == "name:the of"
    marked = json.loads(bridge.preview_truename(json.dumps({"value": value})))
    bare = json.loads(bridge.preview_truename('{"value":"the of"}'))
    assert marked == bare


@pytest.mark.parametrize(
    "value", ["name:", "name:unrecognizedword", "name:the THE", "name:42", "name:+1"]
)
def test_invalid_explicit_name_input_is_not_treated_as_a_string(value: str) -> None:
    result = recognize_input(value, Nmr())
    assert result.truename is None
    assert result.kind == "truename"


def test_name_marker_preserves_an_existing_type_prefix() -> None:
    result = json.loads(bridge.recognize('{"value":"NAME:TUNE:THE"}'))
    assert result["kind"] == "truename"
    assert result["truename"] == "name:tune:the"
    assert Nmr().truename_index(result["full_truename"]) == Nmr().truename_index(
        "tune:the"
    )
