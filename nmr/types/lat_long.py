"""Progressive cube-face positions with a globally bounded sub-metre grid."""

import math

from ..type_name import TypeNamer
from .bounded import bounded


class LatLong(TypeNamer):
    label = "latlong"
    description = (
        "Latitude,longitude in decimal degrees, rounded to a sub-metre cube grid"
    )

    @staticmethod
    def str_to_index(value: str) -> int:
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError("Expected latitude,longitude in decimal degrees")
        latitude, longitude = (float(i) for i in parts)
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("Latitude or longitude outside Earth coordinates")
        latitude, longitude = math.radians(latitude), math.radians(longitude)
        vector = (
            math.cos(latitude) * math.cos(longitude),
            math.cos(latitude) * math.sin(longitude),
            math.sin(latitude),
        )
        maximum = max(abs(i) for i in vector)
        # Fixed X/Y/Z priority also resolves floating-point noise at exact seams.
        axis = next(i for i in range(3) if abs(vector[i]) >= maximum - FACE_TOLERANCE)
        face = FACES.index((axis, 1 if vector[axis] >= 0 else -1))
        a, b = (
            coordinate_rank(vector[i] / abs(vector[axis]))
            for i in range(3)
            if i != axis
        )
        pair = a * a + b if a >= b else b * b + b + 1 + a
        return 6 * pair + face

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        index = bounded(index, SIZE, browse)
        pair, face = divmod(index, 6)
        shell = math.isqrt(pair)
        offset = pair - shell * shell
        a, b = (shell, offset) if offset <= shell else (offset - shell - 1, shell)
        axis, sign = FACES[face]
        vector = [coordinate_value(a), coordinate_value(b)]
        vector.insert(axis, float(sign))
        x, y, z = vector
        latitude = math.degrees(math.atan2(z, math.hypot(x, y)))
        longitude = (math.degrees(math.atan2(y, x)) + 180) % 360 - 180
        parts = [f"{i:.9f}".rstrip("0").rstrip(".") for i in (latitude, longitude)]
        return ",".join("0" if i == "-0" else i for i in parts)


def coordinate_rank(value: float) -> int:
    """Round to an interior grid point, then rank it in midpoint-first order."""
    point = max(1, min(DIVISIONS - 1, math.floor((value + 1) * (DIVISIONS // 2) + 0.5)))
    shift = (point & -point).bit_length() - 1
    level = LEVELS - shift - 1
    return (1 << level) - 1 + ((point >> shift) - 1) // 2


def coordinate_value(rank: int) -> float:
    """Recover the dyadic coordinate from its breadth-first midpoint rank."""
    level = (rank + 1).bit_length() - 1
    position = rank + 1 - (1 << level)
    return (2 * position + 1) / (1 << level) - 1


LEVELS = 24
DIVISIONS = 1 << LEVELS
SIZE = 6 * (DIVISIONS - 1) ** 2
FACE_TOLERANCE = 1e-15
FACES = ((0, 1), (1, 1), (0, -1), (1, -1), (2, 1), (2, -1))
