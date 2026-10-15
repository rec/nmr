import pytest

from nmr.nmr import Nmr
from nmr.types import bounded, lat_long
from nmr.types.temporal import DAY, DAYS, Instant, Local

CASES = [
    ("ipv4", "127.0.0.1", "127.0.0.1"),
    ("ipv6", "2001:0:130f::9c0:876a:130b", "2001:0:130f::9c0:876a:130b"),
    (
        "uuid",
        "123e4567-e89b-12d3-a456-426614174000",
        "123e4567-e89b-12d3-a456-426614174000",
    ),
    ("semver", "v1.2.3-rc.1+build.004", "1.2.3-rc.1+build.004"),
    ("phone", "+44 (20) 7946-0958;ext=004", "+442079460958;ext=004"),
    ("latlong", "-33.8688,151.2093", "-33.8688,151.2093"),
    ("latlong", "40,-74", "40,-74"),
    ("latlong", "90,100", "90,0"),
    ("latlong", "10,180", "10,-180"),
    ("date", "2000-02-29", "2000-02-29"),
    ("clock", "23:59:59.999999", "23:59:59.999999"),
    ("local", "2000-02-29T12:30", "2000-02-29T12:30:00"),
    ("instant", "2000-01-01T00:30:00+01:00", "1999-12-31T23:30:00Z"),
    ("duration", "-0.000001s", "-0.000001s"),
    ("isbn", "978-0-306-40615-7", "9780306406157"),
    ("isbn", "0-306-40615-2", "0306406152"),
    ("upc", "036000291452", "036000291452"),
    ("text", " leading 00\nélan 東京 # : \x00", " leading 00\nélan 東京 # : \x00"),
    ("text", "", ""),
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
        assert engine.decode(result.name).value == canonical
        assert engine.decode(result.name, browse=True).name == result.name


@pytest.mark.parametrize(
    "kind,value",
    [
        ("date", "2023-02-29"),
        ("date", "12/11/2000"),
        ("clock", "24:00"),
        ("clock", "12:00:00.1234567"),
        ("local", "2000-01-01T12:00Z"),
        ("instant", "2000-01-01T12:00"),
        ("phone", "020 1234 5678"),
        ("phone", "+123;ext="),
        ("isbn", "9780306406158"),
        ("upc", "036000291453"),
        ("latlong", "1.1234567,2"),
        ("latlong", "91,0"),
        ("semver", "1.2.3-01"),
        ("ipv6", "fe80::1%en0"),
        ("chess", "e4 nonsense"),
    ],
)
def test_invalid_details_are_not_silently_changed(kind: str, value: str) -> None:
    with pytest.raises(ValueError):
        Nmr().encode(value, kind)


def test_temporal_and_coordinate_boundaries() -> None:
    assert Local.index_to_str(DAYS * DAY - 1) == "9999-12-31T23:59:59.999999"
    assert Instant.index_to_str(0) == "0001-01-01T00:00:00Z"
    for index in [0, 1, lat_long.SIZE - 2, lat_long.SIZE - 1]:
        assert (
            lat_long.LatLong.str_to_index(lat_long.LatLong.index_to_str(index)) == index
        )
    with pytest.raises(ValueError):
        bounded.scaled_integer("1e-7", 10**6)


@pytest.mark.parametrize(
    "kind", ["ipv4", "uuid", "date", "clock", "latlong", "isbn", "upc"]
)
def test_browsing_wraps_but_canonical_decoding_rejects_overflow(kind: str) -> None:
    engine = Nmr()
    path = engine.find_type(kind)[0]
    name = path + ":" + " ".join(engine.encode_to_name(2**200))
    with pytest.raises(ValueError):
        engine.decode(name)
    result = engine.decode(name, browse=True)
    assert not result.canonical
    assert engine.decode(result.name).value == result.value
