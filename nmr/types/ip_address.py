import ipaddress
from typing import Optional

from ..type_base import Type


class IpAddress(Type):
    type = staticmethod(ipaddress.ip_address)

    @staticmethod
    def to_int(s: str) -> Optional[int]:
        try:
            return int(ipaddress.ip_address(s))
        except Exception:
            return None
