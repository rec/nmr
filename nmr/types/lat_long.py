from ..type_namer import TypeNamer
from .bounded import bounded, scaled_integer, scaled_string


class LatLong(TypeNamer):
    label = "latlong"
    description = "Latitude,longitude in decimal degrees, exact to 0.000001 degree"

    @staticmethod
    def str_to_index(value: str) -> int:
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError("Expected latitude,longitude in decimal degrees")
        latitude, longitude = (scaled_integer(i, SCALE) for i in parts)
        if (
            not -90 * SCALE <= latitude <= 90 * SCALE
            or not -180 * SCALE <= longitude <= 180 * SCALE
        ):
            raise ValueError("Latitude or longitude outside Earth coordinates")
        if latitude == -90 * SCALE:
            return 0
        if latitude == 90 * SCALE:
            return SIZE - 1
        longitude = (longitude + 180 * SCALE) % WIDTH
        return 1 + (latitude + 90 * SCALE - 1) * WIDTH + longitude

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        index = bounded(index, SIZE, browse)
        if index == 0:
            return "-90,0"
        if index == SIZE - 1:
            return "90,0"
        latitude, longitude = divmod(index - 1, WIDTH)
        latitude -= 90 * SCALE - 1
        longitude -= 180 * SCALE
        return f"{scaled_string(latitude, SCALE)},{scaled_string(longitude, SCALE)}"


SCALE = 10**6
WIDTH = 360 * SCALE
SIZE = 2 + (180 * SCALE - 1) * WIDTH
