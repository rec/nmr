from __future__ import annotations

import ipaddress

from ..category import Computer
from ..type_namer import TypeNamer


class IPv4Address(TypeNamer[ipaddress.IPv4Address]):
    category = Computer.IP_V4_ADDRESS


class IPv6Address(TypeNamer[ipaddress.IPv6Address]):
    category = Computer.IP_V6_ADDRESS
