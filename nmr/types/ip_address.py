import ipaddress

from ..type_namer import TypeNamer
from .bounded import bounded


class IPv4(TypeNamer):
    label = "ipv4"
    description = "IPv4 address"

    @staticmethod
    def str_to_index(value: str) -> int:
        return int(ipaddress.IPv4Address(value))

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return str(ipaddress.IPv4Address(bounded(index, 2**32, browse)))


class IPv6(TypeNamer):
    label = "ipv6"
    description = "IPv6 address without an interface scope"

    @staticmethod
    def str_to_index(value: str) -> int:
        if "%" in value:
            raise ValueError("Scoped IPv6 addresses require exact text")
        return int(ipaddress.IPv6Address(value))

    @staticmethod
    def index_to_str(index: int, browse: bool = False) -> str:
        return str(ipaddress.IPv6Address(bounded(index, 2**128, browse)))
