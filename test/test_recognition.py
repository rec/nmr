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
def test_details_are_named_without_type_prefixes(value: str, kind: str) -> None:
    engine = Nmr()
    result = recognize_input(value, engine)
    assert result.kind == kind
    assert result.name == engine.encode(value, kind).name
    assert not result.name_mode


def test_slash_pair_is_a_fraction_and_iso_date_is_required() -> None:
    result = recognize_input("8/5", Nmr())
    assert result.kind == "frac"
    assert "YYYY-MM-DD" in result.message
    invalid = recognize_input("2023-02-29", Nmr())
    assert invalid.name is None
    assert invalid.kind == "date"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "th",
        "tun",
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
def test_incomplete_type_or_word_prefix_waits_for_more_input(value: str) -> None:
    assert recognize_input(value, Nmr()).name is None


def test_names_are_case_insensitive_and_can_be_qualified() -> None:
    engine = Nmr()
    assert recognize_input("ThE Of", engine).name == "the of"
    result = recognize_input(":play:music:tune:ThE", engine)
    assert result.name == "tune:the"
    assert result.name_mode


def test_partial_names_stay_in_name_mode_until_cleared() -> None:
    engine = Nmr()
    assert recognize_input("the unknownword", engine).name_mode
    result = recognize_input("42", engine, name_mode=True)
    assert result.name is None
    assert result.name_mode
    assert not recognize_input("", engine, name_mode=True).name_mode


def test_repeated_words_are_not_a_valid_name() -> None:
    result = recognize_input("the THE", Nmr())
    assert result.name is None
    assert result.name_mode
    assert result.message


def test_unassigned_names_are_playable_without_browsing_to_another_name() -> None:
    engine = Nmr()
    name = " ".join(engine.encode_to_name(15))
    with pytest.raises(ValueError):
        engine.decode(name)
    assert recognize_input(name, engine).name == name
    assert engine.name_index(name) == 15
    result = json.loads(bridge.preview_name(json.dumps({"value": name})))
    assert result["value"] == Tune.from_index(15).text()


def test_name_playback_defaults_to_relative_with_explicit_absolute_option() -> None:
    engine = Nmr()
    name = engine.encode("2", "int").name
    relative = json.loads(bridge.preview_name(json.dumps({"value": name})))
    absolute = json.loads(
        bridge.preview_name(json.dumps({"value": name, "absolute": True}))
    )
    assert relative["value"] == engine.to_tune(name).text()
    assert absolute["value"] == engine.to_tune(name, absolute=True).text()
    assert relative["value"] != absolute["value"]
    with pytest.raises(ValueError, match="prefix"):
        engine.name_index(":the")


def test_ode_to_joy_name_plays_the_original_melody_by_default() -> None:
    result = json.loads(
        bridge.preview_name('{"value":"tune:such like","root":53,"bpm":180}')
    )
    assert result["value"] == "@1 @1 1@1 2@1 @1 -2@1 -1@1 -2@1"
    assert len(result["playback"]) == 8
    assert result["playback"][0]["duration"] == 1 / 3


@pytest.mark.parametrize("value", ["42", "tune:such like", "THE OF"])
def test_full_name_has_no_prefix_and_preserves_the_absolute_number(value: str) -> None:
    engine = Nmr()
    result = json.loads(bridge.recognize(json.dumps({"value": value})))
    assert ":" not in result["full_name"]
    assert engine.name_index(result["full_name"]) == engine.name_index(result["name"])
    full = json.loads(bridge.preview_name(json.dumps({"value": result["full_name"]})))
    absolute = json.loads(
        bridge.preview_name(json.dumps({"value": result["name"], "absolute": True}))
    )
    assert full == absolute


def test_browser_recognition_returns_the_controlled_mode() -> None:
    result = json.loads(bridge.recognize('{"value":"THE"}'))
    assert result["name"] == "the"
    assert result["name_mode"]


@pytest.mark.parametrize(
    "value", ["xyzzy", "  Hello, World!  ", ":the", "你好，世界！", "🎵"]
)
def test_unrecognized_text_uses_string_mode_without_losing_whitespace(
    value: str,
) -> None:
    engine = Nmr()
    result = recognize_input(value, engine)
    assert result.kind == "string"
    assert not result.name_mode
    assert result.name == engine.encode(value, "string").name
    assert engine.decode(result.name).value == value


def test_unknown_text_can_become_a_word_or_type_as_it_is_edited() -> None:
    engine = Nmr()
    assert recognize_input("xyzzy", engine).kind == "string"
    assert recognize_input("the", engine).name_mode
    assert recognize_input("42", engine).kind == "int"
    assert recognize_input("@1", engine).kind == "tune"
    assert recognize_input("tune:unfinishedword", engine).name is None
