from __future__ import annotations

from lat_lon_parser import parse, to_str_deg_min_sec  # type: ignore[import-untyped]

from ..categories import Location
from ..type_namer import TypeNamer


class _LatLong:
    DIVISIONS = 100000000  # Each degree is divided by ten million
    MULT = 360 * DIVISIONS

    def __init__(self, s: int | str) -> None:
        if isinstance(s, int):
            self.lat, self.lon = divmod(s, self.MULT)
        else:
            lat, lon = (parse(i) for i in s.split(","))
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Bad LatLong")
            lat = 90 if lat == -90 else lat
            lon = 180 if lon == -180 else lon

            self.lat = round(self.DIVISIONS * (lat + 90))
            self.lon = round(self.DIVISIONS * (lon + 180))

    def __int__(self) -> int:
        return self.MULT * self.lat + self.lon

    def __str__(self) -> str:
        lat = to_str_deg_min_sec(self.lat / self.DIVISIONS - 90)
        lon = to_str_deg_min_sec(self.lon / self.DIVISIONS - 180)

        if lat.startswith("-"):
            lat, ns = lat[1:], "S"
        else:
            ns = "N"

        if lon.startswith("-"):
            lat, ew = lat[1:], "W"
        else:
            ew = "E"

        lat += (" " if " " in lat else "") + ns
        lon += (" " if " " in lon else "") + ew

        return f"{lat}, {lon}"


class LatLong(TypeNamer[_LatLong]):
    category = Location.LAT_LONG
