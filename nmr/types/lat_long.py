from __future__ import annotations

from ..nameable_type import NameableType


class LatLong(NameableType):
    DIVISIONS = 100000000  # Each degree is divided by ten million
    MULT = 100000 * DIVISIONS  # Means a gap of two zeros between numbers

    @classmethod
    def to_int(cls, s: str) -> int | None:
        from lat_lon_parser import parse  # type: ignore[import-untyped]

        lat: int
        lon: int

        try:
            lat, lon = (parse(i) for i in s.split(","))
        except Exception:
            return None

        if -90 <= lat <= 90 and -180 <= lon <= 180:
            lat = round(cls.DIVISIONS * (lat + 90))
            lon = round(cls.DIVISIONS * (lon + 180))
            return lon + cls.MULT * lat
        return None

    @classmethod
    def int_to_type(cls, i: int) -> str | None:
        from lat_lon_parser import to_str_deg_min_sec

        lat, lon = divmod(i, cls.MULT)
        la = lat / cls.DIVISIONS - 90
        lo = lon / cls.DIVISIONS - 180

        if -90 <= la <= 90 and -180 <= lo <= 180:
            las = to_str_deg_min_sec(la)
            los = to_str_deg_min_sec(lo)

            if las.startswith("-"):
                las, ns = las[1:], "S"
            else:
                ns = "N"

            if los.startswith("-"):
                las, ew = las[1:], "W"
            else:
                ew = "E"

            las += " " * (" " in las) + ns
            los += " " * (" " in los) + ew

            return f"{las}, {los}"
        return None
