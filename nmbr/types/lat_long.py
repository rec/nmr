from . _type import Type
from typing import Optional


class LatLong(Type):
    DIVISIONS = 100000000  # Each degree is divided by ten million
    MULT = 100000 * DIVISIONS  # Means a gap of two zeros between numbers

    @classmethod
    def to_int(cls, s: str) -> Optional[int]:
        from lat_lon_parser import parse

        try:
            lat, lon = (parse(i) for i in s.split(','))
        except Exception:
            return

        if -90 <= lat <= 90 and -180 <= lon <= 180:
            lat = round(cls.DIVISIONS * (lat + 90))
            lon = round(cls.DIVISIONS * (lon + 180))
            return lon + cls.MULT * lat

    @classmethod
    def int_to_type(cls, i: int) -> Optional[str]:
        from lat_lon_parser import to_str_deg_min_sec

        lat, lon = divmod(i, cls.MULT)
        lat = lat / cls.DIVISIONS - 90
        lon = lon / cls.DIVISIONS - 180

        if -90 <= lat <= 90 and -180 <= lon <= 180:
            lat = to_str_deg_min_sec(lat)
            lon = to_str_deg_min_sec(lon)

            if lat.startswith('-'):
                lat, ns = lat[1:], 'S'
            else:
                ns = 'N'

            if lon.startswith('-'):
                lat, ew = lat[1:], 'W'
            else:
                ew = 'E'

            lat += ' ' * (' ' in lat) + ns
            lon += ' ' * (' ' in lon) + ew

            return f'{lat}, {lon}'
