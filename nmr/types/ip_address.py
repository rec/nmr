from . _type import Type
from typing import Optional
import ipaddress


class IpAddress(Type):
    type = staticmethod(ipaddress.ip_address)

    @staticmethod
    def to_int(s: str) -> Optional[int]:
        try:
            return int(ipaddress.ip_address(s))
        except Exception:
            return None
