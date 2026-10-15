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
                {"type": "text", "value": " 001 # é "},
                {"type": "frac", "value": "2/4"},
            ],
        },
    }
    engine = Nmr()
    encoded = engine.encode(json.dumps(value), "record")
    decoded = json.loads(engine.decode(encoded.name).value)
    assert decoded["birthday"] == {"type": "physical:time:date", "value": "2000-01-01"}
    assert decoded["details"]["value"][0]["value"] == " 001 # é "
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
