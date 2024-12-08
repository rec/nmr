from __future__ import annotations

import ipaddress

from ..type_base import Type


class IpAddress(Type):
    type = staticmethod(ipaddress.ip_address)

    @staticmethod
    def to_int(s: str) -> int | None:
        try:
            return int(ipaddress.ip_address(s))
        except Exception:
            return None
