import json

import pytest

from nmr.nmr import Nmr
from nmr.web import bridge


@pytest.mark.parametrize("index", [0, 1, 42, 2**120])
def test_count_names_the_index_itself_and_browses_for_an_object(index: int) -> None:
    result = json.loads(bridge.count(json.dumps({"value": str(index)})))
    engine = Nmr()
    assert engine.truename_index(result["truename"]) == index
    assert (
        result["browsed"] == engine.decode(result["truename"], browse=True).model_dump()
    )


def test_count_keeps_the_truename_when_browsing_cannot_construct_an_object() -> None:
    engine = Nmr()
    index = engine.truename_index("tune:" + " ".join(engine.to_truename(2**4096)))
    result = json.loads(bridge.count(json.dumps({"value": str(index)})))
    assert engine.truename_index(result["truename"]) == index
    assert result["browse_error"]
    assert "browsed" not in result


@pytest.mark.parametrize("value", ["-1", "1.5", "abc"])
def test_count_rejects_invalid_indices(value: str) -> None:
    with pytest.raises(ValueError):
        bridge.count(json.dumps({"value": value}))


@pytest.mark.parametrize(
    "type_name,index", [("time", 86401), ("cards", 42), ("int", 2**120)]
)
def test_scoped_count_preserves_source_index_and_wraps_objects(
    type_name: str, index: int
) -> None:
    result = json.loads(
        bridge.count(json.dumps({"value": str(index), "type_name": type_name}))
    )
    engine = Nmr()
    assert result["index"] == str(index)
    assert engine.truename_index(result["truename"], False) == index
    assert result["browsed"]["type"] == type_name
    if type_name == "time":
        assert result["browsed"]["value"] == "00:00:01"


@pytest.mark.parametrize("scope", ["", "cards"])
def test_clock_index_is_relative_to_its_source_and_independent_of_target(
    scope: str,
) -> None:
    result = json.loads(
        bridge.count(
            json.dumps(
                {
                    "value": "0",
                    "source_type": "time",
                    "source_value": "00:00:42",
                    "type_name": scope,
                }
            )
        )
    )
    engine = Nmr()
    assert result["index"] == "42"
    assert engine.truename_index(result["truename"], not bool(scope)) == 42
    assert (
        result["browsed"] == engine.decode(result["truename"], browse=True).model_dump()
    )


def test_scoped_name_fields_convert_in_both_directions() -> None:
    encoded = json.loads(
        bridge.recognize(json.dumps({"value": "42", "type_name": "int"}))
    )
    decoded = json.loads(
        bridge.recognize(
            json.dumps(
                {
                    "value": encoded["truename"],
                    "mode": "truename",
                    "type_name": "int",
                }
            )
        )
    )
    assert decoded["browsed"]["value"] == "42"


def test_scoped_card_action_returns_a_local_index() -> None:
    result = json.loads(
        bridge.count_action(
            json.dumps(
                {
                    "value": "0",
                    "type_name": "cards",
                    "action": "swap",
                    "first": 0,
                    "second": 1,
                }
            )
        )
    )
    decoded = json.loads(
        bridge.count(json.dumps({"value": result["index"], "type_name": "cards"}))
    )
    assert decoded["browsed"]["value"] == "(1 2)"
