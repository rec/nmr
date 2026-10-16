import json

import pytest

from nmr.nmr import Nmr
from nmr.types.collections import List, Record


def test_nested_contact_record_preserves_typed_details() -> None:
    value = {
        "birthday": {"type": "date", "value": "2000-01-01"},
        "details": {
            "type": "list",
            "value": [
                {"type": "phone", "value": "+442079460958;ext=001"},
                {"type": "frac", "value": "2/4"},
            ],
        },
    }
    engine = Nmr()
    encoded = engine.encode(json.dumps(value), "record")
    decoded = json.loads(engine.decode(encoded.name).value)
    assert decoded["birthday"] == {"type": "physical:time:date", "value": "2000-01-01"}
    assert decoded["details"]["value"][0]["value"] == "+442079460958;ext=001"
    assert decoded["details"]["value"][1]["value"] == "2/4"
    assert engine.encode(json.dumps(decoded), "record").name == encoded.name


def test_record_order_is_not_identity_but_list_order_is() -> None:
    a = {"type": "int", "value": "1"}
    b = {"type": "frac", "value": "0/0"}
    assert Record.str_to_index(json.dumps({"a": a, "b": b})) == Record.str_to_index(
        json.dumps({"b": b, "a": a})
    )
    assert List.str_to_index(json.dumps([a, b])) != List.str_to_index(
        json.dumps([b, a])
    )


def test_noncanonical_empty_list_is_only_browsable() -> None:
    with pytest.raises(ValueError, match="Noncanonical"):
        List.index_to_str(2)
    assert List.index_to_str(2, browse=True) == "[]"


@pytest.mark.parametrize(
    "value", ["[1]", '[{"type":"int","value":1}]', '[{"type":"missing","value":"1"}]']
)
def test_collection_rejects_ambiguous_items(value: str) -> None:
    with pytest.raises(ValueError):
        List.str_to_index(value)


def test_duplicate_json_fields_are_rejected_instead_of_lost() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        Record.str_to_index(
            '{"a":{"type":"int","value":"1"},"a":{"type":"int","value":"2"}}'
        )
    with pytest.raises(ValueError, match="Duplicate"):
        List.str_to_index('[{"type":"int","type":"frac","value":"1"}]')


def test_record_field_names_preserve_unicode_and_whitespace() -> None:
    value = {" 001 # é 東京 :\x00 ": {"type": "int", "value": "0"}}
    decoded = json.loads(Record.index_to_str(Record.str_to_index(json.dumps(value))))
    assert list(decoded) == list(value)
    assert decoded[next(iter(value))]["value"] == "0"


def test_record_browsing_repairs_invalid_utf8_field_names() -> None:
    # One field with key index 256 (the invalid UTF-8 byte ff), integer zero.
    index = 131585
    with pytest.raises(UnicodeDecodeError):
        Record.index_to_str(index)
    value = Record.index_to_str(index, browse=True)
    assert json.loads(value) == {"?": {"type": "universal:math:int", "value": "0"}}
    assert Record.index_to_str(Record.str_to_index(value)) == value


def test_collection_work_limits_are_explicit() -> None:
    with pytest.raises(ValueError, match="256"):
        List.str_to_index(json.dumps([{"type": "int", "value": "0"}] * 257))
    value: object = []
    for _ in range(8):
        value = [{"type": "list", "value": value}]
    with pytest.raises(ValueError, match="eight"):
        List.str_to_index(json.dumps(value))


def test_excessive_json_nesting_is_a_value_error() -> None:
    with pytest.raises(ValueError):
        List.str_to_index("[" * 1100 + "0" + "]" * 1100)
