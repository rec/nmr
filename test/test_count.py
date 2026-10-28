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
