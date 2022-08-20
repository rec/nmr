from typing import Optional, Union
import ipaddress
import uuid


class _Base:
    @classmethod
    def from_int(cls, i: int, name) -> str:
        try:
            c = cls._from_int(i)
            if c is not None:
                return c
        except Exception:
            pass

        raise ValueError(f'Can\'t convert "{i}" ({name}) to {cls.__name__}')


class Integer(_Base):
    to_int = staticmethod(int)
    _from_int = staticmethod(str)


class Hex(_Base):
    @staticmethod
    def to_int(s: str):
        s = s.lower()
        if s.startswith('0x'):
            return int(s[2:], 16)
        if s.startswith('-0x'):
            return -int(s[2:], 16)

    _from_int = staticmethod(hex)


class Semver(_Base):
    BASE = 1024

    @classmethod
    def to_int(cls, s: str) -> Optional[int]:
        s2 = s[1:] if s.startswith('v') else s
        p = [int(i) for i in s2.split('.')]
        if len(p) == 3 and all(i < cls.BASE for i in p):
            v = p[2] + cls.BASE * (p[1] + cls.BASE * p[0])
            return v * cls.BASE

    @classmethod
    def _from_int(cls, i: int) -> Optional[str]:
        if i >= 0:
            d0, m0 = divmod(i, cls.BASE)
            if not m0:
                d1, m1 = divmod(d0, cls.BASE)
                d2, m2 = divmod(d1, cls.BASE)
                d3, m3 = divmod(d2, cls.BASE)
                if not d3:
                    return f'v{m3}.{m2}.{m1}'


class LatLong(_Base):
    DIVISIONS = 100000000  # Each degree is divided by ten million
    MULT = 100000 * DIVISIONS  # Means a gap of two zeros between numbers

    @classmethod
    def to_int(cls, s: str) -> Optional[int]:
        from lat_long_parser import parse

        lat, lon = (parse(i) for i in s.split(','))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            lat = round(cls.DIVISIONS * (lat + 90))
            lon = round(cls.DIVISIONS * (lon + 180))
            return lon + cls.MULT * lat

    @classmethod
    def _from_int(cls, i: int) -> Optional[str]:
        from lat_long_parser import to_str_deg_min_sec

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


class IpAddress(_Base):
    @staticmethod
    def to_int(s: str) -> Optional[int]:
        return int(ipaddress.ip_address(s))

    @staticmethod
    def _from_int(i: int) -> Optional[str]:
        return str(ipaddress.ip_address(i))


class UUID(_Base):
    @staticmethod
    def to_int(s: str) -> Optional[int]:
        if len(s) == 36 and s.count('-') == 4:
            return uuid.UUID(s)

    @staticmethod
    def from_int(i: int) -> Optional[str]:
        return str(uuid.UUID(int=i))


CLASSES = Integer, Hex, Semver, LatLong, IpAddress, UUID
NAMES = tuple(c.__name__.lower() for c in CLASSES)


def try_to_int(s: str) -> Union[int, str]:
    for c in CLASSES:
        try:
            i = c.to_int(s)
        except Exception:
            pass
        else:
            if i is not None:
                return i
    return s


def get_class(prefix: str):
    cl = [c for (n, c) in zip(NAMES, CLASSES) if n.startswith(prefix)]
    if not cl:
        raise ValueError(f'Unknown {prefix=}')
    if len(cl) > 1:
        raise ValueError(f'Ambiguous {prefix=}, could be {cl}')
    return cl[0]
