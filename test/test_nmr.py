import pytest

from nmr.nmr import Nmr


@pytest.mark.parametrize(
    "kind,value", [("int", "-42"), ("frac", "2/4"), ("frac", "0/0"), ("float", "-0.0")]
)
def test_prefix_scopes_decode_the_same_value(kind: str, value: str) -> None:
    engine = Nmr()
    path = engine.find_type(kind)[0]
    for scope in [None, "", "pure", "pure:math", path]:
        result = engine.encode(value, kind, scope)
        assert engine.decode(result.truename).value == value
        assert engine.decode(result.truename, browse=True).truename == result.truename


def test_canonical_decode_never_silently_browses() -> None:
    engine = Nmr()
    truename = "pure:" + " ".join(engine.to_truename(3))
    with pytest.raises(ValueError, match="unassigned"):
        engine.decode(truename)
    result = engine.decode(truename, browse=True)
    assert not result.canonical
    assert engine.decode(result.truename).value == result.value


def test_scope_must_contain_the_type() -> None:
    with pytest.raises(ValueError, match="contain"):
        Nmr().encode("1", "int", "play")


def test_vocabulary_identity_is_checked() -> None:
    engine = Nmr()
    with pytest.raises(ValueError, match="identifier"):
        engine.decode(engine.encode("1", "int").truename, vocabulary="wrong")


@pytest.mark.parametrize(
    "prefix", ["chess", "game:chess", "play:game:chess", ":play:game:chess"]
)
def test_full_and_partial_paths_read_and_print_as_short_prefixes(prefix: str) -> None:
    engine = Nmr()
    result = engine.encode("e4 e5 Nf3", prefix)
    assert result.type == "chess"
    assert result.truename == "chess:in get"
    for browse in (False, True):
        decoded = engine.decode(prefix + ":in get", browse=browse)
        assert decoded == result


@pytest.mark.parametrize("scope", ["game", "play:game"])
def test_category_scopes_are_shortened_without_changing_the_payload(scope: str) -> None:
    engine = Nmr()
    result = engine.encode("e4 e5 Nf3", "chess", scope)
    assert result.truename == "game:will gas"
    assert engine.decode(scope + ":will gas") == result


def test_wrong_parent_categories_are_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        Nmr().decode("data:chess:in get")


@pytest.mark.parametrize(
    "truename", [":the", "pure::the", "pure:", "pure:math:int:extra:the"]
)
def test_malformed_prefixes_are_not_accepted_as_canonical(truename: str) -> None:
    with pytest.raises(ValueError):
        Nmr().decode(truename)
