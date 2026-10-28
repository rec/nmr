"""Round trips and conservative WGS84 distance bounds for the globe grid."""

import math
import random
from collections.abc import Iterator

import pytest

from nmr.types.lat_long import SIZE, LatLong


@pytest.mark.parametrize(
    "index,position",
    [(0, "0,0"), (1, "0,90"), (2, "0,-180"), (3, "0,-90"), (4, "90,0"), (5, "-90,0")],
)
def test_first_six_positions_cover_the_globe(index: int, position: str) -> None:
    assert LatLong.index_to_str(index) == position
    assert LatLong.str_to_index(position) == index


def test_coarse_and_fine_positions_have_unique_reversible_names() -> None:
    generator = random.Random(20261028)
    indices = [*range(1000), SIZE - 1, SIZE - 2]
    indices.extend(generator.randrange(SIZE) for _ in range(20000))
    for i in range(1, 25):
        indices.extend(generator.randrange(6 * (2**i - 1) ** 2) for _ in range(50))
    for i in indices:
        position = LatLong.index_to_str(i)
        assert LatLong.str_to_index(position) == i, (i, position)


@pytest.mark.parametrize("longitude", [-180, -90, 0, 90, 180])
def test_poles_and_antimeridian_have_one_identity(longitude: int) -> None:
    assert LatLong.str_to_index(f"90,{longitude}") == 4
    assert LatLong.str_to_index(f"-90,{longitude}") == 5
    assert LatLong.str_to_index("10,180") == LatLong.str_to_index("10,-180")


@pytest.mark.parametrize("value", ["91,0", "0,181", "nan,0", "0,inf", "0", "0,0,0"])
def test_invalid_coordinates_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        LatLong.str_to_index(value)


def test_complete_finite_domain_and_browsing_wrap() -> None:
    with pytest.raises(ValueError):
        LatLong.index_to_str(SIZE)
    assert LatLong.index_to_str(SIZE, browse=True) == "0,0"
    assert LatLong.index_to_str(2 * SIZE - 1, browse=True) == LatLong.index_to_str(
        SIZE - 1
    )


def test_global_and_seam_samples_stay_within_the_wgs84_error_bound() -> None:
    worst = (0.0, "", "")
    count = 0
    for latitude, longitude in sample_positions():
        source = f"{latitude:.17g},{longitude:.17g}"
        index = LatLong.str_to_index(source)
        target = LatLong.index_to_str(index)
        assert LatLong.str_to_index(target) == index
        error = distance_upper_bound(source, target)
        assert error < 0.63, (source, target, error)
        worst = max(worst, (error, source, target))
        count += 1
    print(f"{count} global/seam samples; largest WGS84 distance upper bound: {worst}")


def test_analytic_rounding_bound_is_less_than_a_metre() -> None:
    # On WGS84 both principal radii of curvature are at most a / (1-f).
    assert 6378137 / (1 - 1 / 298.257223563) < RADIUS_LIMIT
    # A normalized cube face has derivative norm <= 1/sqrt(1+u*u+v*v).
    # Interior rounding moves at most h/2 per axis. At a clipped face edge
    # the displacement may reach h, but the larger denominator reduces it.
    h = 2 / 2**24 + 1e-14  # Includes the face-tie tolerance and arithmetic noise.
    bounds = [
        RADIUS_LIMIT * h / math.sqrt(2),
        RADIUS_LIMIT * h * math.sqrt(1.25 / (1 + (1 - h) ** 2)),
        RADIUS_LIMIT * h * math.sqrt(2 / (1 + 2 * (1 - h) ** 2)),
    ]
    # Nine decimal places add < 0.00008 m; reserve 0.0001 m for text rounding.
    bound = max(bounds) + 0.0001
    assert bound < 0.63
    print(f"Conservative global WGS84 error bound, including text: {bound:.6f} m")


def sample_positions() -> Iterator[tuple[float, float]]:
    generator = random.Random(20261028)
    for _ in range(20000):
        yield (
            math.degrees(math.asin(generator.uniform(-1, 1))),
            generator.uniform(-180, 180),
        )
    for a in range(-90, 91, 3):
        for b in range(-180, 181, 5):
            yield float(a), float(b)
    h = 2 / 2**24
    seams = [-1, -1 + h / 2, -1 + h, -h / 2, 0, h / 2, 1 - h, 1 - h / 2, 1]
    for a in range(3):
        for b in [-1, 1]:
            for u in seams:
                for v in seams:
                    vector = [u, v]
                    vector.insert(a, float(b))
                    x, y, z = vector
                    yield (
                        math.degrees(math.atan2(z, math.hypot(x, y))),
                        math.degrees(math.atan2(y, x)),
                    )


def distance_upper_bound(source: str, target: str) -> float:
    """Bound WGS84 geodesic distance by the lifted unit-sphere great-circle path."""
    a, b = (math.radians(float(i)) for i in source.split(","))
    c, d = (math.radians(float(i)) for i in target.split(","))
    haversine = (
        math.sin((a - c) / 2) ** 2
        + math.cos(a) * math.cos(c) * math.sin((b - d) / 2) ** 2
    )
    return RADIUS_LIMIT * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))


RADIUS_LIMIT = 6_400_000
