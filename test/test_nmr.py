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
    assert result.truename == "chess:in also"
    for browse in (False, True):
        decoded = engine.decode(prefix + ":in also", browse=browse)
        assert decoded == result


@pytest.mark.parametrize("scope", ["game", "play:game"])
def test_category_scopes_are_shortened_without_changing_the_payload(scope: str) -> None:
    engine = Nmr()
    result = engine.encode("e4 e5 Nf3", "chess", scope)
    assert result.truename == "game:was hope"
    assert engine.decode(scope + ":was hope") == result


def test_wrong_parent_categories_are_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        Nmr().decode("data:chess:in also")


@pytest.mark.parametrize(
    "truename", [":the", "pure::the", "pure:", "pure:math:int:extra:the"]
)
def test_malformed_prefixes_are_not_accepted_as_canonical(truename: str) -> None:
    with pytest.raises(ValueError):
        Nmr().decode(truename)


@pytest.mark.parametrize("prefix", ["name", "NAME", "NaMe"])
def test_name_prefix_has_no_category_cost(prefix: str) -> None:
    engine = Nmr()
    bare = engine.encode("2/4", "frac", scope="")
    marked = prefix + ":" + bare.truename
    assert engine.truename_index(marked) == engine.truename_index(bare.truename)
    decoded = engine.decode(marked)
    assert decoded.value == bare.value
    assert decoded.truename == "name:" + bare.truename
    assert decoded.canonical
    assert engine.to_tune(marked) == engine.to_tune(bare.truename)
    assert engine.encode("2/4", "frac", scope="name").truename == decoded.truename
    assert "name" not in engine.types()
    assert all("name" not in i.split(":") for i in engine.types())


def test_name_prefix_preserves_browsing_repairs() -> None:
    engine = Nmr()
    bare = " ".join(engine.to_truename(15))
    with pytest.raises(ValueError, match="unassigned"):
        engine.decode("name:" + bare)
    browsed = engine.decode("name:" + bare, browse=True)
    assert browsed.value == engine.decode(bare, browse=True).value
    assert browsed.truename.startswith("name:")
    assert not browsed.canonical


@pytest.mark.parametrize("scope", ["", "play", "game", "chess"])
def test_name_marker_can_wrap_an_existing_prefix(scope: str) -> None:
    engine = Nmr()
    source = engine.encode("e4 e5 Nf3", "chess", scope).truename
    marked = "name:" + source
    assert engine.decode(marked).value == engine.decode(source).value
    assert engine.decode(marked).truename == marked
    for absolute in (False, True):
        assert engine.truename_index(marked, absolute) == engine.truename_index(
            source, absolute
        )
        assert engine.to_tune(marked, absolute) == engine.to_tune(source, absolute)


@pytest.mark.parametrize(
    "prefix", ["time", "time:time", "real:time:time", ":real:time:time"]
)
def test_time_paths_read_as_the_type_and_print_one_time_prefix(prefix: str) -> None:
    engine = Nmr()
    result = engine.encode("12:34", prefix)
    assert result.type == "time"
    assert result.value == "12:34:00"
    assert result.truename.startswith("time:")
    assert result.truename.count(":") == 1
    payload = result.truename.partition(":")[2]
    assert engine.decode(prefix + ":" + payload) == result
    assert engine.truename_index(prefix + ":" + payload) == engine.truename_index(
        result.truename
    )


@pytest.mark.parametrize(
    "kind,value", [("date", "2000-02-29"), ("time", "12:34"), ("duration", "1s")]
)
def test_time_category_scope_stays_distinct_from_the_type(
    kind: str, value: str
) -> None:
    engine = Nmr()
    result = engine.encode(value, kind, scope="real:time")
    assert result.truename.startswith("real:time:")
    assert engine.decode(result.truename) == result
    assert engine.decode(":" + result.truename) == result
    assert engine.truename_index(result.truename) == engine.truename_index(
        engine.encode(value, kind).truename
    )


def test_time_short_prefix_cannot_be_used_as_a_duration_category_scope() -> None:
    with pytest.raises(ValueError, match="does not contain"):
        Nmr().encode("1s", "duration", scope="time")
