from . base import Base
from typing import Optional
import ipaddress


class IpAddress(Base):
    type = staticmethod(ipaddress.ip_address)

    @staticmethod
    def to_int(s: str) -> Optional[int]:
        return int(ipaddress.ip_address(s))
