import json

import pytest

from nmr.category import route
from nmr.nmr import Nmr
from nmr.types.tune import Tune
from nmr.web import bridge


@pytest.mark.parametrize(
    "kind,value",
    [
        ("int", "2"),
        ("frac", "2/4"),
        ("date", "2000-02-29"),
        ("chess", "e4 e5 Nf3"),
        ("go", "9x9:D4 E4"),
        ("list", "[]"),
        ("tune", "@1 2@1/2"),
    ],
)
@pytest.mark.parametrize("scope", [None, ""])
def test_any_item_can_be_interpreted_as_its_payload_or_root_index(
    kind: str, value: str, scope: str | None
) -> None:
    engine = Nmr()
    result = engine.encode(value, kind, scope)
    index = engine.from_truename(result.truename.rsplit(":", 1)[-1].split())
    slots = engine.find_type(kind)[1] if scope is None else []
    assert engine.to_tune(result.truename).index() == index
    assert engine.to_tune(result.truename, absolute=True).index() == route(slots, index)


def test_relative_mapping_follows_the_selected_prefix_and_absolute_does_not() -> None:
    engine = Nmr()
    absolute = []
    relative = []
    for scope in ["", "play", "play:music", "play:music:tune"]:
        result = engine.encode("@1 2@1/2", "tune", scope)
        relative.append(engine.to_tune(result.truename).index())
        absolute.append(engine.to_tune(result.truename, absolute=True).index())
    assert len(set(absolute)) == 1
    assert len(set(relative)) == 4
    assert relative[0] == absolute[0]
    assert relative[-1] == Tune.str_to_index("@1 2@1/2")


def test_projection_obeys_canonical_and_vocabulary_rules() -> None:
    engine = Nmr([f"word{i}" for i in range(32)])
    result = engine.encode("2", "int")
    assert engine.to_tune(result.truename).index() == 3
    unassigned = "pure:" + engine.words[3]
    with pytest.raises(ValueError, match="unassigned"):
        engine.to_tune(unassigned)
    browsed = engine.decode(unassigned, browse=True)
    assert engine.to_tune(unassigned, browse=True) == engine.to_tune(browsed.truename)


def test_bridge_previews_items_without_changing_their_values() -> None:
    bridge.configure("{}")
    source = {"operation": "encode", "type_name": "int", "value": "2"}
    relative = json.loads(bridge.preview_item(json.dumps(source)))
    assert relative["value"] == "@1 -1@1"
    absolute = json.loads(bridge.preview_item(json.dumps({**source, "absolute": True})))
    result = Nmr().encode("2", "int")
    assert absolute["value"] == Nmr().to_tune(result.truename, absolute=True).text()
    decoded = json.loads(
        bridge.preview_item(
            json.dumps({"operation": "decode", "value": result.truename})
        )
    )
    assert decoded == relative
    assert source["value"] == "2"
    with pytest.raises(ValueError, match="identifier"):
        bridge.preview_item(json.dumps({**source, "vocabulary": "wrong"}))


def test_projection_preserves_work_and_playback_refusals() -> None:
    engine = Nmr()
    truename = engine.encode(str(2**4096), "int").truename
    with pytest.raises(ValueError, match="work limit"):
        engine.to_tune(truename)
    request = {"operation": "encode", "type_name": "tune", "value": "@1000"}
    result = json.loads(bridge.preview_item(json.dumps(request)))
    assert result["value"] == "@1000"
    assert "Playback limit" in result["playback_error"]
