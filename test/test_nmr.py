import pytest

from nmr.nmr import Nmr


@pytest.mark.parametrize(
    "kind,value", [("int", "-42"), ("frac", "2/4"), ("frac", "0/0"), ("float", "-0.0")]
)
def test_prefix_scopes_decode_the_same_value(kind: str, value: str) -> None:
    engine = Nmr()
    path = engine.find_type(kind)[0]
    for scope in [None, "", "universal", "universal:math", path]:
        result = engine.encode(value, kind, scope)
        assert engine.decode(result.name).value == value
        assert engine.decode(result.name, browse=True).name == result.name


def test_canonical_decode_never_silently_browses() -> None:
    engine = Nmr()
    name = "universal:" + " ".join(engine.encode_to_name(3))
    with pytest.raises(ValueError, match="unassigned"):
        engine.decode(name)
    result = engine.decode(name, browse=True)
    assert not result.canonical
    assert engine.decode(result.name).value == result.value


def test_scope_must_contain_the_type() -> None:
    with pytest.raises(ValueError, match="contain"):
        Nmr().encode("1", "int", "play")


def test_vocabulary_identity_is_checked() -> None:
    engine = Nmr()
    with pytest.raises(ValueError, match="identifier"):
        engine.decode(engine.encode("1", "int").name, vocabulary="wrong")
