from __future__ import annotations

import ipaddress

from ..nameable_type import NameableType


class IpAddress(NameableType):
    type = staticmethod(ipaddress.ip_address)  # type: ignore[assignment]

    @staticmethod
    def to_int(s: str) -> int | None:
        try:
            return int(ipaddress.ip_address(s))
        except Exception:
            return None
