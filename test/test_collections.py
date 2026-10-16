import json

import pytest

from nmr.nmr import Nmr
from nmr.types.collections import List


def test_nested_lists_preserve_typed_details() -> None:
    value = [
        {"type": "date", "value": "2000-01-01"},
        {
            "type": "list",
            "value": [
                {"type": "phone", "value": "+442079460958;ext=001"},
                {"type": "frac", "value": "2/4"},
            ],
        },
    ]
    engine = Nmr()
    encoded = engine.encode(json.dumps(value), "list")
    decoded = json.loads(engine.decode(encoded.name).value)
    assert decoded[0] == {"type": "real:time:date", "value": "2000-01-01"}
    assert decoded[1]["value"][0]["value"] == "+442079460958;ext=001"
    assert decoded[1]["value"][1]["value"] == "2/4"
    assert engine.encode(json.dumps(decoded), "list").name == encoded.name


def test_list_order_is_part_of_its_identity() -> None:
    a = {"type": "int", "value": "1"}
    b = {"type": "frac", "value": "0/0"}
    assert List.str_to_index(json.dumps([a, b])) != List.str_to_index(
        json.dumps([b, a])
    )


def test_noncanonical_empty_list_is_only_browsable() -> None:
    with pytest.raises(ValueError, match="Noncanonical"):
        List.index_to_str(2)
    assert List.index_to_str(2, browse=True) == "[]"


@pytest.mark.parametrize(
    "value",
    ["{}", "[1]", '[{"type":"int","value":1}]', '[{"type":"missing","value":"1"}]'],
)
def test_collection_rejects_ambiguous_items(value: str) -> None:
    with pytest.raises(ValueError):
        List.str_to_index(value)


def test_duplicate_json_fields_are_rejected_instead_of_lost() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        List.str_to_index('[{"type":"int","type":"frac","value":"1"}]')


def test_record_is_not_a_supported_type_or_category_slot() -> None:
    engine = Nmr()
    assert "meta:record" not in engine.types()
    with pytest.raises(ValueError, match="Unknown"):
        engine.encode("{}", "record")
    with pytest.raises(ValueError, match="Unknown"):
        engine.decode("meta:record:the")
    with pytest.raises(ValueError, match="unassigned"):
        engine.decode("meta:" + " ".join(engine.encode_to_name(1)))
    with pytest.raises(ValueError, match="Unknown"):
        List.str_to_index('[{"type":"record","value":{}}]')


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
