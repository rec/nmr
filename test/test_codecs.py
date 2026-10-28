import pytest

from nmr.nmr import Nmr
from nmr.types import bounded, lat_long
from nmr.types.temporal import DAY, DAYS, Date, DateTime, Time

CASES = [
    ("string", "  Mixed Case 🎵  ", "  Mixed Case 🎵  "),
    ("ip", "127.0.0.1", "127.0.0.1"),
    ("ip", "2001:0:130f::9c0:876a:130b", "2001:0:130f::9c0:876a:130b"),
    (
        "uuid",
        "123e4567-e89b-12d3-a456-426614174000",
        "123e4567-e89b-12d3-a456-426614174000",
    ),
    ("semver", "v1.2.3-rc.1+build.004", "1.2.3-rc.1+build.004"),
    ("phone", "+44 (20) 7946-0958;ext=004", "+442079460958;ext=004"),
    ("latlong", "-33.8688,151.2093", "-33.868802248,151.209301638"),
    ("latlong", "40,-74", "40.000000884,-73.999997709"),
    ("latlong", "90,100", "90,0"),
    ("latlong", "10,180", "10.000000523,-180"),
    ("date", "2000-02-29", "2000-02-29"),
    ("time", "23:59:59", "23:59:59"),
    ("datetime", "2000-02-29 12:34", "2000-02-29T12:34:00"),
    ("isbn", "978-0-306-40615-7", "9780306406157"),
    ("isbn", "0-306-40615-2", "0306406152"),
    ("upc", "036000291452", "036000291452"),
    ("chess", "e4 e5 Nf3", "e2e4 e7e5 g1f3"),
]


@pytest.mark.parametrize("kind,value,canonical", CASES)
def test_codecs_round_trip_at_each_scope(kind: str, value: str, canonical: str) -> None:
    engine = Nmr()
    path = engine.find_type(kind)[0]
    scopes = [
        "",
        *[":".join(path.split(":")[:i]) for i in range(1, len(path.split(":")) + 1)],
    ]
    for scope in scopes:
        result = engine.encode(value, kind, scope)
        assert result.value == canonical
        assert engine.decode(result.truename).value == canonical
        assert engine.decode(result.truename, browse=True).truename == result.truename


@pytest.mark.parametrize(
    "kind,value",
    [
        ("date", "2023-02-29"),
        ("date", "12/11/2000"),
        ("time", "24:00"),
        ("time", "12:00:00.1234567"),
        ("time", "12:60"),
        ("phone", "020 1234 5678"),
        ("phone", "+123;ext="),
        ("isbn", "9780306406158"),
        ("upc", "036000291453"),
        ("latlong", "nan,2"),
        ("latlong", "91,0"),
        ("semver", "1.2.3-01"),
        ("ip", "fe80::1%en0"),
        ("chess", "e4 nonsense"),
    ],
)
def test_invalid_details_are_not_silently_changed(kind: str, value: str) -> None:
    with pytest.raises(ValueError):
        Nmr().encode(value, kind)


def test_temporal_and_coordinate_boundaries() -> None:
    assert Date.index_to_str(DAYS - 1, center_on_zoot=False) == "9999-12-31"
    assert Time.index_to_str(DAY - 1) == "23:59:59"
    for index in [0, 1, lat_long.SIZE - 2, lat_long.SIZE - 1]:
        assert (
            lat_long.LatLong.str_to_index(lat_long.LatLong.index_to_str(index)) == index
        )
    with pytest.raises(ValueError):
        bounded.scaled_integer("1e-7", 10**6)


@pytest.mark.parametrize(
    "kind", ["ip", "uuid", "date", "time", "datetime", "latlong", "isbn", "upc"]
)
def test_browsing_wraps_but_canonical_decoding_rejects_overflow(kind: str) -> None:
    engine = Nmr()
    path = engine.find_type(kind)[0]
    truename = path + ":" + " ".join(engine.to_truename(2**200))
    with pytest.raises(ValueError):
        engine.decode(truename)
    result = engine.decode(truename, browse=True)
    assert not result.canonical
    assert engine.decode(result.truename).value == result.value


def test_string_uses_the_id_category_without_a_text_alias() -> None:
    engine = Nmr()
    assert "data:text" not in engine.types()
    with pytest.raises(ValueError, match="Unknown"):
        engine.encode("hello", "text")
    with pytest.raises(ValueError, match="Unknown"):
        engine.decode("data:text:the")
    result = engine.decode("id:" + " ".join(engine.to_truename(2)))
    assert result.type == "string"
    assert result.value == ""


def test_semver_browsing_normalizes_invalid_metadata() -> None:
    from nmr.pack_numbers import Packer
    from nmr.types.sem_ver import Semver, metadata_index

    index = Packer(count=5).pack(0, 0, 0, metadata_index("01.."), metadata_index(".."))
    with pytest.raises(ValueError):
        Semver.index_to_str(index)
    value = Semver.index_to_str(index, browse=True)
    assert value == "0.0.0-1.0.0+0.0.0"
    assert Semver.index_to_str(Semver.str_to_index(value)) == value


@pytest.mark.parametrize("kind", ["clock", "local", "instant", "duration"])
def test_removed_temporal_labels_are_not_available(kind: str) -> None:
    engine = Nmr()
    with pytest.raises(ValueError, match="Unknown"):
        engine.find_type(kind)
    with pytest.raises(ValueError, match="Unknown"):
        engine.decode(kind + ":the")


def test_datetime_is_part_of_the_time_category() -> None:
    engine = Nmr()
    assert engine.find_type("datetime")[0] == "real:time:datetime"
    result = engine.encode("2000-02-29T12:34", "datetime", scope="real:time")
    assert result.truename.startswith("real:time:")
    assert engine.decode(result.truename).type == "datetime"
    assert engine.decode(result.truename).value == "2000-02-29T12:34:00"


def test_uncentered_datetime_counts_seconds_before_advancing_the_date() -> None:
    assert DateTime.index_to_str(0, center_on_zoot=False) == "0001-01-01T00:00:00"
    assert DateTime.index_to_str(1, center_on_zoot=False) == "0001-01-01T00:00:01"
    assert DateTime.index_to_str(DAY - 1, center_on_zoot=False) == "0001-01-01T23:59:59"
    assert DateTime.index_to_str(DAY, center_on_zoot=False) == "0001-01-02T00:00:00"
    assert (
        DateTime.index_to_str(DAYS * DAY - 1, center_on_zoot=False)
        == "9999-12-31T23:59:59"
    )
    for i in [0, 1, DAY - 1, DAY, DAYS * DAY - 1]:
        assert (
            DateTime.str_to_index(
                DateTime.index_to_str(i, center_on_zoot=False), center_on_zoot=False
            )
            == i
        )


@pytest.mark.parametrize(
    "value",
    [
        "2000-02-30T12:34",
        "2000-02-29T24:00",
        "2000-02-29T12:34Z",
        "2000-02-29T12:34+01:00",
        "2000-02-29T12:34:56.1234567",
    ],
)
def test_datetime_rejects_invalid_components_and_timezones(value: str) -> None:
    with pytest.raises(ValueError):
        DateTime.str_to_index(value)


@pytest.mark.parametrize("fraction", ["0", "1", "123456"])
@pytest.mark.parametrize(
    "kind,value", [("time", "12:34:56"), ("datetime", "2000-02-29T12:34:56")]
)
def test_temporal_types_reject_fractional_seconds(
    kind: str, value: str, fraction: str
) -> None:
    with pytest.raises(ValueError):
        Nmr().encode(value + "." + fraction, kind)
