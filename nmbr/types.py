from typing import Any, Optional, Tuple, Union
import ipaddress
import uuid


class _Base:
    type = staticmethod(str)

    @classmethod
    def from_int(cls, i: int, name='str') -> str:
        try:
            c = str(cls.int_to_type(i))
            if c is not None:
                return c
        except Exception:
            pass

        raise ValueError(f'Can\'t convert "{i}" ({name}) to {cls.__name__}')

    @classmethod
    def int_to_type(cls, i: int) -> Optional[Any]:
        return cls.type(i)

    @staticmethod
    def type_to_int(t: Any) -> int:
        return int(t)

    @classmethod
    def to_int(cls, s: str) -> int:
        return cls.type_to_int(cls.type(s))


class Integer(_Base):
    type = staticmethod(int)


class Hex(_Base):
    @staticmethod
    def type_to_int(s: str):
        s = s.lower()
        if s.startswith('0x'):
            return int(s[2:], 16)
        if s.startswith('-0x'):
            return -int(s[2:], 16)

    int_to_type = staticmethod(hex)


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
    def int_to_type(cls, i: int) -> Optional[str]:
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
        from lat_lon_parser import parse

        lat, lon = (parse(i) for i in s.split(','))
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


class IpAddress(_Base):
    type = staticmethod(ipaddress.ip_address)

    @staticmethod
    def to_int(s: str) -> Optional[int]:
        return int(ipaddress.ip_address(s))


class UUID(_Base):
    type = uuid.UUID

    @staticmethod
    def to_int(s: str) -> Optional[int]:
        if len(s) == 36 and s.count('-') == 4:
            return uuid.UUID(s).int

    @staticmethod
    def int_to_type(i: int) -> Optional[str]:
        return uuid.UUID(int=i)


CLASSES = Integer, Hex, Semver, LatLong, IpAddress, UUID
NAMES = tuple(c.__name__.lower() for c in CLASSES)


def try_to_int(s: str) -> Union[int, str]:
    ci = class_int(s)
    return s if ci is None else ci[1]


def class_int(s: str) -> Optional[Tuple]:
    for c in CLASSES:
        try:
            i = c.to_int(s)
        except Exception:
            pass
        else:
            if i is not None:
                return c, i


def get_class(prefix: str):
    cl = [c for (n, c) in zip(NAMES, CLASSES) if n.startswith(prefix)]
    if not cl:
        raise ValueError(f'Unknown {prefix=}')
    if len(cl) > 1:
        raise ValueError(f'Ambiguous {prefix=}, could be {cl}')
    return cl[0]
